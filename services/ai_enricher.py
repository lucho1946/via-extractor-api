# ==========================================================
# AI ENRICHER - VIA EXTRACTOR
# ----------------------------------------------------------
# Genera fichas técnicas estructuradas usando OpenAI.
# El output es SIEMPRE un JSON con schema fijo y validado.
#
# SCHEMA DE SALIDA GARANTIZADO:
# {
#   "descripcion_general": str,
#   "caracteristicas_tecnicas": [str, ...],
#   "ventajas": [str, ...],
#   "aplicaciones": [str, ...]
# }
#
# CAMBIOS v2 (mejora incremental sobre v1):
# - Schema fijo con Pydantic para validar output de IA
# - Prompt más estricto con ejemplos de formato
# - Fallback por sección (no pierde todo si la IA falla parcialmente)
# - Eliminada duplicación de normalize_units (ya existe en spec_normalizer)
# - caracteristicas_tecnicas reemplaza 'tecnica' (nombre más claro)
# - build_description() ahora usa order fijo e irrompible
# - detect_technical_patterns() movido a función pura reutilizable
# ==========================================================

import os
import json
import re
from openai import OpenAI
from pydantic import BaseModel, field_validator
from typing import List

from normalizer.spec_postprocessor import process_description


# ==========================================================
# SCHEMA OFICIAL DE SALIDA (Pydantic)
# ==========================================================

class FichaTecnica(BaseModel):
    """
    Contrato estricto del JSON que debe devolver la IA.
    Si la IA devuelve un campo vacío o malformado,
    Pydantic lo normaliza sin romper el pipeline.
    """
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
        return [str(item).strip() for item in v if item and str(item).strip()]


# ==========================================================
# FORMATEAR DETALLES TECNICOS
# ==========================================================

def format_technical_details(details: dict) -> str:
    """Convierte dict de specs en texto línea por línea."""
    if not details:
        return ""
    return "\n".join([f"{k}: {v}" for k, v in details.items()])


# ==========================================================
# DETECTAR PATRONES TECNICOS DESDE TEXTO
# ==========================================================

def detect_technical_patterns(text: str) -> List[str]:
    """
    Extrae valores técnicos detectados por regex.
    Devuelve lista de strings 'Campo: valor'.
    """
    patterns = {
        "Voltaje": r"\b\d+\s?V\b",
        "Potencia": r"\b\d+\s?W\b",
        "Corriente": r"\b\d+\s?A\b",
        "Frecuencia": r"\b\d+\s?Hz\b",
        "Dimensión": r"\b\d+\s?mm\b",
        "Peso": r"\b\d+(\.\d+)?\s?(kg|lb)\b",
        "Temperatura": r"\b\d+\s?°C\b",
        "Capacidad": r"\b\d+\s?(L|litros|GB|mAh)\b",
    }

    seen = set()
    specs = []

    for field, pattern in patterns.items():
        matches = re.findall(pattern, text)
        for m in matches:
            val = m if isinstance(m, str) else m[0]
            entry = f"{field}: {val}"
            if entry not in seen:
                seen.add(entry)
                specs.append(entry)

    return specs


# ==========================================================
# LIMPIAR RESPUESTA RAW DE LA IA
# ==========================================================

