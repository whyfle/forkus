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

from .models import Usuario
from .schemas.usuario import UsuarioCreate, UsuarioUpdate, Usuario, LoginRequest, Token

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

from fastapi.middleware.cors import CORSMiddleware

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
from typing import Optional

SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from .models import Usuario, Producto, Venta, DetalleVenta, Categoria, MovimientoStock, Cliente, Configuracion
from .schemas.usuario import UsuarioCreate, Usuario, LoginRequest, Token

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Stock y Ventas")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    print(f"Authenticating user: {username}")
    print(f"Usuario class: {Usuario}")
    user = db.query(Usuario).filter(Usuario.username == username).first()
    print(f"User found: {user is not None}")
    if not user:
        print("User not found")
        return False
    if not verify_password(password, user.password_hash):
        print("Password verification failed")
        return False
    print("Authentication successful")
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: Usuario = Depends(get_current_user)):
    if not current_user.activo:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Initialize default admin user
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        from .models import Usuario as UsuarioModel
        admin = db.query(UsuarioModel).filter(UsuarioModel.username == "admin").first()
        if not admin:
            hashed_password = get_password_hash("FORKUS")
            admin_user = UsuarioModel(username="admin", password_hash=hashed_password, role="admin")
            db.add(admin_user)
            db.commit()
        elif not verify_password("FORKUS", admin.password_hash):
            admin.password_hash = get_password_hash("FORKUS")
            db.commit()
    finally:
        db.close()


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login-json", response_model=Token)
def login_json(credentials: LoginRequest, db: Session = Depends(get_db)):
    print(f"Login attempt for user: {credentials.username}")
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background: #f4f5f8; color: #111; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .login-form { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 300px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
            button { width: 100%; padding: 10px; background: #2f78f6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #3a8dff; }
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>Login</h2>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Username" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const response = await fetch('/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ username, password })
                });
                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('token', data.access_token);
                    window.location.href = '/';
                } else {
                    alert('Invalid credentials');
                }
            });
        </script>
    </body>
    </html>
    """


@app.get("/users/me", response_model=Usuario)
def read_users_me(current_user: Usuario = Depends(get_current_active_user)):
    return current_user


@app.post("/users", response_model=Usuario)
def create_user(user: UsuarioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    hashed_password = get_password_hash(user.password)
    db_user = Usuario(username=user.username, password_hash=hashed_password, role=user.role, activo=user.activo)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users", response_model=list[Usuario])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    users = db.query(Usuario).offset(skip).limit(limit).all()
    return users


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
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def listar_productos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def crear_venta(venta: VentaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def listar_ventas(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    nueva = Categoria(nombre=categoria.nombre)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@app.get("/categorias", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    return db.query(Categoria).filter(Categoria.activa == True).all()

@app.delete("/categorias/{categoria_id}")
def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    categoria = db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.activa == True
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Check if category has products
    productos_count = db.query(Producto).filter(
        Producto.categoria_id == categoria_id,
        Producto.activo == True
    ).count()

    if productos_count > 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar la categoría porque tiene productos asociados"
        )

    categoria.activa = False
    db.commit()

    return {"mensaje": "Categoría eliminada"}

@app.get("/configuracion", response_class=HTMLResponse)
def configuracion():
    with open("app/static/configuracion.html", encoding="utf-8") as f:
        return f.read()    
    
@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def listar_productos_admin(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    return (
        db.query(Producto)
        .options(joinedload(Producto.categoria))
        .all()
    )
    
@app.post("/stock/ingreso")
def ingresar_stock(data: IngresoStockCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def buscar_productos(q: str, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):

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
def buscar_clientes(q: str, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
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
def listar_clientes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    return (
        db.query(Cliente)
        .filter(Cliente.activo == True)
        .order_by(Cliente.codigo_cliente)
        .all()
    )    
    
@app.get("/api/configuracion", response_model=ConfiguracionResponse)
def obtener_configuracion(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):

    config = db.query(Configuracion).first()

    if not config:
        config = Configuracion(
            max_precio_producto=9999.99,
            max_stock_producto=10000,
            idioma="es"
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config


@app.put("/api/configuracion", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    data: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)):
    
    config = db.query(Configuracion).first()

    if not config:
        raise HTTPException(
            status_code=404,
            detail="Configuración no encontrada"
        )

    config.max_precio_producto = data.max_precio_producto
    config.max_stock_producto = data.max_stock_producto
    config.idioma = data.idioma
    config.tema = data.tema

    db.commit()
    db.refresh(config)

    return config


@app.get("/api/stats")
def obtener_stats(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_user)):
    productos = db.query(func.count(Producto.id)).filter(Producto.activo == True).scalar()
    categorias = db.query(func.count(Categoria.id)).filter(Categoria.activa == True).scalar()
    ventas = db.query(func.count(Venta.id)).scalar()
    stock_total = db.query(func.sum(Producto.stock)).scalar() or 0
    clientes = db.query(func.count(Cliente.id)).filter(Cliente.activo == True).scalar()
    
    return {
        "productos": productos,
        "categorias": categorias,
        "ventas": ventas,
        "stock_total": stock_total,
        "clientes": clientes
    }