# MODULO - DETECTAR PROVEEDOR POR DOMINIO 

from urllib.parse import urlparse
from core.logger_config import logger

import re
from core.logger_config import logger


def resolver_referencia(technical_details: dict, url: str) -> str | None:
    """
    Resuelve la referencia según reglas oficiales del negocio:

    Referencia del fabricante
    Número de modelo
    ASIN en tabla técnica
    ASIN desde URL (fallback)
    """

    if not technical_details:
        technical_details = {}

    #Referencia fabricante
    claves_fabricante = [
        "Manufacturer Part Number",
        "Número de pieza del fabricante",
        "Part Number",
        "Referencia del fabricante"
    ]

    for key, value in technical_details.items():
        if key in claves_fabricante and value:
            logger.info(f"Referencia encontrada (fabricante): {value}")
            return value.strip()

    #Número de modelo
    claves_modelo = [
        "Model Number",
        "Número de modelo",
        "Número de modelo del producto",
        "Item model number"
    ]

    for key, value in technical_details.items():
        if key in claves_modelo and value:
            logger.info(f"Referencia encontrada (modelo): {value}")
            return value.strip()

    # ASIN tabla
    asin = technical_details.get("ASIN")
    if asin:
        logger.info(f"Referencia encontrada (ASIN tabla): {asin}")
        return asin.strip()

    # ASIN URL fallback
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if match:
        asin_url = match.group(1)
        logger.info(f"Referencia encontrada (ASIN URL fallback): {asin_url}")
        return asin_url

    logger.warning("No se encontró referencia válida.")
    return None


def resolve_provider(url: str) -> dict:
    """
    Determina el proveedor basado en el dominio de la URL.
    Retorna estructura controlada.
    """
    try: 
        domain = urlparse(url).netloc.lower()
        
        if "amazon" in domain:
            logger.info("Proveedor detectado: Amazon")
            return{
                "provider": "Amazon",
                "is_supported": True
            }
            
        logger.warning(f"Proveedor no soportado: {domain}")
        return{
            "provider":None,
            "is_supported": None
        }
        
    except Exception as e:
        logger.error("Error resolviendo proveedor.")
        logger.error(str(e))
        return{
            "provider": None,
            "is_supported": False 
        }
        