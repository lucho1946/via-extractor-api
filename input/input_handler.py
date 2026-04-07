#MODULO - VERIFICACION TOTAL DEL FORMATO Y VALIDACION DEL CONTRATO

from urllib.parse import urlparse
from core.logger_config import logger


ALLOWED_DOMAINS = ["amazon.com", "amazon.es", "amazon.com.co"]


def validate_input_url(url: str) -> dict:
    """
    Valida que la URL tenga formato correcto
    y que el dominio esté permitido.
    Retorna un diccionario con el resultado.
    """

    if not url:
        logger.warning("URL vacía recibida.")
        return {
            "is_valid": False,
            "error": "URL vacía"
        }

    try:
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            logger.warning("URL con formato inválido.")
            return {
                "is_valid": False,
                "error": "Formato de URL inválido"
            }

        domain = parsed.netloc.lower()

        if not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.warning(f"Dominio no permitido: {domain}")
            return {
                "is_valid": False,
                "error": "Dominio no permitido"
            }

        logger.info("URL válida y dominio permitido.")
        return {
            "is_valid": True,
            "error": None
        }

    except Exception as e:
        logger.error("Error inesperado validando URL.")
        logger.error(str(e))
        return {
            "is_valid": False,
            "error": "Error inesperado en validación"
        }
