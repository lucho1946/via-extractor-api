# ==========================================================
# AI ENRICHER - VIA EXTRACTOR v8 (FICHAS TÉCNICAS COMPLETAS)
# ==========================================================

import os
import json
import re
from openai import OpenAI
from pydantic import BaseModel, field_validator
from typing import List


# ==========================================================
# SCHEMA EXTENDIDO
# ==========================================================

class FichaTecnica(BaseModel):
    descripcion_general: str = ""
    caracteristicas_tecnicas: List[str] = []
    especificaciones_electricas: List[str] = []
    dimensiones: List[str] = []
    certificaciones: List[str] = []
    contenido_del_paquete: List[str] = []
    ventajas: List[str] = []
    aplicaciones: List[str] = []

    @field_validator("descripcion_general", mode="before")
    @classmethod
    def clean_descripcion(cls, v):
        return str(v).strip() if v else ""

    @field_validator(
        "caracteristicas_tecnicas",
        "especificaciones_electricas",
        "dimensiones",
        "certificaciones",
        "contenido_del_paquete",
        "ventajas",
        "aplicaciones",
        mode="before"
    )
    @classmethod
    def clean_list(cls, v):
        if not v or not isinstance(v, list):
            return []
        return [str(item).strip() for item in v if item and str(item).strip()]


# ==========================================================
# VALORES VACÍOS / SIN DATOS
# ==========================================================

NO_DATA_VALUES = {
    "no data", "n/a", "not available", "none", "no disponible",
    "not specified", "no aplica", "-", "—", "na", "null", "unknown",
    "no information", "sin datos", "sin información"
}

def is_no_data(value: str) -> bool:
    return value.strip().lower() in NO_DATA_VALUES


# ==========================================================
# TÍTULO INTELIGENTE
# ==========================================================

def build_short_title(title_raw: str, marca: str):
    if not title_raw:
        return "Producto"

    title = title_raw

    if marca:
        title = title.replace(marca, "").strip()

    title = re.split(r"[-|–|,]", title)[0]
    title = re.sub(r"\(.*?\)", "", title)

    return title.strip()[:80]


# ==========================================================
# LIMPIEZA DE SPECS (filtra "no data" y deduplica por clave)
# ==========================================================

def clean_technical_specs(tech: dict) -> List[str]:
    specs = []
    seen_keys = set()
    seen_specs = set()

    for k, v in tech.items():
        key = str(k).strip()
        value = str(v).strip()

        if not value or len(value) < 2:
            continue

        if is_no_data(value):
            continue

        key_lower = key.lower()

        if any(x in key_lower for x in [
            "price", "precio", "rating", "review", "opiniones",
            "marca", "brand", "modelo", "model", "seller", "id"
        ]):
            continue

        if any(x in key_lower for x in [
            "uso", "application", "feature", "about"
        ]):
            continue

        if key_lower in seen_keys:
            continue
        seen_keys.add(key_lower)

        spec = f"{key}: {value}"

        if spec.lower() not in seen_specs:
            seen_specs.add(spec.lower())
            specs.append(spec)

    return specs


# ==========================================================
# BUILD DESCRIPTION - TODAS LAS SECCIONES
# ==========================================================

def build_description(ficha: FichaTecnica) -> str:

    def clean_text(text):
        if not text:
            return ""
        return re.sub(r"(qué es:|para qué sirve:)", "", text, flags=re.IGNORECASE).strip()

    def format_list(items):
        return "\n".join([f"- {clean_text(i)}" for i in items if i and clean_text(i)])

    sections = []

    if ficha.descripcion_general:
        sections.append(
            "DESCRIPCIÓN GENERAL\n" +
            clean_text(ficha.descripcion_general[:400])
        )

    if ficha.caracteristicas_tecnicas:
        specs = format_list(ficha.caracteristicas_tecnicas)
        if specs.strip():
            sections.append("CARACTERÍSTICAS TÉCNICAS\n" + specs)

    if ficha.especificaciones_electricas:
        elec = format_list(ficha.especificaciones_electricas)
        if elec.strip():
            sections.append("ESPECIFICACIONES ELÉCTRICAS\n" + elec)

    if ficha.dimensiones:
        dims = format_list(ficha.dimensiones)
        if dims.strip():
            sections.append("DIMENSIONES Y PESO\n" + dims)

    if ficha.certificaciones:
        certs = format_list(ficha.certificaciones)
        if certs.strip():
            sections.append("CERTIFICACIONES Y NORMAS\n" + certs)

    if ficha.contenido_del_paquete:
        contenido = format_list(ficha.contenido_del_paquete)
        if contenido.strip():
            sections.append("CONTENIDO DEL PAQUETE\n" + contenido)

    if ficha.ventajas:
        ventajas = list(dict.fromkeys(ficha.ventajas))
        v_text = format_list(ventajas[:6])
        if v_text.strip():
            sections.append("VENTAJAS PRINCIPALES\n" + v_text)

    if ficha.aplicaciones:
        aplicaciones = list(dict.fromkeys(ficha.aplicaciones))
        a_text = format_list(aplicaciones[:6])
        if a_text.strip():
            sections.append("APLICACIONES\n" + a_text)

    return "\n\n".join(sections) + "\n"


# ==========================================================
# UTILIDADES
# ==========================================================

def safe_parse_json(content: str):
    try:
        return json.loads(content)
    except Exception:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return None


# ==========================================================
# FALLBACK ROBUSTO
# ==========================================================

