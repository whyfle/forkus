from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from .models import Producto
from .schemas.producto import ProductoCreate, ProductoResponse

from .models import Venta, DetalleVenta
from .schemas.venta import VentaCreate
from .schemas.venta import VentaResponse

from .models import Categoria
from .schemas.categoria import CategoriaCreate, CategoriaResponse

from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from .models import MovimientoStock
from .schemas.stock import IngresoStockCreate

from sqlalchemy import or_

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import Depends

from sqlalchemy import func, or_
from fastapi import HTTPException

from .models import Cliente
from .schemas.cliente import ClienteCreate, ClienteResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import Venta

from .models import Configuracion
from .schemas.configuracion import (
    ConfiguracionResponse,
    ConfiguracionUpdate )


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Stock y Ventas")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#@app.get("/")
#def root():
#    return {"mensaje": "Sistema de Stock funcionando 🚀"}


#"@app.post("/productos", response_model=ProductoResponse)
#def crear_producto(
#   producto: ProductoCreate,
#   db: Session = Depends(get_db),
#):
#   nuevo_producto = Producto(
#       nombre=producto.nombre,
#       precio_venta=producto.precio_venta,
#       stock=producto.stock,
#   )
#   db.add(nuevo_producto)
#   db.commit()
#   db.refresh(nuevo_producto)
#   return nuevo_producto



from sqlalchemy import func
from fastapi import Depends
from sqlalchemy.orm import Session

@app.post("/productos", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    """
    Genera código de producto con formato:
    100001 .. 100999
    """

    # 1️⃣ Obtener el último código generado
    ultimo_codigo = (
        db.query(func.max(Producto.codigo))
        .filter(Producto.codigo.like("100%"))
        .scalar()
    )

    # 2️⃣ Calcular siguiente secuencia
    if ultimo_codigo:
        secuencia = int(ultimo_codigo[-3:]) + 1
    else:
        secuencia = 1

    # 3️⃣ Validación simple de límite (MVP)
    if secuencia > 999:
        raise ValueError("Límite máximo de productos alcanzado (999)")

    # 4️⃣ Construir código
    codigo = f"100{secuencia:03d}"

    # 5️⃣ Crear producto (activo por defecto)
    nuevo = Producto(
        codigo=codigo,
        nombre=producto.nombre,
        precio_venta=producto.precio_venta,
        stock=producto.stock,
        categoria_id=producto.categoria_id,
        activo=True
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


@app.get("/productos", response_model=list[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    return (
        db.query(Producto)
        .options(joinedload(Producto.categoria))
        .filter(Producto.activo == True)
        .all()
    )

@app.get("/web", response_class=HTMLResponse)
def web():
    with open("app/static/index.html", encoding="utf-8") as f:
        return f.read()
    
@app.post("/ventas")
def crear_venta(venta: VentaCreate, db: Session = Depends(get_db)):
    # 1️⃣ Validar cliente
    cliente = db.query(Cliente).filter(
        Cliente.id == venta.cliente_id,
        Cliente.activo == True
    ).first()

    if not cliente:
        raise HTTPException(status_code=400, detail="Cliente inválido o inactivo")

    total = 0
    detalles_db = []

    # 2️⃣ Validar productos y stock
    for item in venta.detalles:
        producto = db.query(Producto).filter(
            Producto.id == item.producto_id,
            Producto.activo == True
        ).first()

        if not producto:
            raise HTTPException(
                status_code=400,
                detail=f"Producto {item.producto_id} inválido o inactivo"
            )

        if item.cantidad > producto.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}"
            )

        subtotal = producto.precio_venta * item.cantidad
        total += subtotal

        detalles_db.append(
            DetalleVenta(
                producto_id=producto.id,
                cantidad=item.cantidad,
                precio_unitario=producto.precio_venta
            )
        )

    # 3️⃣ Crear venta
    nueva_venta = Venta(
        cliente_id=cliente.id,
        total=total
    )

    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)

    # 4️⃣ Guardar detalles + descontar stock
    for detalle in detalles_db:
        detalle.venta_id = nueva_venta.id

        producto = db.query(Producto).filter(
            Producto.id == detalle.producto_id
        ).first()

        producto.stock -= detalle.cantidad

        db.add(detalle)

    db.commit()

    return {
        "venta_id": nueva_venta.id,
        "cliente": cliente.nombre_razon_social,
        "total": total
    } 
       
@app.get("/ventas-web", response_class=HTMLResponse)    
def ventas_web():
    with open("app/static/ventas.html", encoding="utf-8") as f:
        return f.read()

@app.get("/ventas", response_model=list[VentaResponse])
def listar_ventas(db: Session = Depends(get_db)):
    return (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles)
            .joinedload(DetalleVenta.producto)
            .joinedload(Producto.categoria)
        )
        .all()
    )

@app.get("/historial-web", response_class=HTMLResponse)
def historial_web():
    with open("app/static/historial.html", encoding="utf-8") as f:
        return f.read()
    
@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/static/home.html", encoding="utf-8") as f:
        return f.read()    


@app.post("/categorias", response_model=CategoriaResponse)
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    nueva = Categoria(nombre=categoria.nombre)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@app.get("/categorias", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).filter(Categoria.activa == True).all()

