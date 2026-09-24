from datetime import datetime
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, Request, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_password
from app.authz.engine import AuthorizationEngine
from app.authz.rbac import RBACEngine
from app.database import get_db
from app.models import Departamento, Documento, RegistroAuditoria, Rol, Usuario
from app.schemas import (
    ContextoEntorno,
    DocumentoCreate,
    DocumentoSchema,
    LoginRequest,
    TokenResponse,
    UsuarioSchema,
)

app = FastAPI(
    title="SecureDocs API - RBAC + ABAC",
    description="Sistema de Gestión de Expedientes con Control de Acceso Combinado",
    version="1.0.0",
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper para capturar el entorno ABAC desde cabeceras HTTP o valores por defecto
def obtener_entorno_solicitud(
    request: Request,
    x_hora: Optional[str] = Header(default=None),
    x_ubicacion: Optional[str] = Header(default="PERU"),
    x_dispositivo: Optional[str] = Header(default="CORPORATIVO"),
) -> ContextoEntorno:
    hora_actual = x_hora if x_hora else datetime.now().strftime("%H:%M")
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    ip_cliente = request.client.host if request.client else "127.0.0.1"

    return ContextoEntorno(
        hora=hora_actual,
        fecha=fecha_actual,
        direccion_ip=ip_cliente,
        ubicacion=x_ubicacion,
        dispositivo=x_dispositivo,
    )


# ==========================================
# 1. MÓDULO DE AUTENTICACIÓN
# ==========================================
@app.post("/auth/login", response_model=TokenResponse, tags=["Autenticación"])
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter_by(correo=datos.correo).first()
    if not usuario or not verify_password(datos.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if usuario.estado != "ACTIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo o suspendido",
        )

    token = create_access_token(data={"sub": usuario.correo, "id": usuario.id})
    return {"access_token": token, "token_type": "bearer"}


# ==========================================
# 2. MÓDULO DE USUARIOS
# ==========================================
@app.get("/usuarios", response_model=List[UsuarioSchema], tags=["Usuarios"])
def listar_usuarios(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    # Verificación de RBAC para ver usuarios / administrar
    if not RBACEngine.verificar_permiso(usuario_actual, "GESTIONAR_USUARIOS", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No posee permiso RBAC para consultar usuarios",
        )

    usuarios = db.query(Usuario).all()
    resultado = []
    for u in usuarios:
        resultado.append(
            UsuarioSchema(
                id=u.id,
                nombre=u.nombre,
                correo=u.correo,
                rol=u.rol.nombre,
                departamento=u.departamento.nombre if u.departamento else None,
                nivel_seguridad=u.nivel_seguridad,
                pais=u.pais,
                tipo_contrato=u.tipo_contrato,
                estado=u.estado,
            )
        )
    return resultado


# ==========================================
# 3. MÓDULO DE DOCUMENTOS (RBAC + ABAC)
# ==========================================
@app.post("/documentos", response_model=DocumentoSchema, tags=["Documentos"])
def crear_documento(
    doc: DocumentoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    if not RBACEngine.verificar_permiso(usuario_actual, "CREAR_DOCUMENTO", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado por RBAC: Rol no autorizado para crear documentos",
        )

    nuevo_doc = Documento(
        titulo=doc.titulo,
        descripcion=doc.descripcion,
        propietario_id=usuario_actual.id,
        departamento_id=doc.departamento_id,
        nivel_confidencialidad=doc.nivel_confidencialidad,
        estado="PENDIENTE",
        pais=doc.pais,
    )
    db.add(nuevo_doc)
    db.commit()
    db.refresh(nuevo_doc)

    return DocumentoSchema(
        id=nuevo_doc.id,
        titulo=nuevo_doc.titulo,
        descripcion=nuevo_doc.descripcion,
        propietario_id=nuevo_doc.propietario_id,
        departamento=nuevo_doc.departamento.nombre,
        nivel_confidencialidad=nuevo_doc.nivel_confidencialidad,
        estado=nuevo_doc.estado,
        pais=nuevo_doc.pais,
        fecha_creacion=nuevo_doc.fecha_creacion,
    )


@app.get("/documentos", response_model=List[DocumentoSchema], tags=["Documentos"])
def listar_documentos(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    documentos = db.query(Documento).all()
    resultado = []
    for d in documentos:
        resultado.append(
            DocumentoSchema(
                id=d.id,
                titulo=d.titulo,
                descripcion=d.descripcion,
                propietario_id=d.propietario_id,
                departamento=d.departamento.nombre,
                nivel_confidencialidad=d.nivel_confidencialidad,
                estado=d.estado,
                pais=d.pais,
                fecha_creacion=d.fecha_creacion,
            )
        )
    return resultado


@app.get(
    "/documentos/{documento_id}",
    response_model=DocumentoSchema,
    tags=["Documentos"],
)
def consultar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
    entorno: ContextoEntorno = Depends(obtener_entorno_solicitud),
):
    doc = db.query(Documento).filter_by(id=documento_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
        )

    # Evaluación combinada RBAC + ABAC
    permitido, motivo = AuthorizationEngine.evaluar_solicitud(
        usuario=usuario_actual,
        operacion="CONSULTAR_DOCUMENTO",
        documento=doc,
        entorno=entorno,
        db=db,
    )

    if not permitido:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=motivo)

    return DocumentoSchema(
        id=doc.id,
        titulo=doc.titulo,
        descripcion=doc.descripcion,
        propietario_id=doc.propietario_id,
        departamento=doc.departamento.nombre,
        nivel_confidencialidad=doc.nivel_confidencialidad,
        estado=doc.estado,
        pais=doc.pais,
        fecha_creacion=doc.fecha_creacion,
    )


@app.put(
    "/documentos/{documento_id}",
    response_model=DocumentoSchema,
    tags=["Documentos"],
)
def modificar_documento(
    documento_id: int,
    datos_actualizados: DocumentoCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
    entorno: ContextoEntorno = Depends(obtener_entorno_solicitud),
):
    doc = db.query(Documento).filter_by(id=documento_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
        )

    permitido, motivo = AuthorizationEngine.evaluar_solicitud(
        usuario=usuario_actual,
        operacion="MODIFICAR_DOCUMENTO",
        documento=doc,
        entorno=entorno,
        db=db,
    )

    if not permitido:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=motivo)

    doc.titulo = datos_actualizados.titulo
    doc.descripcion = datos_actualizados.descripcion
    doc.nivel_confidencialidad = datos_actualizados.nivel_confidencialidad
    db.commit()
    db.refresh(doc)

    return DocumentoSchema(
        id=doc.id,
        titulo=doc.titulo,
        descripcion=doc.descripcion,
        propietario_id=doc.propietario_id,
        departamento=doc.departamento.nombre,
        nivel_confidencialidad=doc.nivel_confidencialidad,
        estado=doc.estado,
        pais=doc.pais,
        fecha_creacion=doc.fecha_creacion,
    )


@app.post(
    "/documentos/{documento_id}/aprobar",
    response_model=DocumentoSchema,
    tags=["Documentos"],
)
def aprobar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
    entorno: ContextoEntorno = Depends(obtener_entorno_solicitud),
):
    doc = db.query(Documento).filter_by(id=documento_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
        )

    permitido, motivo = AuthorizationEngine.evaluar_solicitud(
        usuario=usuario_actual,
        operacion="APROBAR_DOCUMENTO",
        documento=doc,
        entorno=entorno,
        db=db,
    )

    if not permitido:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=motivo)

    doc.estado = "APROBADO"
    db.commit()
    db.refresh(doc)

    return DocumentoSchema(
        id=doc.id,
        titulo=doc.titulo,
        descripcion=doc.descripcion,
        propietario_id=doc.propietario_id,
        departamento=doc.departamento.nombre,
        nivel_confidencialidad=doc.nivel_confidencialidad,
        estado=doc.estado,
        pais=doc.pais,
        fecha_creacion=doc.fecha_creacion,
    )


@app.delete("/documentos/{documento_id}", tags=["Documentos"])
def eliminar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
    entorno: ContextoEntorno = Depends(obtener_entorno_solicitud),
):
    doc = db.query(Documento).filter_by(id=documento_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado"
        )

    permitido, motivo = AuthorizationEngine.evaluar_solicitud(
        usuario=usuario_actual,
        operacion="ELIMINAR_DOCUMENTO",
        documento=doc,
        entorno=entorno,
        db=db,
    )

    if not permitido:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=motivo)

    db.delete(doc)
    db.commit()
    return {"mensaje": f"Documento {documento_id} eliminado exitosamente"}


# ==========================================
# 4. MÓDULO DE AUDITORÍA
# ==========================================
@app.get("/auditoria", tags=["Auditoría"])
def consultar_auditoria(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    if not RBACEngine.verificar_permiso(usuario_actual, "VER_AUDITORIA", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado por RBAC: No está autorizado a consultar auditorías",
        )

    logs = (
        db.query(RegistroAuditoria)
        .order_by(RegistroAuditoria.fecha.desc())
        .all()
    )
    return logs