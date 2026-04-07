# ==========================================================
# MAIN - ORQUESTADOR PRINCIPAL DEL EXTRACTOR
# ==========================================================
# Nuevo flujo:
# Extractor → Cleaner → Return limpio
# La estructura final la hará la IA después
# ==========================================================

import sys
import time
from datetime import datetime, timezone
from input.input_handler import validate_input_url
from providers.resolver import resolve_provider
from providers.amazon.extractor import extract_product
from normalizer.product_cleaner import clean_raw_product
from core.logger_config import logger


# ==========================================================
# PIPELINE PURO (SIN PRINTS)
# ==========================================================

def run_pipeline(url: str) -> dict:
    """
    Ejecuta el flujo completo:
    1. Validación
    2. Resolución proveedor
    3. Extracción
    4. Limpieza ligera
    5. Retorna datos limpios (sin estructurar)
    """

    start_time = time.time()

    # ------------------------------------------------------
    # VALIDAR URL
    # ------------------------------------------------------

    validation = validate_input_url(url)
    if not validation["is_valid"]:
        raise ValueError("URL inválida")

    # ------------------------------------------------------
    # RESOLVER PROVEEDOR
    # ------------------------------------------------------

    provider_info = resolve_provider(url)
    if not provider_info["is_supported"]:
        raise ValueError("Proveedor no soportado")

    # ------------------------------------------------------
    # EXTRAER DATOS CRUDOS
    # ------------------------------------------------------

    raw_data = extract_product(url)
    raw_data["fecha_extraccion"] = datetime.now(timezone.utc)

    # ------------------------------------------------------
    #LIMPIEZA LIGERA (SIN ESTRUCTURA)
    # ------------------------------------------------------

    cleaned_data = clean_raw_product(raw_data)

    # ------------------------------------------------------
    # METADATA BÁSICA
    # ------------------------------------------------------

    end_time = time.time()
    response_time = int((end_time - start_time) * 1000)

    cleaned_data["metadata"] = {
        "estado_extraccion": "success",
        "tiempo_respuesta_ms": response_time,
        "version_extractor": "3.0.0-clean"
    }

    logger.info("Pipeline limpio completado correctamente.")

    return cleaned_data


# ==========================================================
# FUNCIÓN MAIN (SOLO CLI)
# ==========================================================

def main(url: str):
    """
    Versión CLI para pruebas locales.
    Muestra datos limpios en consola.
    """

    try:
        result = run_pipeline(url)

        print("\n========================================")
        print("DATOS LIMPIOS (SIN ESTRUCTURA IA)")
        print("========================================\n")

        for key, value in result.items():
            print(f"{key}: {value}\n")

    except Exception as e:
        print(f"\nERROR: {str(e)}\n")


# ==========================================================
# EJECUCIÓN LOCAL
# ==========================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_url = sys.argv[1].strip()
    else:
        test_url = input("Ingresa la URL del producto Amazon: ").strip()

    main(test_url)