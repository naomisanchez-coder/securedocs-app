from passlib.context import CryptContext
from app.database import Base, SessionLocal, engine
from app.models import (
    Departamento,
    Documento,
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def inicializar_bd():
    print(
        "Recreando tablas en la base de datos configurada en DATABASE_URL..."
    )
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Insertar Roles
        rol_admin = Rol(id=1, nombre="ADMINISTRADOR")
        rol_empleado = Rol(id=2, nombre="EMPLEADO")
        rol_invitado = Rol(id=3, nombre="INVITADO")
        db.add_all([rol_admin, rol_empleado, rol_invitado])

        # 2. Insertar Departamentos
        dep_finanzas = Departamento(id=1, nombre="FINANZAS")
        dep_rrhh = Departamento(id=2, nombre="RRHH")
        dep_ti = Departamento(id=3, nombre="TI")
        db.add_all([dep_finanzas, dep_rrhh, dep_ti])

        # 3. Insertar Permisos RBAC
        p1 = Permiso(id=1, nombre="GESTIONAR_USUARIOS")
        p2 = Permiso(id=2, nombre="CREAR_DOCUMENTO")
        p3 = Permiso(id=3, nombre="VER_AUDITORIA")
        p4 = Permiso(id=4, nombre="CONSULTAR_DOCUMENTO")
        db.add_all([p1, p2, p3, p4])
        db.commit()

        # Asignar Permisos a Roles
        for p in [p1, p2, p3, p4]:
            db.add(RolPermiso(rol_id=1, permiso_id=p.id))  # Admin
        db.add(RolPermiso(rol_id=2, permiso_id=p2.id))  # Empleado
        db.add(RolPermiso(rol_id=2, permiso_id=p4.id))  # Empleado
        db.commit()

        # 4. Insertar Usuarios
        pwd_comun = hash_password("password123")

        u1 = Usuario(
            nombre="Administrador General",
            correo="admin@techcorp.com",
            password_hash=pwd_comun,
            rol_id=1,
            departamento_id=3,
            nivel_seguridad=5,
            pais="PERU",
            tipo_contrato="INTERNO",
            estado="ACTIVO",
        )
        u2 = Usuario(
            nombre="Juan Perez (RRHH)",
            correo="juan@techcorp.com",
            password_hash=pwd_comun,
            rol_id=2,
            departamento_id=2,
            nivel_seguridad=3,
            pais="PERU",
            tipo_contrato="INTERNO",
            estado="ACTIVO",
        )
        u3 = Usuario(
            nombre="Maria Lopez (Finanzas)",
            correo="maria@techcorp.com",
            password_hash=pwd_comun,
            rol_id=2,
            departamento_id=1,
            nivel_seguridad=2,
            pais="PERU",
            tipo_contrato="INTERNO",
            estado="ACTIVO",
        )
        u4 = Usuario(
            nombre="Carlos Gomez (Invitado)",
            correo="carlos@techcorp.com",
            password_hash=pwd_comun,
            rol_id=3,
            departamento_id=None,
            nivel_seguridad=1,
            pais="PERU",
            tipo_contrato="EXTERNO",
            estado="ACTIVO",
        )
        db.add_all([u1, u2, u3, u4])
        db.commit()

        # 5. Insertar Documentos de Prueba
        d1 = Documento(
            titulo="Reporte Financiero 2026",
            descripcion="Presupuesto anual de operaciones",
            propietario_id=u3.id,
            departamento_id=1,
            nivel_confidencialidad=2,
            estado="APROBADO",
            pais="PERU",
        )
        d2 = Documento(
            titulo="Contratos Personal RRHH",
            descripcion="Expedientes laborales del personal",
            propietario_id=u2.id,
            departamento_id=2,
            nivel_confidencialidad=3,
            estado="PENDIENTE",
            pais="PERU",
        )
        d3 = Documento(
            titulo="Manual de Servidores TI",
            descripcion="Infraestructura crítica del sistema",
            propietario_id=u1.id,
            departamento_id=3,
            nivel_confidencialidad=4,
            estado="APROBADO",
            pais="PERU",
        )
        db.add_all([d1, d2, d3])
        db.commit()

        print("Base de datos recreada y poblada exitosamente en PostgreSQL.")
    except Exception as e:
        db.rollback()
        print(f"Error al poblar la base de datos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    inicializar_bd()