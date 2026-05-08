from pydantic import BaseModel
from typing import Optional

class UsuarioBase(BaseModel):
    username: str
    role: Optional[str] = "user"
    activo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None

class Usuario(UsuarioBase):
    id: int

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str