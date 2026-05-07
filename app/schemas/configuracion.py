from pydantic import BaseModel


class ConfiguracionResponse(BaseModel):
    max_precio_producto: float
    max_stock_producto: int
    idioma: str
    tema: str

    class Config:
        orm_mode = True


class ConfiguracionUpdate(BaseModel):
    max_precio_producto: float
    max_stock_producto: int
    idioma: str
    tema: str
