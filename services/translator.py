"""
Capa profesional de traducción
Esta capa traduce únicamente textos descriptivos
sin alterar estructura del contrato.
"""

from deep_translator import GoogleTranslator
from core.logger_config import logger


def safe_translate(text: str, target_lang: str = "es") -> str:
    """
    Traduce texto de forma segura.
    Si falla la traducción, devuelve el texto original.
    """
    try:
        if not text or not isinstance(text, str):
            return text

        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return translated

    except Exception as e:
        logger.warning(f"Error en traducción: {e}")
        return text


def translate_product(normalized_data: dict) -> dict:
    """
    Traduce campos descriptivos del producto
    manteniendo la estructura original.
    """

    logger.info("Iniciando capa de traducción.")

    # ==============================
    # TRADUCIR DESCRIPCIÓN CORTA
    # ==============================
    normalized_data["descripcion_corta"] = safe_translate(
        normalized_data.get("descripcion_corta")
    )

    # ==============================
    # TRADUCIR DESCRIPCIÓN LARGA
    # ==============================
    descripcion_larga = normalized_data.get("descripcion_larga", "")

    if descripcion_larga:
        normalized_data["descripcion_larga"] = safe_translate(descripcion_larga)

    logger.info("Traducción completada.")

    return normalized_data
    