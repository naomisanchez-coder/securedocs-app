from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


# Esquemas de Autenticación
class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Esquema para Atributos del Usuario (ABAC + RBAC)
class UsuarioSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: EmailStr
    rol: str
    departamento: Optional[str] = None
    nivel_seguridad: int
    pais: str
    tipo_contrato: str
    estado: str


# Esquema para Atributos del Recurso / Documento (ABAC)
class DocumentoCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    departamento_id: int
    nivel_confidencialidad: int
    pais: str = "PERU"


class DocumentoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descripcion: Optional[str] = None
    propietario_id: int
    departamento: str
    nivel_confidencialidad: int
    estado: str
    pais: str
    fecha_creacion: datetime


# Contexto de Entorno (Entorno ABAC)
class ContextoEntorno(BaseModel):
    hora: str
    fecha: str
    direccion_ip: str
    ubicacion: str
    dispositivo: str