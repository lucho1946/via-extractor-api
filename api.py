# ==========================================================
# API - VIA EXTRACTOR (VERSIÓN CORREGIDA Y ESTABLE)
# ==========================================================

import os
import time
from dotenv import load_dotenv

# ==========================================================
# CARGA DE VARIABLES DE ENTORNO
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

print("ENV SCRAPER:", os.getenv("SCRAPER_API_KEY"))

# ==========================================================
# IMPORTS
# ==========================================================

from fastapi import FastAPI, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

from main import run_pipeline
from services.ai_enricher import enrich_product
from presentation.via_mapper import map_to_via_fields  # 🔥 NUEVO

# ==========================================================
# CONFIG
# ==========================================================

app = FastAPI(
    title="VIA Extractor API",
    version="4.2.0"
)

VIA_API_KEY = os.getenv("VIA_API_KEY")

# ==========================================================
# CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# VALIDACIÓN API KEY
# ==========================================================

def validate_api_key(x_api_key: Optional[str]):
    if VIA_API_KEY:
        if x_api_key != VIA_API_KEY:
            raise HTTPException(status_code=401, detail="API key inválida")

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
# ENDPOINT PRINCIPAL (FRONTEND)
# ==========================================================

@app.post("/extract-json")
def extract_product_json(
    body: Dict[str, Any] = Body(...)
):

    url = body.get("url")

    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="URL válida requerida")

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

        if not result or not result.get("title_raw"):
            return {
                "success": False,
                "error": "No se pudo extraer el producto. Amazon pudo haber bloqueado la solicitud."
            }

        print("Extracción completada")

        # --------------------------------------------------
        # 2. ENRIQUECIMIENTO IA
        # --------------------------------------------------
        print("Ejecutando IA...")

        enriched = enrich_product(result)

        print("IA completada")
        print("AI_KEYS:", enriched.keys())

        # --------------------------------------------------
        # 3. MAPPER VIA (🔥 FIX CRÍTICO)
        # --------------------------------------------------
        print("Generando VIA fields...")

        via_fields = map_to_via_fields(enriched)

        print("VIA_FIELDS:", via_fields)

        if not via_fields or not via_fields.get("21"):
            raise Exception("Error: VIA fields vacío o inválido")

        # --------------------------------------------------
        # 4. METADATA FINAL
        # --------------------------------------------------
        metadata = enriched.get("metadata", {})

        metadata["tiempo_total_api_ms"] = int(
            (time.time() - start_time) * 1000
        )

        print(f"Tiempo total: {metadata['tiempo_total_api_ms']} ms")
        print("======================================\n")

        return {
            "success": True,
            "via_fields": via_fields,
            "metadata": metadata
        }

    except Exception as e:

        print("\n❌ ERROR EN API:")
        print(str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================================================
# TEST IA
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