def clean_ai_output(text: str) -> str:
    """Elimina bloques markdown que la IA pueda añadir."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
    return text.strip()


# ==========================================================
# PARSER ROBUSTO JSON
# ==========================================================

def safe_parse_json(content: str) -> dict | None:
    """
    Intenta parsear JSON de forma tolerante.
    Primero intento directo, luego extrae el primer bloque {}.
    """
    try:
        return json.loads(content)
    except Exception:
        pass

    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return None


# ==========================================================
# VALIDAR Y NORMALIZAR OUTPUT DE IA
# ==========================================================

def validate_ai_output(raw: dict) -> FichaTecnica:
    """
    Valida el dict devuelto por la IA contra el schema oficial.
    Si la IA usó 'tecnica' en vez de 'caracteristicas_tecnicas'
    (compatibilidad con prompts anteriores), lo remapea.
    """
    # Compatibilidad con campo 'tecnica' del schema v1
    if "tecnica" in raw and "caracteristicas_tecnicas" not in raw:
        raw["caracteristicas_tecnicas"] = raw.pop("tecnica")

    return FichaTecnica(**raw)


# ==========================================================
# CONSTRUCTOR DE DESCRIPCIÓN (ORDEN FIJO)
# ==========================================================

def build_description(ficha: FichaTecnica) -> str:
    """
    Construye texto final con secciones en orden fijo.
    El orden NUNCA cambia independientemente del output de la IA.
    """

    def format_list(items: List[str]) -> str:
        return "\n".join([f"• {item}" for item in items if item])

    sections = [
        ("DESCRIPCIÓN GENERAL", ficha.descripcion_general),
        ("CARACTERÍSTICAS TÉCNICAS", format_list(ficha.caracteristicas_tecnicas)),
        ("VENTAJAS PRINCIPALES", format_list(ficha.ventajas)),
        ("APLICACIONES", format_list(ficha.aplicaciones)),
    ]

    parts = []
    for title, content in sections:
        if content and content.strip():
            parts.append(f"{title}\n{content.strip()}")

    return "\n\n".join(parts)


# ==========================================================
# CONSTRUIR FALLBACK DESDE DATOS CRUDOS
# ==========================================================

def build_fallback_ficha(
    bullets: list,
    technical_details: dict,
    description: str,
    detected_specs: List[str],
) -> FichaTecnica:
    """
    Si la IA falla completamente, construye una ficha básica
    reorganizando los datos disponibles sin inventar nada.
    """
    descripcion_general = description[:300] if description else (
        bullets[0] if bullets else "Información técnica no disponible."
    )

    # Usar tabla técnica + specs detectadas como características
    caracteristicas = []
    for k, v in (technical_details or {}).items():
        caracteristicas.append(f"{k}: {v}")
    for spec in detected_specs:
        if spec not in caracteristicas:
            caracteristicas.append(spec)

    # Usar bullets como ventajas
    ventajas = [b for b in (bullets or []) if len(b) > 15][:6]

    return FichaTecnica(
        descripcion_general=descripcion_general,
        caracteristicas_tecnicas=caracteristicas[:10],
        ventajas=ventajas,
        aplicaciones=[],
    )


# ==========================================================
# PROMPT CON SCHEMA ESTRICTO Y EJEMPLOS
# ==========================================================

def build_prompt(
    title_raw: str,
    marca: str,
    bullets_text: str,
    description_text: str,
    tech_text: str,
    product_info_text: str,
    aplus_text: str,
    detected_specs_text: str,
) -> str:
    return f"""Eres un redactor técnico industrial experto en fichas de productos.

INSTRUCCIONES ESTRICTAS:
- Responde ÚNICAMENTE con el JSON especificado. Sin texto adicional.
- NO inventes especificaciones que no estén en los datos.
- NO incluyas la marca ni la referencia en la descripción general.
- Cada ítem de las listas debe ser una oración completa y concisa.
- Si no hay información suficiente para una sección, devuelve lista vacía [].
- Las características técnicas deben tener formato "Clave: Valor" (ej: "Voltaje: 600 V").

SCHEMA REQUERIDO (respeta exactamente estos campos):
{{
  "descripcion_general": "2-3 oraciones describiendo el producto y su función principal",
  "caracteristicas_tecnicas": ["Clave: Valor", "Clave: Valor"],
  "ventajas": ["Beneficio o diferenciador clave", "..."],
  "aplicaciones": ["Caso de uso o industria", "..."]
}}

EJEMPLO DE RESPUESTA CORRECTA:
{{
  "descripcion_general": "Multímetro digital de alta precisión con tecnología True RMS para mediciones exactas en cargas no lineales.",
  "caracteristicas_tecnicas": ["Voltaje máximo: 600 V", "Resolución: 0.1 mV", "Categoría de seguridad: CAT III"],
  "ventajas": ["Detección de voltaje sin contacto integrada", "Selección automática AC/DC", "Pantalla retroiluminada para ambientes oscuros"],
  "aplicaciones": ["Instalaciones eléctricas industriales", "Mantenimiento de equipos electrónicos", "Diagnóstico de tableros eléctricos"]
}}

DATOS DEL PRODUCTO:

TÍTULO ORIGINAL:
{title_raw}

MARCA:
{marca}

CARACTERÍSTICAS (bullets):
{bullets_text or "No disponible"}

DESCRIPCIÓN:
{description_text or "No disponible"}

TABLA TÉCNICA:
{tech_text or "No disponible"}

INFORMACIÓN ADICIONAL:
{product_info_text or "No disponible"}

