from passlib.context import CryptContext
from app.database import Base, SessionLocal, engine
from app.models import Departamento, Permiso, Rol, RolPermiso, Usuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def seed_data():
    # Crear tablas en la base de datos
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Crear Departamentos
        deptos_nombres = ["FINANZAS", "RRHH", "SISTEMAS", "LOGISTICA", "VENTAS"]
        deptos_db = {}
        for d_nombre in deptos_nombres:
            depto = db.query(Departamento).filter_by(nombre=d_nombre).first()
            if not depto:
                depto = Departamento(nombre=d_nombre)
                db.add(depto)
                db.commit()
                db.refresh(depto)
            deptos_db[d_nombre] = depto

        # 2. Crear Permisos RBAC
        permisos_nombres = [
            "CREAR_DOCUMENTO",
            "CONSULTAR_DOCUMENTO",
            "MODIFICAR_DOCUMENTO",
            "ELIMINAR_DOCUMENTO",
            "APROBAR_DOCUMENTO",
            "VER_AUDITORIA",
            "GESTIONAR_USUARIOS",
            "ASIGNAR_ROLES",
        ]
        permisos_db = {}
        for p_nombre in permisos_nombres:
            permiso = db.query(Permiso).filter_by(nombre=p_nombre).first()
            if not permiso:
                permiso = Permiso(nombre=p_nombre)
                db.add(permiso)
                db.commit()
                db.refresh(permiso)
            permisos_db[p_nombre] = permiso

        # 3. Crear Roles
        roles_nombres = [
            "ADMINISTRADOR",
            "GERENTE",
            "SUPERVISOR",
            "EMPLEADO",
            "AUDITOR",
            "INVITADO",
        ]
        roles_db = {}
        for r_nombre in roles_nombres:
            rol = db.query(Rol).filter_by(nombre=r_nombre).first()
            if not rol:
                rol = Rol(nombre=r_nombre)
                db.add(rol)
                db.commit()
                db.refresh(rol)
            roles_db[r_nombre] = rol

        # 4. Asignar Matriz RBAC (Según Tabla del Laboratorio)
        matriz_rbac = {
            "ADMINISTRADOR": [
                "CREAR_DOCUMENTO",
                "CONSULTAR_DOCUMENTO",
                "MODIFICAR_DOCUMENTO",
                "ELIMINAR_DOCUMENTO",
                "APROBAR_DOCUMENTO",
                "VER_AUDITORIA",
                "GESTIONAR_USUARIOS",
                "ASIGNAR_ROLES",
            ],
            "GERENTE": [
                "CREAR_DOCUMENTO",
                "CONSULTAR_DOCUMENTO",
                "MODIFICAR_DOCUMENTO",
                "ELIMINAR_DOCUMENTO",
                "APROBAR_DOCUMENTO",
                "VER_AUDITORIA",
            ],
            "SUPERVISOR": [
                "CREAR_DOCUMENTO",
                "CONSULTAR_DOCUMENTO",
                "MODIFICAR_DOCUMENTO",
                "APROBAR_DOCUMENTO",
            ],
            "EMPLEADO": [
                "CREAR_DOCUMENTO",
                "CONSULTAR_DOCUMENTO",
                "MODIFICAR_DOCUMENTO",
            ],
            "AUDITOR": [
                "CONSULTAR_DOCUMENTO",
                "VER_AUDITORIA",
            ],
            "INVITADO": [
                "CONSULTAR_DOCUMENTO",
            ],
        }

        for rol_nombre, lista_permisos in matriz_rbac.items():
            rol_obj = roles_db[rol_nombre]
            for perm_nombre in lista_permisos:
                perm_obj = permisos_db[perm_nombre]
                existe = (
                    db.query(RolPermiso)
                    .filter_by(rol_id=rol_obj.id, permiso_id=perm_obj.id)
                    .first()
                )
                if not existe:
                    rp = RolPermiso(rol_id=rol_obj.id, permiso_id=perm_obj.id)
                    db.add(rp)
        db.commit()

        # 5. Usuarios de prueba (Escenarios del Lab)
        usuarios_semilla = [
            {
                "nombre": "Admin TechCorp",
                "correo": "admin@techcorp.com",
                "password": "Password123!",
                "rol": "ADMINISTRADOR",
                "depto": "SISTEMAS",
                "nivel": 5,
                "pais": "PERU",
                "contrato": "INTERNO",
                "estado": "ACTIVO",
            },
            {
                "nombre": "Carlos Ruiz",
                "correo": "carlos.ruiz@techcorp.com",
                "password": "Password123!",
                "rol": "SUPERVISOR",
                "depto": "FINANZAS",
                "nivel": 3,
                "pais": "PERU",
                "contrato": "INTERNO",
                "estado": "ACTIVO",
            },
            {
                "nombre": "Ana Torres",
                "correo": "ana.torres@techcorp.com",
                "password": "Password123!",
                "rol": "SUPERVISOR",
                "depto": "FINANZAS",
                "nivel": 3,
                "pais": "PERU",
                "contrato": "INTERNO",
                "estado": "ACTIVO",
            },
            {
                "nombre": "Empleado RRHH",
                "correo": "empleado.rrhh@techcorp.com",
                "password": "Password123!",
                "rol": "EMPLEADO",
                "depto": "RRHH",
                "nivel": 2,
                "pais": "PERU",
                "contrato": "INTERNO",
                "estado": "ACTIVO",
            },
            {
                "nombre": "Auditor Externo",
                "correo": "auditor@techcorp.com",
                "password": "Password123!",
                "rol": "AUDITOR",
                "depto": "FINANZAS",
                "nivel": 5,
                "pais": "PERU",
                "contrato": "INTERNO",
                "estado": "ACTIVO",
            },
            {
                "nombre": "Usuario Inactivo",
                "correo": "inactivo@techcorp.com",
                "password": "Password123!",
                "rol": "EMPLEADO",
                "depto": "FINANZAS",
                "nivel": 2,
                "pais": "PERU",
                "contrato": "INTERNO",
                "estado": "INACTIVO",
            },
            {
                "nombre": "Invitado Temporal",
                "correo": "invitado@externo.com",
                "password": "Password123!",
                "rol": "INVITADO",
                "depto": "VENTAS",
                "nivel": 1,
                "pais": "PERU",
                "contrato": "EXTERNO",
                "estado": "ACTIVO",
            },
        ]

        for u in usuarios_semilla:
            user_exists = db.query(Usuario).filter_by(correo=u["correo"]).first()
            if not user_exists:
                nuevo_usuario = Usuario(
                    nombre=u["nombre"],
                    correo=u["correo"],
                    password_hash=hash_password(u["password"]),
                    rol_id=roles_db[u["rol"]].id,
                    departamento_id=deptos_db[u["depto"]].id,
                    nivel_seguridad=u["nivel"],
                    pais=u["pais"],
                    tipo_contrato=u["contrato"],
                    estado=u["estado"],
                )
                db.add(nuevo_usuario)

        db.commit()
        print("✅ Base de datos poblada exitosamente con roles, permisos y usuarios de prueba.")

    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()