# ==========================================================
# PRODUCT CLEANER
# ----------------------------------------------------------
# Este módulo limpia y normaliza la información extraída
# desde Amazon antes de enviarla al AI_ENRICHER.
#
# RESPONSABILIDAD:
# - limpiar texto
# - identificar referencia
# - normalizar bullets
# - normalizar especificaciones técnicas
# - preparar estructura para IA
#
# NO USA IA
# ==========================================================

import re

from normalizer.spec_normalizer import (
    normalize_technical_specs,
    normalize_bullets
)


# ==========================================================
# LIMPIAR TEXTO GENERAL
# ==========================================================

def clean_text(value: str) -> str:
    """
    Limpia espacios innecesarios y caracteres raros.
    """

    if not value:
        return value

    value = value.strip()

    value = re.sub(r"\s+", " ", value)

    return value


# ==========================================================
# DETECTAR REFERENCIA
# ==========================================================

def detect_reference(title: str, technical_details: dict):
    """
    Intenta detectar referencia o modelo del producto.
    """

    if technical_details:

        possible_keys = [
            "model",
            "modelo",
            "model number",
            "item model number",
            "reference"
        ]

        for key in technical_details.keys():

            if key.lower() in possible_keys:

                value = technical_details.get(key)

                if value:
                    return value

    # fallback desde el título
    if title:

        match = re.search(r"[A-Z0-9]{3,}-[A-Z0-9]{2,}", title)

        if match:
            return match.group(0)

    return None


# ==========================================================
# LIMPIAR BULLETS
# ==========================================================

def clean_bullets(bullets: list):
    """
    Limpia lista de bullets del proveedor.
    """

    if not bullets:
        return []

    cleaned = []

    for bullet in bullets:

        bullet = clean_text(bullet)

        if bullet:
            cleaned.append(bullet)

    return cleaned


# ==========================================================
# LIMPIAR DETALLES TECNICOS
# ==========================================================

def clean_technical_details(details: dict):
    """
    Limpia claves y valores de especificaciones técnicas.
    """

    if not details:
        return {}

    cleaned = {}

    for key, value in details.items():

        key = clean_text(key)

        if isinstance(value, str):
            value = clean_text(value)

        cleaned[key] = value

    return cleaned


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def clean_product_data(raw_data: dict):
    """
    Función principal que limpia la información del producto.
    """

    if not raw_data:
        return {}

    # ------------------------------------------------------
    # EXTRAER DATOS CRUDOS
    # ------------------------------------------------------

    title_raw = raw_data.get("title") or raw_data.get("title_raw")

    marca = raw_data.get("brand") or raw_data.get("marca")

    bullets = raw_data.get("bullets", [])

    technical_details = raw_data.get("technical_details", {})

    precio = raw_data.get("price") or raw_data.get("price_value")

    moneda = raw_data.get("currency") or raw_data.get("price_currency")

    peso = raw_data.get("weight") or raw_data.get("peso")

    url_origen = raw_data.get("url") or raw_data.get("url_origen")

    # ------------------------------------------------------
    # LIMPIEZA BASICA
    # ------------------------------------------------------

    title_raw = clean_text(title_raw)

    marca = clean_text(marca)

    bullets = clean_bullets(bullets)

    technical_details = clean_technical_details(technical_details)

    # ------------------------------------------------------
    # NORMALIZACIÓN TECNICA (NUEVO MODULO)
    # ------------------------------------------------------

    bullets = normalize_bullets(bullets)

    technical_details = normalize_technical_specs(technical_details)

    # ------------------------------------------------------
    # DETECTAR REFERENCIA
    # ------------------------------------------------------

    referencia = detect_reference(title_raw, technical_details)

    # ------------------------------------------------------
    # ESTRUCTURA FINAL
    # ------------------------------------------------------

    cleaned_data = {

        "title_raw": title_raw,

        "marca": marca,

        "referencia": referencia,

        "bullets": bullets,

        "technical_details": technical_details,

        "costo": precio,

        "moneda": moneda,

        "peso": peso,

        "url_origen": url_origen,

        "metadata": raw_data.get("metadata", {})

    }

    return cleaned_data