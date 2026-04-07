# ==========================================================
# CONFIGURACIÓN CENTRAL DEL SISTEMA
# ==========================================================

import os

# ==========================================================
# SETTINGS
# ==========================================================

class Settings:
    """
    Clase centralizada de variables de entorno
    """

    def __init__(self):
        self.SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.VIA_API_KEY = os.getenv("VIA_API_KEY")


# Instancia global
settings = Settings()


# ==========================================================
# VALIDACIÓN DE VARIABLES CRÍTICAS
# ==========================================================

def validate_settings():
    """
    Valida que las variables críticas existan
    """

    missing = []

    if not settings.SCRAPER_API_KEY:
        missing.append("SCRAPER_API_KEY")

    if not settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")

    if missing:
        raise RuntimeError(
            f"Variables de entorno faltantes: {', '.join(missing)}"
        )