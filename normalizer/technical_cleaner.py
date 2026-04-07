# ==========================================================
# TECHNICAL CLEANER (Limpia Campo por Campo + Filtro Global)
# Limpieza y normalización universal de especificaciones
# Compatible con cualquier categoría de Amazon
# ==========================================================

import re


# ==========================================================
# NORMALIZADOR UNIVERSAL DE UNIDADES
# ==========================================================

def normalize_units(value: str) -> str:
    """
    Limpia y estandariza unidades técnicas sin depender
    de una categoría específica.
    """

    value = value.strip()

    replacements = {
        # Longitud
        "millimeters": "mm",
        "millimeter": "mm",
        "milímetros": "mm",
        "pulgadas": "in",
        "inches": "in",
        "inch": "in",

        # Peso
        "Libras": "lb",
        "libras": "lb",
        "pounds": "lb",

        # Energía / potencia
        "milliamp_hours": "mAh",
        "milliamperios hora": "mAh",
        "vatios": "W",
        "watts": "W",

        # Velocidad
        "Páginas por minuto": "ppm",
        "pages per minute": "ppm",

        # Volumen
        "onzas líquidas": "fl oz",

        # Área
        "pies cuadrados": "ft²",
        "square feet": "ft²",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value


# ==========================================================
# LIMPIEZA GENERAL DE CLAVE
# ==========================================================

def clean_key(key: str) -> str:
    """
    Limpia etiquetas técnicas sin alterar su significado.
    """

    key = key.strip()
    key = re.sub(r"\s+", " ", key)

    return key[:1].upper() + key[1:]


# ==========================================================
# LIMPIEZA GENERAL DE VALOR
# ==========================================================

def clean_value(value: str) -> str:
    """
    Limpia valor técnico de forma universal.
    """

    value = value.strip()
    value = re.sub(r"\s+", " ", value)
    value = normalize_units(value)

    return value


# ==========================================================
# FILTRO DE CLAVES IRRELEVANTES
# ==========================================================

def is_relevant_technical_key(key: str) -> bool:
    """
    Filtra campos que no deben ir en ficha técnica.
    """

    irrelevant_keywords = [
        "opinión",
        "ranking",
        "clasificación",
        "amazon",
        "desde",
        "descatalogado",
        "asin",
        "upc",
        "más vendidos",
        "estrellas",
        "fabricante",
        "modelo",
        "número de modelo"
    ]

    key_lower = key.lower()

    for word in irrelevant_keywords:
        if word in key_lower:
            return False

    return True


# ==========================================================
# NORMALIZADOR SEMÁNTICO DE CLAVES
# ==========================================================

def normalize_semantic_key(key: str) -> str:
    """
    Agrupa claves similares bajo una categoría común
    para evitar duplicados semánticos.
    """

    key_lower = key.lower()

    if "resolución" in key_lower:
        return "Resolución máxima"

    if "tamaño" in key_lower:
        return "Tamaño de papel"

    if "memoria" in key_lower:
        return "Memoria"

    if "batería" in key_lower or "potencia" in key_lower:
        return "Capacidad batería"

    if "dimensiones" in key_lower:
        return "Dimensiones"

    return key


# ==========================================================
# FUNCIÓN PRINCIPAL DE LIMPIEZA INDIVIDUAL
# ==========================================================

def clean_technical_field(key: str, value: str) -> tuple:
    """
    Devuelve (key_limpio, value_limpio)
    No depende de categoría.
    """

    key_clean = clean_key(key)
    value_clean = clean_value(value)

    return key_clean, value_clean


# ==========================================================
# FUNCIÓN NUEVA: LIMPIEZA GLOBAL DE LISTA TÉCNICA
# ==========================================================

def clean_technical_collection(technical_items: list) -> dict:
    """
    Recibe lista de tuplas [(key, value), ...]
    Devuelve diccionario limpio, sin duplicados y sin irrelevantes.
    """

    technical_dict = {}

    for key, value in technical_items:

        if not is_relevant_technical_key(key):
            continue

        key_clean, value_clean = clean_technical_field(key, value)

        semantic_key = normalize_semantic_key(key_clean)

        if semantic_key not in technical_dict:
            technical_dict[semantic_key] = value_clean

    return technical_dict