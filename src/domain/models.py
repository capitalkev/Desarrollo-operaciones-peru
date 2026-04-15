from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Moneda(str, Enum):
    PEN = "PEN"
    USD = "USD"


class Factura(BaseModel):
    numero_documento: str
    deudor_ruc: str
    monto_neto: float = Field(gt=0, description="El monto debe ser mayor a 0")
    moneda: Moneda
    fecha_emision: datetime
    fecha_vencimiento: datetime

    @field_validator("fecha_vencimiento")
    def vencimiento_posterior_emision(cls, v, values):
        if "fecha_emision" in values.data and v <= values.data["fecha_emision"]:
            raise ValueError("La fecha de vencimiento debe ser posterior a la emisión")
        return v


class Operacion(BaseModel):
    codigo_operacion: str
    cliente_ruc: str
    facturas: list[Factura]
    tasa_operacion: float
    comision: float

    def calcular_monto_total(self) -> float:
        """Aquí vive la regla de negocio, ¡no en el router ni en el caso de uso!"""
        return sum(factura.monto_neto for factura in self.facturas)
