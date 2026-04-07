# ==========================================================
# SPEC NORMALIZER
# ----------------------------------------------------------
# Este módulo limpia y normaliza especificaciones técnicas
# provenientes de Amazon antes de enviarlas a la IA.
#
# RESPONSABILIDAD:
# - Limpiar unidades
# - Eliminar símbolos raros
# - Normalizar formatos
# - Mejorar consistencia técnica
#
# NO USA IA
# ==========================================================

import re


# ==========================================================
# LIMPIAR TEXTO TECNICO
# ==========================================================

def clean_text(value: str) -> str:
    """
    Limpia texto técnico eliminando símbolos
    extraños y espacios innecesarios.
    """

    if not value:
        return value

    # eliminar símbolo diámetro
    value = value.replace("Ø", "")
    value = value.replace("ø", "")
    value = value.replace("f", "")

    # eliminar espacios duplicados
    value = re.sub(r"\s+", " ", value)

    return value.strip()


# ==========================================================
# NORMALIZAR DIMENSIONES
# ==========================================================

def normalize_dimensions(value: str) -> str:
    """
    Normaliza dimensiones tipo:
    5,59 x 2,44 x 12,83 pulgadas
    """

    if not value:
        return value

    value = value.replace(",", ".")

    return value


# ==========================================================
# NORMALIZAR UNIDADES ELECTRICAS
# ==========================================================

def normalize_electrical_units(value: str) -> str:
    """
    Normaliza unidades eléctricas como:
    600V → 600 V
    1000A → 1000 A
    """

    if not value:
        return value

    value = re.sub(r"(\d)(V)", r"\1 V", value)
    value = re.sub(r"(\d)(A)", r"\1 A", value)
    value = re.sub(r"(\d)(W)", r"\1 W", value)
    value = re.sub(r"(\d)(Hz)", r"\1 Hz", value)

    return value


# ==========================================================
# NORMALIZAR CATEGORIAS DE SEGURIDAD
# ==========================================================

def normalize_cat_rating(value: str) -> str:
    """
    Convierte:
    CAT IV 600 V CAT III 1000 V
    en
    CAT IV 600 V / CAT III 1000 V
    """

    if not value:
        return value

    if "CAT" in value and "CAT" in value[5:]:
        value = value.replace("CAT III", "/ CAT III")

    return value


# ==========================================================
# NORMALIZAR ESPECIFICACIONES TECNICAS
# ==========================================================

def normalize_technical_specs(technical_details: dict) -> dict:
    """
    Aplica limpieza y normalización a todas las
    especificaciones técnicas extraídas.
    """

    if not technical_details:
        return technical_details

    normalized = {}

    for key, value in technical_details.items():

        if not isinstance(value, str):
            normalized[key] = value
            continue

        value = clean_text(value)

        value = normalize_dimensions(value)

        value = normalize_electrical_units(value)

        value = normalize_cat_rating(value)

        normalized[key] = value

    return normalized


# ==========================================================
# NORMALIZAR BULLETS
# ==========================================================

def normalize_bullets(bullets: list) -> list:
    """
    Limpia bullets del proveedor
    para mejorar su interpretación.
    """

    if not bullets:
        return bullets

    cleaned = []

    for bullet in bullets:

        bullet = clean_text(bullet)

        bullet = normalize_electrical_units(bullet)

        cleaned.append(bullet)

    return cleaned  