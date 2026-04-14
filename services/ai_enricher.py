# ==========================================================
# AI ENRICHER - VIA EXTRACTOR v7 (REFINADO Y PROFESIONAL)
# ==========================================================

import os
import json
import re
from openai import OpenAI
from pydantic import BaseModel, field_validator
from typing import List

from normalizer.spec_postprocessor import process_description


# ==========================================================
# SCHEMA
# ==========================================================

class FichaTecnica(BaseModel):
    descripcion_general: str = ""
    caracteristicas_tecnicas: List[str] = []
    ventajas: List[str] = []
    aplicaciones: List[str] = []

    @field_validator("descripcion_general", mode="before")
    @classmethod
    def clean_descripcion(cls, v):
        return str(v).strip() if v else ""

    @field_validator("caracteristicas_tecnicas", "ventajas", "aplicaciones", mode="before")
    @classmethod
    def clean_list(cls, v):
        if not v or not isinstance(v, list):
            return []
        return [str(item).strip() for item in v if item]


# ==========================================================
# 🔥 TÍTULO INTELIGENTE (MEJORADO)
# ==========================================================

def build_short_title(title_raw: str, marca: str):

    if not title_raw:
        return "Producto"

    title = title_raw

    # eliminar marca
    if marca:
        title = title.replace(marca, "").strip()

    # cortar ruido SEO
    title = re.split(r"[-|–|,]", title)[0]

    # eliminar paréntesis
    title = re.sub(r"\(.*?\)", "", title)

    return title.strip()[:80]


# ==========================================================
# 🔥 LIMPIEZA DE SPECS (PROFESIONAL)
# ==========================================================

def clean_technical_specs(tech: dict) -> List[str]:

    specs = []
    seen = set()

    for k, v in tech.items():

        key = str(k).strip()
        value = str(v).strip()

        if not value or len(value) < 2:
            continue

        key_lower = key.lower()

        # ❌ eliminar basura
        if any(x in key_lower for x in [
            "price", "precio", "rating", "review", "opiniones",
            "marca", "brand", "modelo", "model",
            "seller", "id"
        ]):
            continue

        # ❌ eliminar contenido no técnico
        if any(x in key_lower for x in [
            "uso", "application", "feature", "about"
        ]):
            continue

        spec = f"{key}: {value}"

        # evitar duplicados
        if spec.lower() not in seen:
            seen.add(spec.lower())
            specs.append(spec)

    return specs


# ==========================================================
# 🔥 BUILD DESCRIPTION (ESTRUCTURA FINAL CORRECTA)
# ==========================================================

def build_description(ficha: FichaTecnica) -> str:

    def clean_text(text):
        if not text:
            return ""
        return re.sub(r"(qué es:|para qué sirve:)", "", text, flags=re.IGNORECASE).strip()

    def format_list(items):
        return "\n".join([f"- {clean_text(i)}" for i in items if i])

    partes = []

    # =============================
    # DESCRIPCIÓN GENERAL
    # =============================
    if ficha.descripcion_general:
        partes.append(
            "DESCRIPCIÓN GENERAL\n" +
            clean_text(ficha.descripcion_general[:280])
        )

    # =============================
    # CARACTERÍSTICAS TÉCNICAS
    # =============================
    if ficha.caracteristicas_tecnicas:

        specs = format_list(ficha.caracteristicas_tecnicas)

        if specs.strip():
            partes.append(f"\nCARACTERÍSTICAS TÉCNICAS\n{specs}\n")

    # =============================
    # VENTAJAS
    # =============================
    if ficha.ventajas:

        ventajas = list(dict.fromkeys(ficha.ventajas))

        partes.append(
            "VENTAJAS PRINCIPALES\n" +
            format_list(ventajas[:5])
        )

    # =============================
    # APLICACIONES
    # =============================
    if ficha.aplicaciones:

        aplicaciones = list(dict.fromkeys(ficha.aplicaciones))

        partes.append(
            "APLICACIONES\n" +
            format_list(aplicaciones[:5])
        )

    # 🔥 separación real entre bloques
    return "\n\n".join([p.strip() for p in partes if p.strip()]) + "\n"


# ==========================================================
# UTILIDADES
# ==========================================================

def safe_parse_json(content: str):
    try:
        return json.loads(content)
    except:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


# ==========================================================
# FALLBACK ROBUSTO
# ==========================================================

def build_fallback_ficha(bullets, technical_details, description):

    descripcion_general = description[:300] if description else (
        bullets[0] if bullets else "Información técnica no disponible"
    )

    caracteristicas = clean_technical_specs(technical_details)

    return FichaTecnica(
        descripcion_general=descripcion_general,
        caracteristicas_tecnicas=caracteristicas,
        ventajas=bullets[:5],
        aplicaciones=[]
    )


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def enrich_product(cleaned_data: dict):

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    title = cleaned_data.get("title_raw")
    marca = cleaned_data.get("marca")
    bullets = cleaned_data.get("bullets") or []
    tech = cleaned_data.get("technical_details") or {}
    description = cleaned_data.get("product_description") or ""

    # ======================================================
    # PROMPT OPTIMIZADO (SIN CAMBIAR TU LÓGICA)
    # ======================================================

    prompt = f"""
Eres un ingeniero técnico industrial experto en la creacion de fichas tecnicas.

Reglas:
- No incluir marca ni modelo
- No incluir precio
- No mezclar secciones

Devuelve JSON con:
descripcion_general
caracteristicas_tecnicas
ventajas
aplicaciones

Datos:
{title}
{bullets}
{description}
{tech}
"""

    ficha = None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde SOLO JSON válido"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        parsed = safe_parse_json(response.choices[0].message.content)

        ficha = FichaTecnica(**parsed)

    except Exception as e:
        print("Fallback IA:", e)
        ficha = build_fallback_ficha(bullets, tech, description)

    # ======================================================
    # 🔥 INYECCIÓN CONTROLADA DE SPECS (VERSIÓN CORRECTA)
    # ======================================================

    specs_final = clean_technical_specs(tech)

    # fallback si no hay nada
    if not specs_final and tech:
        specs_final = [f"{k}: {v}" for k, v in list(tech.items())[:5]]

    # 🔥 evitar duplicados y mantener orden
    specs_unicas = []
    seen = set()

    for spec in specs_final + ficha.caracteristicas_tecnicas:

        clean = spec.strip().lower()

        if clean not in seen:
            seen.add(clean)
            specs_unicas.append(spec)

    # ahora sí reemplazamos
    ficha.caracteristicas_tecnicas = specs_unicas

    # ======================================================
    # FINAL
    # ======================================================

    descripcion_raw = build_description(ficha)

    # ======================================================
    # USAMOS DIRECTAMENTE LA DESCRIPCIÓN (SIN POST-PROCESO)
    # ======================================================

    descripcion = descripcion_raw

    descripcion = descripcion.replace("\\n", "\n")

    return {
        "via_fields": {
            "21": cleaned_data.get("referencia"),
            "24": marca,
            "54": {
                "costo": cleaned_data.get("costo"),
                "moneda": cleaned_data.get("moneda"),
            },
            "36": cleaned_data.get("peso"),
            "66": cleaned_data.get("url_origen"),
            "69": build_short_title(title, marca),
            "72": descripcion
        },
        "metadata": cleaned_data.get("metadata", {})
    }