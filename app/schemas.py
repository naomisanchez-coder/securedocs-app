from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# Esquemas de Autenticación
class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Esquema para Atributos del Usuario (ABAC + RBAC)
class UsuarioSchema(BaseModel):
    id: int
    nombre: str
    correo: EmailStr
    rol: str
    departamento: Optional[str] = None
    nivel_seguridad: int
    pais: str
    tipo_contrato: str
    estado: str

    class Config:
        from_attributes = True


# Esquema para Atributos del Recurso / Documento (ABAC)
class DocumentoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    departamento_id: int
    nivel_confidencialidad: int  # 1 a 5
    pais: str = "PERU"


class DocumentoSchema(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str] = None
    propietario_id: int
    departamento: str
    nivel_confidencialidad: int
    estado: str
    pais: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# Contexto de Entorno (Entorno ABAC)
class ContextoEntorno(BaseModel):
    hora: str  # Formato "HH:MM"
    fecha: str
    direccion_ip: str
    ubicacion: str  # Ej: "PERU"
    dispositivo: str  # Ej: "CORPORATIVO", "PERSONAL"