def build_fallback_ficha(bullets, technical_details, description):
    descripcion_general = description[:400] if description else (
        bullets[0] if bullets else "Información técnica no disponible"
    )

    caracteristicas = clean_technical_specs(technical_details)

    return FichaTecnica(
        descripcion_general=descripcion_general,
        caracteristicas_tecnicas=caracteristicas,
        especificaciones_electricas=[],
        dimensiones=[],
        certificaciones=[],
        contenido_del_paquete=[],
        ventajas=bullets[:5],
        aplicaciones=[]
    )


# ==========================================================
# PROMPT MEJORADO
# ==========================================================

def build_prompt(title: str, bullets: list, description: str, tech: dict) -> str:
    bullets_text = "\n".join(f"- {b}" for b in bullets) if bullets else "No disponible"
    tech_text = "\n".join(f"  {k}: {v}" for k, v in tech.items()) if tech else "No disponible"
    desc_text = description[:600] if description else "No disponible"

    return f"""Eres un ingeniero técnico industrial experto en la creación de fichas técnicas profesionales para catálogos industriales.

Tu tarea es generar una ficha técnica COMPLETA, PRECISA y PROFESIONAL en ESPAÑOL para el siguiente producto.

REGLAS OBLIGATORIAS:
1. Responde ÚNICAMENTE en español
2. NO incluyas nombre de marca, modelo ni precio en ningún campo
3. NO repitas información entre secciones
4. Cada ítem debe ser específico, concreto y de valor técnico real
5. Si una sección no aplica al producto, devuelve lista vacía []
6. Las características técnicas deben estar en formato "Parámetro: Valor con unidades"
7. NO incluyas características cuyo valor sea "no data", "N/A", "no disponible", "-" o similar
8. NO repitas la misma característica con distintas unidades (ej: "95%" y "95 por ciento" es lo mismo, incluye solo una)

ESTRUCTURA DEL JSON:

"descripcion_general"
  - Descripción técnica concisa del producto: qué es, para qué sirve y cuál es su función principal
  - Entre 150 y 350 caracteres
  - Sin mencionar marca ni modelo

"caracteristicas_tecnicas"
  - Lista de especificaciones técnicas clave del producto
  - Mínimo 5 ítems, máximo 15
  - Formato: "Parámetro: Valor" (ej: "Rango de medición: 0–600 V AC/DC")
  - Incluir solo parámetros con valores reales y concretos

"especificaciones_electricas"
  - Solo completar si el producto es eléctrico o electrónico
  - Voltaje de alimentación, corriente máxima, potencia, frecuencia, tipo de señal, etc.
  - Lista vacía [] si no aplica

"dimensiones"
  - Peso, dimensiones físicas (largo × ancho × alto), tamaño de pantalla, etc.
  - Solo incluir si hay datos disponibles en los specs del producto
  - Lista vacía [] si no aplica

"certificaciones"
  - Normas de seguridad y certificaciones (CE, UL, CSA, IEC, IP, NEMA, CAT, RoHS, NIST, etc.)
  - Solo incluir si se mencionan explícitamente en los datos del producto
  - Lista vacía [] si no aplica

"contenido_del_paquete"
  - Elementos incluidos en la caja o paquete del producto
  - Solo incluir si se mencionan en los datos del producto
  - Lista vacía [] si no aplica

"ventajas"
  - Principales beneficios y puntos fuertes del producto desde perspectiva técnica/industrial
  - Mínimo 3 ítems, máximo 6
  - Frases concisas y orientadas a valor para el usuario técnico

"aplicaciones"
  - Sectores, industrias o casos de uso donde se aplica el producto
  - Mínimo 3 ítems, máximo 6
  - Frases concisas (ej: "Detección de gases en espacios confinados")

DATOS DEL PRODUCTO:
Título: {title}

Características del producto:
{bullets_text}

Descripción:
{desc_text}

Especificaciones técnicas:
{tech_text}
"""


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def enrich_product(cleaned_data: dict):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    title = cleaned_data.get("title_raw") or ""
    marca = cleaned_data.get("marca")
    bullets = cleaned_data.get("bullets") or []
    tech = cleaned_data.get("technical_details") or {}
    description = cleaned_data.get("product_description") or ""

    prompt = build_prompt(title, bullets, description, tech)

    ficha = None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en fichas técnicas industriales. "
                        "Responde ÚNICAMENTE con JSON válido que cumpla exactamente la estructura solicitada. "
                        "No incluyas texto fuera del JSON."
                    )
                },
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
    # INYECCIÓN DE SPECS EXTRAÍDAS (deduplicada por clave)
    # ======================================================

    specs_final = clean_technical_specs(tech)

    if not specs_final and tech:
        specs_final = [f"{k}: {v}" for k, v in list(tech.items())[:5]]

    seen_keys = set()
    seen_specs = set()
    specs_unicas = []

    for spec in specs_final + ficha.caracteristicas_tecnicas:
        spec = spec.strip()
        key_part = spec.split(":")[0].strip().lower()
        spec_lower = spec.lower()

        if key_part in seen_keys:
            continue
        if spec_lower in seen_specs:
            continue

        seen_keys.add(key_part)
        seen_specs.add(spec_lower)
        specs_unicas.append(spec)

    ficha.caracteristicas_tecnicas = specs_unicas

    # ======================================================
    # DESCRIPCIÓN FINAL
    # ======================================================

    descripcion = build_description(ficha)
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
