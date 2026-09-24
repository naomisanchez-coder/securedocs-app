from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)  # ADMINISTRADOR, GERENTE, SUPERVISOR, EMPLEADO, AUDITOR, INVITADO

    permisos = relationship("RolPermiso", back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)  # CREAR, CONSULTAR, MODIFICAR, ELIMINAR, APROBAR, VER_AUDITORIA, GESTIONAR_USUARIOS, ASIGNAR_ROLES


class RolPermiso(Base):
    __tablename__ = "rol_permisos"

    id = Column(Integer, primary_key=True, index=True)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permiso_id = Column(Integer, ForeignKey("permisos.id", ondelete="CASCADE"), nullable=False)

    rol = relationship("Rol", back_populates="permisos")
    permiso = relationship("Permiso")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Atributos ABAC / Rol
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=True)
    nivel_seguridad = Column(Integer, default=1)  # 1 a 5
    pais = Column(String(50), default="PERU")
    tipo_contrato = Column(String(50), default="INTERNO")  # INTERNO, EXTERNO
    estado = Column(String(20), default="ACTIVO")  # ACTIVO, INACTIVO, SUSPENDIDO

    rol = relationship("Rol")
    departamento = relationship("Departamento")


class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)

    # Atributos ABAC
    propietario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=False)
    nivel_confidencialidad = Column(Integer, default=1)  # 1 a 5
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE, APROBADO, PUBLICADO
    pais = Column(String(50), default="PERU")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    propietario = relationship("Usuario")
    departamento = relationship("Departamento")


class RegistroAuditoria(Base):
    __tablename__ = "auditorias"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(100), nullable=False)
    recurso = Column(String(100), nullable=False)
    accion = Column(String(50), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    resultado = Column(String(20), nullable=False)  # PERMITIDO, DENEGADO
    motivo = Column(Text, nullable=False)