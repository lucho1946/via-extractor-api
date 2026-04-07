# ==========================================================
# VIA FIELD MAPPER
# Convierte resultado limpio en estructura VIA
# ==========================================================

import re
from presentation.via_formatter import build_via_description


# ==========================================================
# UTILIDADES
# ==========================================================

def is_valid_reference(ref: str) -> bool:
    """
    Valida que la referencia sea real (no slug SEO)
    """

    if not ref:
        return False

    ref = str(ref).strip()

    # longitud básica
    if len(ref) < 4 or len(ref) > 25:
        return False

    # evitar slugs 
    if "-" in ref:
        parts = ref.split("-")

        # si tiene muchas palabras → es slug
        if len(parts) >= 3:
            return False

    # evitar palabras largas tipo descripción
    if ref.isalpha():
        return False

    # debe tener al menos un número o combinación
    if not any(char.isdigit() for char in ref):
        return False

    return True


def extract_reference_from_text(text: str):
    """
    Extrae referencias reales desde texto técnico (nivel robusto)
    """

    if not text:
        return None

    # Buscar patrones tipo modelo real
    candidates = re.findall(r"\b[A-Z0-9\-]{5,20}\b", text.upper())

    for candidate in candidates:

        candidate = candidate.strip()

        # ignorar si tiene muchas palabras separadas por guiones (slug)
        if candidate.count("-") >= 2:
            continue

        # ignorar si no tiene números (clave)
        if not any(c.isdigit() for c in candidate):
            continue

        # evitar palabras comunes
        if candidate.lower() in ["model", "modelo", "product"]:
            continue

        return candidate

    return None


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def map_to_via_fields(product: dict) -> dict:
    """
    Mapea el producto procesado al formato requerido por VIA.

    RESPONSABILIDAD:
    - Seleccionar campos correctos
    - Aplicar formateo final (solo presentación)
    - NO modificar lógica de negocio
    """

    # ======================================================
    # DATOS BASE
    # ======================================================

    referencia = product.get("referencia")
    marca = product.get("marca")
    costo = product.get("costo")
    moneda = product.get("moneda")
    peso = product.get("peso")
    url = product.get("url_origen")

    descripcion_corta = product.get("descripcion_corta")
    descripcion_larga_raw = product.get("descripcion_larga", "")

    ai_data = product.get("ai_data")

    # ======================================================
    # REFERENCIA INTELIGENTE
    # ======================================================

    if not is_valid_reference(referencia):

        # 1. Intentar desde IA (si existe)
        if ai_data and isinstance(ai_data, dict):
            posible_ref = ai_data.get("referencia_detectada")

            if is_valid_reference(posible_ref):
                referencia = posible_ref

        # 2. Intentar desde descripción
        if not is_valid_reference(referencia):
            ref_from_text = extract_reference_from_text(descripcion_larga_raw)

            if is_valid_reference(ref_from_text):
                referencia = ref_from_text

    # ======================================================
    # DESCRIPCIÓN LARGA (FORMATEADA)
    # ======================================================

    if ai_data and isinstance(ai_data, dict):
        descripcion_larga = build_via_description(ai_data)
    else:
        descripcion_larga = descripcion_larga_raw

    # ======================================================
    # ESTRUCTURA FINAL VIA
    # ======================================================

    return {

        # Referencia (mejorada)
        "21": referencia,

        # Marca
        "24": marca,

        # Precio
        "54": {
            "costo": costo,
            "moneda": moneda,
        },

        # Peso (opcional)
        "36": peso,

        # URL origen
        "66": url,

        # Descripción corta
        "69": descripcion_corta,

        # Descripción larga (formateada)
        "72": descripcion_larga,
    }