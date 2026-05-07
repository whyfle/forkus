from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .producto import ProductoMini

class DetalleVentaCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)


class VentaCreate(BaseModel):
    cliente_id: int
    detalles: List[DetalleVentaCreate]
    
class DetalleVentaResponse(BaseModel):
    producto_id: int
    cantidad: int
    precio_unitario: float
    producto: ProductoMini

    class Config:
        from_attributes = True


class VentaResponse(BaseModel):
    id: int
    fecha: datetime
    total: float
    detalles: list[DetalleVentaResponse]

class Config:
    from_attributes = True
    