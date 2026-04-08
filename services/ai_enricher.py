# ==========================================================
# AI ENRICHER v2 — OPTIMIZADO Y ESTABLE
# ==========================================================

import os
import json
import re
from openai import OpenAI
from pydantic import BaseModel

from normalizer.spec_postprocessor import process_description


# ==========================================================
# SCHEMA CONTROLADO
# ==========================================================

class FichaTecnica(BaseModel):
    nombre: str
    descripcion_general: str
    caracteristicas_tecnicas: list[str] = []
    ventajas: list[str] = []
    aplicaciones: list[str] = []


# ==========================================================
# PROMPT MEJORADO
# ==========================================================

SYSTEM_PROMPT = """
Eres un ingeniero de producto experto en fichas técnicas industriales.

REGLAS:
- Responde SOLO JSON válido
- NO inventes datos
- NO repitas información
- NO incluyas marca ni referencia en el nombre
- Usa lenguaje técnico claro
- Máximo 6 elementos por lista

Formato obligatorio:
{
  "nombre": "",
  "descripcion_general": "",
  "caracteristicas_tecnicas": [],
  "ventajas": [],
  "aplicaciones": []
}
"""


# ==========================================================
# UTILIDADES
# ==========================================================

def safe_parse_json(text: str):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


def clean_list(items):
    return [str(i).strip() for i in items if i and len(str(i).strip()) > 3]


def build_description(ficha: FichaTecnica):

    def format_list(items):
        return "\n".join([f"• {i}" for i in items if i])

    sections = []

    if ficha.descripcion_general:
        sections.append(f"""DESCRIPCIÓN GENERAL
{ficha.descripcion_general}""")

    if ficha.caracteristicas_tecnicas:
        sections.append(f"""CARACTERÍSTICAS TÉCNICAS
{format_list(ficha.caracteristicas_tecnicas)}""")

    if ficha.ventajas:
        sections.append(f"""VENTAJAS PRINCIPALES
{format_list(ficha.ventajas)}""")

    if ficha.aplicaciones:
        sections.append(f"""APLICACIONES
{format_list(ficha.aplicaciones)}""")

    return "\n\n".join(sections).strip()


def build_fallback(cleaned_data: dict) -> FichaTecnica:

    title = cleaned_data.get("title_raw") or "Producto"
    bullets = cleaned_data.get("bullets") or []
    tech = cleaned_data.get("technical_details") or {}

    return FichaTecnica(
        nombre=title[:100],
        descripcion_general=bullets[0] if bullets else title,
        caracteristicas_tecnicas=[f"{k}: {v}" for k, v in tech.items()],
        ventajas=bullets[:5],
        aplicaciones=[]
    )


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def enrich_product(cleaned_data: dict):

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    client = OpenAI(api_key=api_key)

    title = cleaned_data.get("title_raw")
    marca = cleaned_data.get("marca")
    bullets = clean_list(cleaned_data.get("bullets") or [])
    tech = cleaned_data.get("technical_details") or {}
    description = cleaned_data.get("product_description") or ""

    prompt = f"""
TITULO: {title}
MARCA: {marca}

CARACTERISTICAS:
{chr(10).join(bullets)}

DESCRIPCION:
{description}

TABLA TECNICA:
{tech}
"""

    ficha = None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.05,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content
        parsed = safe_parse_json(raw)

        if not parsed:
            raise Exception("JSON inválido")

        ficha = FichaTecnica(**parsed)

        # Validación mínima
        if not ficha.descripcion_general:
            ficha.descripcion_general = title or "Producto industrial"

        if len(ficha.caracteristicas_tecnicas) > 8:
            ficha.caracteristicas_tecnicas = ficha.caracteristicas_tecnicas[:8]

    except Exception as e:
        print("Fallback IA:", e)
        ficha = build_fallback(cleaned_data)

    descripcion = build_description(ficha)
    descripcion = process_description(descripcion)

    cleaned_data["ai_data"] = ficha.model_dump()
    cleaned_data["descripcion_larga"] = descripcion

    return cleaned_data