@app.get("/configuracion", response_class=HTMLResponse)
def configuracion():
    with open("app/static/configuracion.html", encoding="utf-8") as f:
        return f.read()    
    
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.activo == True
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto.activo = False
    db.commit()

    return {"mensaje": "Producto eliminado"}


from fastapi import HTTPException

@app.patch("/productos/{producto_id}/desactivar")
def desactivar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto.activo = False
    db.commit()

    return {"mensaje": "Producto desactivado"}


@app.patch("/productos/{producto_id}/activar")
def activar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    producto.activo = True
    db.commit()

    return {"mensaje": "Producto activado"}

@app.get("/productos-admin", response_model=list[ProductoResponse])
def listar_productos_admin(db: Session = Depends(get_db)):
    return (
        db.query(Producto)
        .options(joinedload(Producto.categoria))
        .all()
    )
    
@app.post("/stock/ingreso")
def ingresar_stock(data: IngresoStockCreate, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(
        Producto.id == data.producto_id,
        Producto.activo == True
    ).first()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no válido")

    # Registrar movimiento
    movimiento = MovimientoStock(
        producto_id=producto.id,
        tipo="INGRESO",
        cantidad=data.cantidad,
        motivo=data.motivo
    )
    db.add(movimiento)

    # Actualizar stock derivado
    producto.stock += data.cantidad

    db.commit()

    return {
        "mensaje": "Stock ingresado",
        "producto": producto.nombre,
        "nuevo_stock": producto.stock
    }
    
@app.get("/stock-web", response_class=HTMLResponse)
def stock_web():
    with open("app/static/stock.html", encoding="utf-8") as f:
        return f.read()    
    


@app.get("/productos/buscar")
def buscar_productos(q: str, db: Session = Depends(get_db)):
    q = q.strip()
    if len(q) < 2:
        return []

    productos = (
        db.query(Producto)
        .filter(
            or_(
                Producto.nombre.ilike(f"%{q}%"),
                Producto.codigo.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

    return [
        {
            "id": p.id,
            "codigo": p.codigo,
            "nombre": p.nombre,
            "precio": p.precio_venta,
            "stock": p.stock,
            "activo": p.activo
        }
        for p in productos
    ]
    
@app.post("/clientes", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):

    # Validaciones por tipo
    if cliente.tipo_cliente == "EMPRESA":
        if not cliente.codigo_fiscal:
            raise HTTPException(status_code=400, detail="Código fiscal obligatorio para Empresa")
        prefijo = "200"

    elif cliente.tipo_cliente == "PERSONA":
        prefijo = "300"

    else:
        raise HTTPException(status_code=400, detail="Tipo de cliente inválido")

    # Obtener último código del tipo
    ultimo_codigo = (
        db.query(func.max(Cliente.codigo_cliente))
        .filter(Cliente.codigo_cliente.like(f"{prefijo}%"))
        .scalar()
    )

    if ultimo_codigo:
        secuencia = int(ultimo_codigo[-3:]) + 1
    else:
        secuencia = 1

    if secuencia > 999:
        raise HTTPException(status_code=400, detail="Límite de clientes alcanzado")

    codigo_cliente = f"{prefijo}{secuencia:03d}"

    nuevo = Cliente(
        codigo_cliente=codigo_cliente,
        tipo_cliente=cliente.tipo_cliente,
        nombre_razon_social=cliente.nombre_razon_social,
        telefono=cliente.telefono,
        calle=cliente.calle,
        numero=cliente.numero,
        localidad=cliente.localidad,
        codigo_postal=cliente.codigo_postal,
        codigo_fiscal=cliente.codigo_fiscal,
        dni=cliente.dni,
        activo=True
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo

@app.get("/clientes/buscar", response_model=list[ClienteResponse])
def buscar_clientes(q: str, db: Session = Depends(get_db)):
    q = q.strip()
    if len(q) < 2:
        return []

    return (
        db.query(Cliente)
        .filter(
            Cliente.activo == True,
            or_(
                Cliente.codigo_cliente.ilike(f"%{q}%"),
                Cliente.nombre_razon_social.ilike(f"%{q}%")
            )
        )
        .limit(10)
        .all()
    )

from fastapi.responses import HTMLResponse

@app.get("/clientes-web", response_class=HTMLResponse)
def clientes_web():
    with open("app/static/clientes.html", encoding="utf-8") as f:
        return f.read()
    
@app.get("/clientes", response_model=list[ClienteResponse])
def listar_clientes(db: Session = Depends(get_db)):
    return (
        db.query(Cliente)
        .filter(Cliente.activo == True)
        .order_by(Cliente.codigo_cliente)
        .all()
    )    
    
@app.get("/api/configuracion", response_model=ConfiguracionResponse)
def obtener_configuracion(db: Session = Depends(get_db)):

    config = db.query(Configuracion).first()

    if not config:
        config = Configuracion(
            max_precio_producto=9999.99,
            max_stock_producto=10000
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


@app.put("/api/configuracion", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    data: ConfiguracionUpdate,
    db: Session = Depends(get_db)):
    
    config = db.query(Configuracion).first()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Configuración no encontrada"
        )

    config.max_precio_producto = data.max_precio_producto
    config.max_stock_producto = data.max_stock_producto

    db.commit()
    db.refresh(config)

    return config