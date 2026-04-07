"""
LOGGER CONFIGURATION
Extractor Empresarial - VIA Industrial

- Logging estructurado
- Soporte UTF-8 (archivo y consola)
- Rotación automática de logs
- Prevención de duplicación de handlers
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# ======================================================
# CONFIGURACIÓN BASE
# ======================================================

LOG_DIR = "logs"
LOG_FILE = "extractor.log"

# Crear carpeta de logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

# Crear logger principal
logger = logging.getLogger("extractor_logger")
logger.setLevel(logging.INFO)

# Evitar que los logs se propaguen al root logger
logger.propagate = False

# ======================================================
# EVITAR DUPLICACIÓN DE HANDLERS
# ======================================================

if not logger.handlers:

    # ==================================================
    # FORMATO ESTÁNDAR CORPORATIVO
    # ==================================================

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # ==================================================
    # HANDLER DE ARCHIVO (UTF-8 + ROTACIÓN)
    # ==================================================

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        maxBytes=5 * 1024 * 1024,   # 5 MB por archivo
        backupCount=5,             # Mantener últimos 5 archivos
        encoding="utf-8"           # 🔴 CRÍTICO: evita errores Unicode
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # ==================================================
    # HANDLER DE CONSOLA (FORZANDO UTF-8)
    # ==================================================

    # Forzar UTF-8 en consola (evita cp1252 en Windows)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass  # Si no es compatible, continúa sin romper ejecución

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # ==================================================
    # AGREGAR HANDLERS
    # ==================================================

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)