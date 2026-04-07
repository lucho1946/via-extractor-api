# ==========================================================
# FORMATEADOR DE SALIDA PARA VIA
# Capa de Presentación (No altera datos)
# ==========================================================

from datetime import datetime


# ==========================================================
# FUNCION EXISTENTE (SE MANTIENE)
# ==========================================================

def build_via_output(product: dict) -> str:
    """
    Construye un texto formateado listo para debug o consola.
    No modifica datos. Solo organiza presentación.
    """

    referencia = product.get("referencia", "")
    marca = product.get("marca", "")
    costo = product.get("costo", "")
    moneda = product.get("moneda", "")
    peso = product.get("peso", "")
    origen = product.get("origen", "")
    descripcion_corta = product.get("descripcion_corta", "")
    descripcion_larga = product.get("descripcion_larga", "")
    link = product.get("link_proveedor", "")
    fecha = product.get("fecha_extraccion", "")

    if isinstance(fecha, datetime):
        fecha = fecha.isoformat()

    output = f"""
========================================
PRODUCTO LISTO PARA VIA
========================================

Referencia: {referencia}
Marca: {marca}

Precio: {costo}
Moneda: {moneda}
Peso: {peso}
Origen: {origen}

----------------------------------------
DESCRIPCIÓN CORTA
----------------------------------------
{descripcion_corta}

----------------------------------------
DESCRIPCIÓN LARGA
----------------------------------------
{descripcion_larga}

----------------------------------------
METADATOS
----------------------------------------
URL Origen: {link}
Fecha Extracción: {fecha}

========================================
"""

    return output.strip()


# ==========================================================
# NUEVO: NORMALIZADOR DE BULLETS
# ==========================================================

def format_list(items):
    """
    Convierte listas en bullets consistentes
    """
    if not items:
        return ""

    lines = []

    for item in items:
        item = str(item).strip()

        # limpiar posibles formatos previos
        item = item.lstrip("-").lstrip("•").strip()

        if item:
            lines.append(f"• {item}")

    return "\n".join(lines)


# ==========================================================
# NUEVO: CONSTRUCTOR DE DESCRIPCIÓN PARA VIA
# ==========================================================

def build_via_description(ai_data: dict) -> str:
    """
    Construye la descripción larga estándar para VIA.

    IMPORTANTE:
    - NO depende de la IA para estructura
    - Garantiza consistencia visual
    """

    if not ai_data:
        return ""

    descripcion_general = ai_data.get("descripcion_general", "")
    ventajas = ai_data.get("ventajas", [])
    aplicaciones = ai_data.get("aplicaciones", [])
    tecnica = ai_data.get("tecnica", [])

    descripcion = f"""
DESCRIPCIÓN GENERAL
{descripcion_general}

VENTAJAS PRINCIPALES
{format_list(ventajas)}

APLICACIONES
{format_list(aplicaciones)}

CARACTERÍSTICAS TÉCNICAS
{format_list(tecnica)}
"""

    return descripcion.strip()