# MODULO - DEFINE LA ESTRUCTURA OFICIAL DEL JSON DE SALIDA

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class Metadata(BaseModel):
    estado_extraccion: str = Field(
        ...,
        description="Estado final del proceso: success | partial | failed"
    )
    tiempo_respuesta_ms: int = Field(
        ...,
        description="Tiempo total de extraccion en milisegundos"
    )
    version_extractor: str = Field(
        ...,
        description="Version del extractor siguiendo Semantic Versioning"
    )


class ProductoContrato(BaseModel):
    """
    Nuevo contrato estructurado en columnas
    alineado con el modelo VIA.
    """

    # ===============================
    # CAMPOS OBLIGATORIOS
    # ===============================

    referencia: str = Field(
        ...,
        description="Referencia unica del producto (modelo o codigo principal)"
    )

    marca: str = Field(
        ...,
        description="Marca oficial del producto"
    )

    # ===============================
    # CAMPOS ECONOMICOS
    # ===============================

    costo: Optional[float] = Field(
        default=None,
        description="Valor numerico del producto"
    )

    moneda: Optional[str] = Field(
        default=None,
        description="Codigo de moneda ISO 4217 (USD, EUR, etc)"
    )

    # ===============================
    # CAMPOS LOGISTICOS
    # ===============================

    peso: Optional[str] = Field(
        default=None,
        description="Peso del producto segun proveedor"
    )

    origen: Optional[str] = Field(
        default=None,
        description="Origen del producto (Importado / Nacional)"
    )

    # ===============================
    # INFORMACION GENERAL
    # ===============================

    link_proveedor: Optional[HttpUrl] = Field(
        default=None,
        description="URL original del producto en el proveedor"
    )

    descripcion_corta: Optional[str] = None
    descripcion_larga: Optional[str] = None

    asin: Optional[str] = None
    modelo: Optional[str] = None

    # ===============================
    # METADATA SISTEMA
    # ===============================

    fecha_extraccion: datetime = Field(
        ...,
        description="Fecha de extraccion en formato ISO 8601"
    )

    metadata: Metadata