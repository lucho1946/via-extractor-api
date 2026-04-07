import os
import json
import re
from openai import OpenAI

from normalizer.spec_postprocessor import process_description


# ==========================================================
# FORMATEAR DETALLES TECNICOS
# ==========================================================

def format_technical_details(details: dict):
    if not details:
        return ""

    return "\n".join([f"{k}: {v}" for k, v in details.items()])


# ==========================================================
# DETECTAR PATRONES TECNICOS
# ==========================================================

def detect_technical_patterns(text: str):

    patterns = {
        "Voltaje": r"\b\d+\s?V\b",
        "Potencia": r"\b\d+\s?W\b",
        "Corriente": r"\b\d+\s?A\b",
        "Frecuencia": r"\b\d+\s?Hz\b",
        "Dimensión": r"\b\d+\s?mm\b",
        "Peso": r"\b\d+(\.\d+)?\s?(kg|lb)\b",
        "Temperatura": r"\b\d+\s?°C\b",
        "Capacidad": r"\b\d+\s?(L|litros|GB)\b"
    }

    specs = []

    for field, pattern in patterns.items():
        matches = re.findall(pattern, text)
        for m in matches:
            val = m if isinstance(m, str) else m[0]
            specs.append(f"{field}: {val}")

    return list(set(specs))


# ==========================================================
# LIMPIAR RESPUESTA IA
# ==========================================================

def clean_ai_output(text):

    text = text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "")

    return text.strip()


# ==========================================================
# NORMALIZAR UNIDADES
# ==========================================================

def normalize_units(text):

    replacements = {
        "milliamp_hours": "mAh",
        "milliamp hour": "mAh",
        "milliamp-hours": "mAh",
        "pounds": "lb",
        "pound": "lb",
        "inches": "in",
        "inch": "in"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


# ==========================================================
# PARSER ROBUSTO JSON
# ==========================================================

def safe_parse_json(content: str):

    try:
        return json.loads(content)
    except:
        pass

    json_match = re.search(r'\{.*\}', content, re.DOTALL)

    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass

    return None


# ==========================================================
# NUEVO: CONSTRUCTOR DE DESCRIPCIÓN LIMPIA
# ==========================================================

def build_description(structured):

    def format_list(items):
        return "\n".join([f"• {i}" for i in items if i])

    return f"""
DESCRIPCIÓN GENERAL
{structured.get("descripcion_general", "")}

VENTAJAS PRINCIPALES
{format_list(structured.get("ventajas", []))}

APLICACIONES
{format_list(structured.get("aplicaciones", []))}

CARACTERÍSTICAS TÉCNICAS
{format_list(structured.get("tecnica", []))}
""".strip()


# ==========================================================
# PROMPT ACTUALIZADO (JSON ESTRUCTURADO)
# ==========================================================

def build_prompt(
    title_raw,
    marca,
    bullets_text,
    description_text,
    tech_text,
    product_info_text,
    aplus_text,
    detected_specs_text
):

    return f"""
Actúa como un ingeniero de producto experto en redacción de fichas técnicas industriales.

REGLAS IMPORTANTES
- No inventar especificaciones
- No modificar unidades
- No repetir datos técnicos
- No incluir marca en el nombre
- No incluir referencia en el nombre
- RESPONDER ÚNICAMENTE JSON válido
- NO incluir texto fuera del JSON

DATOS DEL PRODUCTO

TITULO ORIGINAL:
{title_raw}

MARCA:
{marca}

CARACTERISTICAS:
{bullets_text}

DESCRIPCION:
{description_text}

TABLA TECNICA:
{tech_text}

INFORMACION:
{product_info_text}

A+ CONTENT:
{aplus_text}

ESPECIFICACIONES DETECTADAS:
{detected_specs_text}

RESPUESTA (JSON EXACTO):

{{
 "nombre": "string",
 "descripcion_general": "string",
 "ventajas": ["string"],
 "aplicaciones": ["string"],
 "tecnica": ["string"]
}}
"""


# ==========================================================
# FUNCION PRINCIPAL
# ==========================================================

def enrich_product(cleaned_data: dict):

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    client = OpenAI(api_key=api_key)

    # -----------------------------
    # DATOS BASE
    # -----------------------------
    referencia = cleaned_data.get("referencia")
    marca = cleaned_data.get("marca")
    costo = cleaned_data.get("costo")
    moneda = cleaned_data.get("moneda")
    peso = cleaned_data.get("peso")
    link = cleaned_data.get("url_origen")
    title_raw = cleaned_data.get("title_raw")

    bullets = cleaned_data.get("bullets") or []
    technical_details = cleaned_data.get("technical_details") or {}
    description = cleaned_data.get("product_description") or ""
    product_information = cleaned_data.get("product_information") or {}
    aplus = cleaned_data.get("aplus_content") or ""

    bullets_text = "\n".join(bullets)
    tech_text = format_technical_details(technical_details)
    product_info_text = format_technical_details(product_information)

    combined_text = " ".join([
        bullets_text,
        description,
        tech_text,
        product_info_text,
        aplus
    ])

    detected_specs_text = "\n".join(
        detect_technical_patterns(combined_text)
    )

    prompt = build_prompt(
        title_raw,
        marca,
        bullets_text,
        description,
        tech_text,
        product_info_text,
        aplus,
        detected_specs_text
    )

    try:

        print("\n🤖 LLAMANDO A IA...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde SOLO JSON válido"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1200,
            response_format={"type": "json_object"}  # 🔥 CLAVE
        )

        raw_content = response.choices[0].message.content

        print("\n================ IA RESPONSE =================")
        print(raw_content)
        print("=============================================\n")

        content = clean_ai_output(raw_content)
        structured = safe_parse_json(content)

        if not structured:
            raise Exception("No se pudo extraer JSON válido")

        nombre = structured.get("nombre")

        if nombre:
            nombre = normalize_units(nombre).strip()[:100]

        # 🔥 NUEVA DESCRIPCIÓN CONTROLADA
        descripcion = build_description(structured)
        descripcion = normalize_units(descripcion)
        descripcion = process_description(descripcion)

    except Exception as e:

        print("\n❌ ERROR IA COMPLETO:")
        print(e)

        nombre = title_raw or referencia or "Producto"

        descripcion = (
            description
            or bullets_text
            or tech_text
            or "Información técnica no disponible"
        )

        descripcion = process_description(descripcion)

    # ======================================================
    # MANTENEMOS COMPATIBILIDAD (IMPORTANTE)
    # ======================================================

    via_fields = {
        "21": referencia,
        "24": marca,
        "54": {
            "costo": costo,
            "moneda": moneda
        },
        "36": peso,
        "66": link,
        "69": nombre,
        "72": descripcion
    }

    metadata = cleaned_data.get("metadata", {})
    metadata["ai_enrichment"] = True

    return {
        "via_fields": via_fields,
        "metadata": metadata
    }