A+ CONTENT:
{aplus_text or "No disponible"}

ESPECIFICACIONES DETECTADAS AUTOMÁTICAMENTE:
{detected_specs_text or "Ninguna detectada"}

RESPONDE SOLO EL JSON:"""


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def enrich_product(cleaned_data: dict) -> dict:
    """
    Enriquece el producto con IA y devuelve estructura
    compatible con el contrato VIA.

    RETORNA:
    {{
        "via_fields": {{
            "21": referencia,
            "24": marca,
            "54": {{"costo": ..., "moneda": ...}},
            "36": peso,
            "66": link,
            "69": nombre,
            "72": descripcion_larga
        }},
        "metadata": {{...}}
    }}
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    client = OpenAI(api_key=api_key)

    # --------------------------------------------------
    # DATOS BASE
    # --------------------------------------------------
    referencia  = cleaned_data.get("referencia")
    marca       = cleaned_data.get("marca") or ""
    costo       = cleaned_data.get("costo")
    moneda      = cleaned_data.get("moneda")
    peso        = cleaned_data.get("peso")
    link        = cleaned_data.get("url_origen")
    title_raw   = cleaned_data.get("title_raw") or ""

    bullets             = cleaned_data.get("bullets") or []
    technical_details   = cleaned_data.get("technical_details") or {}
    description         = cleaned_data.get("product_description") or ""
    product_information = cleaned_data.get("product_information") or {}
    aplus               = cleaned_data.get("aplus_content") or ""

    # --------------------------------------------------
    # PREPARAR TEXTOS PARA EL PROMPT
    # --------------------------------------------------
    bullets_text        = "\n".join(bullets)
    tech_text           = format_technical_details(technical_details)
    product_info_text   = format_technical_details(product_information)

    combined_text = " ".join(filter(None, [
        bullets_text, description, tech_text, product_info_text, aplus
    ]))

    detected_specs      = detect_technical_patterns(combined_text)
    detected_specs_text = "\n".join(detected_specs)

    prompt = build_prompt(
        title_raw, marca, bullets_text, description,
        tech_text, product_info_text, aplus, detected_specs_text,
    )

    # --------------------------------------------------
    # LLAMADA A LA IA
    # --------------------------------------------------
    ficha: FichaTecnica | None = None
    nombre = title_raw or referencia or "Producto"

    try:
        print("\n🤖 LLAMANDO A IA...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un redactor técnico industrial. "
                        "Responde SOLO JSON válido con el schema solicitado. "
                        "Sin texto adicional, sin bloques markdown."
                    )
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,          # baja temperatura = más consistencia
            max_tokens=1200,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content

        print("\n================ IA RESPONSE =================")
        print(raw_content)
        print("=============================================\n")

        parsed = safe_parse_json(clean_ai_output(raw_content))

        if parsed:
            ficha = validate_ai_output(parsed)

            # Extraer nombre del JSON si la IA lo devolvió
            nombre_ia = parsed.get("nombre", "").strip()
            if nombre_ia:
                nombre = nombre_ia[:100]
        else:
            raise ValueError("No se pudo parsear el JSON de la IA")

    except Exception as e:
        print(f"\n❌ ERROR IA: {e}")
        print("→ Usando fallback estructurado desde datos crudos")

    # --------------------------------------------------
    # FALLBACK POR SECCIÓN (no pierde la estructura)
    # --------------------------------------------------
    if ficha is None:
        ficha = build_fallback_ficha(
            bullets, technical_details, description, detected_specs
        )

    # --------------------------------------------------
    # CONSTRUIR DESCRIPCIÓN FINAL (ORDEN FIJO)
    # --------------------------------------------------
    descripcion = build_description(ficha)
    descripcion = process_description(descripcion)

    # --------------------------------------------------
    # METADATA
    # --------------------------------------------------
    metadata = cleaned_data.get("metadata", {})
    metadata["ai_enrichment"] = True
    metadata["ai_fallback"] = (ficha is not None and parsed is None) if 'parsed' in dir() else True

    # --------------------------------------------------
    # RETORNO COMPATIBLE CON CONTRATO VIA EXISTENTE
    # --------------------------------------------------
    return {
        "via_fields": {
            "21": referencia,
            "24": marca,
            "54": {"costo": costo, "moneda": moneda},
            "36": peso,
            "66": link,
            "69": nombre,
            "72": descripcion,
        },
        "metadata": metadata,
    }