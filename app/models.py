from sqlalchemy import Column, Integer, String, Float, Boolean
from .database import Base
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import String

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True, nullable=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    precio_venta = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    categoria = relationship("Categoria", back_populates="productos")
    


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, nullable=False)

    detalles = relationship("DetalleVenta", back_populates="venta")    

class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"

    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    producto = relationship("Producto")

    venta = relationship("Venta", back_populates="detalles")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    activa = Column(Boolean, default=True)

    productos = relationship("Producto", back_populates="categoria")


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    tipo = Column(String, nullable=False)  # INGRESO / EGRESO
    cantidad = Column(Integer, nullable=False)
    motivo = Column(String, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto")


class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True, index=True)
    max_precio_producto = Column(Float, default=9999.99)
    max_stock_producto = Column(Integer, default=10000)
    idioma = Column(String, default="es")
