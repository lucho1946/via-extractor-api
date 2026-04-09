# ==========================================================
# API - VIA EXTRACTOR (VERSIÓN PRODUCCIÓN + FRONTEND READY)
# ==========================================================

import os
import time

# ==========================================================
# CARGA SEGURA DE VARIABLES DE ENTORNO
# ==========================================================
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

print("ENV SCRAPER (RENDER):", os.getenv("SCRAPER_API_KEY"))

# ==========================================================
# IMPORTS PRINCIPALES
# ==========================================================

from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

from main import run_pipeline
from services.ai_enricher import enrich_product


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

app = FastAPI(
    title="VIA Extractor API",
    version="4.2.0"
)

VIA_API_KEY = os.getenv("VIA_API_KEY")


# ==========================================================
# CONFIGURACIÓN CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# HEALTH CHECK — CRÍTICO PARA RENDER
# Sin este endpoint, Render recibe 404 y mata el proceso.
# ==========================================================

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "VIA Extractor API",
        "version": "4.2.0"
    }


# ==========================================================
# VALIDACIÓN API KEY
# ==========================================================

def validate_api_key(x_api_key: Optional[str]):
    if VIA_API_KEY:
        if x_api_key != VIA_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="API key inválida"
            )


# ==========================================================
# ENDPOINT PROTEGIDO
# ==========================================================

@app.post("/extract")
def extract_product_secure(
    url: str,
    x_api_key: Optional[str] = Header(default=None)
):
    validate_api_key(x_api_key)
    return process_extraction(url)


# ==========================================================
# ENDPOINT FRONTEND
# ==========================================================

@app.post("/extract-json")
def extract_product_json(
    body: Dict[str, Any] = Body(...)
):
    """
    Endpoint principal usado por frontend (Tampermonkey / VIA)
    """
    url = body.get("url")

    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=400,
            detail="URL válida requerida"
        )

    return process_extraction(url)


# ==========================================================
# LÓGICA CENTRAL
# ==========================================================

def process_extraction(url: str):

    try:
        start_time = time.time()

        print("\n======================================")
        print(f"🚀 Procesando URL: {url}")

        # --------------------------------------------------
        # 1. PIPELINE BASE
        # --------------------------------------------------
        result = run_pipeline(url)

        metadata = result.get("metadata", {})

        if metadata.get("estado_extraccion") == "failed":
            raise HTTPException(
                status_code=500,
                detail="Error en extracción del producto"
            )

        print("✅ Extracción completada")

        # --------------------------------------------------
        # VALIDACIÓN INTELIGENTE
        # --------------------------------------------------
        if not result or not result.get("title_raw"):
            return {
                "success": False,
                "error": "No se pudo extraer el producto. Amazon pudo haber bloqueado la solicitud."
            }

        # --------------------------------------------------
        # 2. ENRIQUECIMIENTO CON IA
        # --------------------------------------------------
        print("Ejecutando enriquecimiento con IA...")

        ai_result = enrich_product(result)

        print("IA completada")

        # --------------------------------------------------
        # 3. METADATA FINAL
        # --------------------------------------------------
        metadata = ai_result.get("metadata", {})

        metadata["tiempo_total_api_ms"] = int(
            (time.time() - start_time) * 1000
        )

        print(f"Tiempo total: {metadata['tiempo_total_api_ms']} ms")
        print("======================================\n")

        return {
            "success": True,
            "via_fields": ai_result.get("via_fields"),
            "metadata": metadata
        }

    except Exception as e:
        print(f"\n❌ ERROR EN API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
# ENDPOINT TEST IA
# ==========================================================

@app.get("/test-ai")
def test_ai():

    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {"error": "OPENAI_API_KEY no configurada"}

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Responde OK"}],
        max_tokens=5
    )

    return {
        "response": response.choices[0].message.content
    }