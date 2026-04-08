# ==========================================================
# VIA FIELD MAPPER (REFINADO - DATA QUALITY)
# ==========================================================

import re
from presentation.via_formatter import build_via_description


# ==========================================================
# UTILIDADES
# ==========================================================

def is_valid_reference(ref: str) -> bool:

    if not ref:
        return False

    ref = str(ref).strip()

    if len(ref) < 4 or len(ref) > 25:
        return False

    if "-" in ref:
        parts = ref.split("-")
        if len(parts) >= 3:
            return False

    if ref.isalpha():
        return False

    if not any(char.isdigit() for char in ref):
        return False

    return True


def extract_reference_from_text(text: str):

    if not text:
        return None

    candidates = re.findall(r"\b[A-Z0-9\-]{5,20}\b", text.upper())

    for candidate in candidates:

        candidate = candidate.strip()

        if candidate.count("-") >= 2:
            continue

        if not any(c.isdigit() for c in candidate):
            continue

        if candidate.lower() in ["model", "modelo", "product"]:
            continue

        return candidate

    return None


# ==========================================================
# NUEVO: DESCRIPCIÓN CORTA INTELIGENTE
# ==========================================================

def build_short_description(product: dict) -> str:

    # 1. Campo original
    desc = product.get("descripcion_corta")

    if desc and len(desc.strip()) > 10:
        return desc.strip()[:120]

    # 2. IA (nombre)
    ai_data = product.get("ai_data")
    if ai_data and isinstance(ai_data, dict):
        nombre = ai_data.get("nombre")
        if nombre and len(nombre.strip()) > 5:
            return nombre.strip()[:120]

    # 3. Título original
    title = product.get("title_raw")
    if title:
        return title.strip()[:120]

    # 4. Último recurso
    descripcion_larga = product.get("descripcion_larga")
    if descripcion_larga:
        return descripcion_larga.strip().split("\n")[0][:120]

    return "Producto industrial"


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def map_to_via_fields(product: dict) -> dict:

    referencia = product.get("referencia")
    marca = product.get("marca")
    costo = product.get("costo")
    moneda = product.get("moneda")
    peso = product.get("peso")
    url = product.get("url_origen")

    descripcion_larga_raw = product.get("descripcion_larga", "")
    ai_data = product.get("ai_data")

    # ======================================================
    # REFERENCIA INTELIGENTE
    # ======================================================

    if not is_valid_reference(referencia):

        if ai_data and isinstance(ai_data, dict):
            posible_ref = ai_data.get("referencia_detectada")

            if is_valid_reference(posible_ref):
                referencia = posible_ref

        if not is_valid_reference(referencia):
            ref_from_text = extract_reference_from_text(descripcion_larga_raw)

            if is_valid_reference(ref_from_text):
                referencia = ref_from_text

    # ======================================================
    # DESCRIPCIÓN CORTA (FIX CRÍTICO)
    # ======================================================

    descripcion_corta = build_short_description(product)

    # ======================================================
    # DESCRIPCIÓN LARGA
    # ======================================================

    if ai_data and isinstance(ai_data, dict):
        descripcion_larga = build_via_description(ai_data)
    else:
        descripcion_larga = descripcion_larga_raw

    # ======================================================
    # ESTRUCTURA FINAL
    # ======================================================

    return {

        "21": referencia,
        "24": marca,

        "54": {
            "costo": costo,
            "moneda": moneda,
        },

        "36": peso,
        "66": url,

        "69": descripcion_corta,

        "72": descripcion_larga,
    }