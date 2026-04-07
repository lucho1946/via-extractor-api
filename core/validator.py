# MODULO - VALIDADOR DE DATOS Y RETORNO DEL JSON ESTRUCTURADO

from pydantic import ValidationError
from datetime import datetime
from core.contract_models import ProductoContrato, Metadata
from core.logger_config import logger 

VERSION_EXTRACTOR = "1.0.0"


def validate_product(data: dict) -> dict:
    """
    Valida el diccionario recibido contra el contrato oficial.
    Siempre retorna un JSON estructurado.
    """

    try:
        # Intentamos construir el modelo oficial
        producto = ProductoContrato(**data)

        logger.info("Validacion exitosa del contrato.")

        # Retornamos como diccionario limpio
        return producto.model_dump()

    except ValidationError as e:
        logger.error("Error de validacion del contrato.")
        logger.error(str(e))

        # ==============================
        # RESPUESTA FALLIDA CONTROLADA
        # ==============================

        failed_response = {
            "referencia": data.get("referencia"),
            "marca": data.get("marca"),
            "costo": data.get("costo"),
            "moneda": data.get("moneda"),
            "peso": data.get("peso"),
            "origen": data.get("origen"),
            "link_proveedor": data.get("link_proveedor"),
            "descripcion_corta": data.get("descripcion_corta"),
            "descripcion_larga": data.get("descripcion_larga"),
            "asin": data.get("asin"),
            "modelo": data.get("modelo"),
            "fecha_extraccion": datetime.utcnow(),
            "metadata": Metadata(
                estado_extraccion="failed",
                tiempo_respuesta_ms=data.get("metadata", {}).get("tiempo_respuesta_ms", 0),
                version_extractor=VERSION_EXTRACTOR
            ).model_dump()  # ⚠️ IMPORTANTE: aquí sí se ejecuta el método
        }

        return failed_response