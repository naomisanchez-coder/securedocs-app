import sqlite3
from passlib.context import CryptContext

# Contexto para encriptar contraseñas igual que en auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def inicializar_bd():
    conn = sqlite3.connect("securedocs.db")
    cursor = conn.cursor()

    # 1. Crear Tablas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol_id INTEGER NOT NULL,
        departamento_id INTEGER,
        nivel_seguridad INTEGER NOT NULL,
        pais TEXT NOT NULL,
        FOREIGN KEY (rol_id) REFERENCES roles (id),
        FOREIGN KEY (departamento_id) REFERENCES departamentos (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        departamento_id INTEGER,
        nivel_confidencialidad INTEGER NOT NULL,
        estado TEXT NOT NULL,
        pais TEXT NOT NULL,
        FOREIGN KEY (departamento_id) REFERENCES departamentos (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registro_auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        usuario TEXT NOT NULL,
        recurso TEXT NOT NULL,
        accion TEXT NOT NULL,
        resultado TEXT NOT NULL,
        motivo TEXT
    );
    """)

    # 2. Insertar Datos Iniciales (Roles y Departamentos)
    cursor.executemany("""
    INSERT OR IGNORE INTO roles (id, nombre, descripcion) VALUES (?, ?, ?)
    """, [
        (1, "ADMINISTRADOR", "Acceso total al sistema"),
        (2, "EMPLEADO", "Acceso operativo regular"),
        (3, "INVITADO", "Acceso restringido")
    ])

    cursor.executemany("""
    INSERT OR IGNORE INTO departamentos (id, nombre) VALUES (?, ?)
    """, [
        (1, "FINANZAS"),
        (2, "RRHH"),
        (3, "TI")
    ])

    # 3. Insertar Usuarios con Hash Correcto
    password_comun = hash_password("password123")

    usuarios = [
        ("Administrador General", "admin@techcorp.com", password_comun, 1, 3, 5, "PERU"),
        ("Juan Perez (RRHH)", "juan@techcorp.com", password_comun, 2, 2, 3, "PERU"),
        ("Maria Lopez (Finanzas)", "maria@techcorp.com", password_comun, 2, 1, 2, "PERU"),
        ("Carlos Gomez (Invitado)", "carlos@techcorp.com", password_comun, 3, None, 1, "PERU")
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO usuarios (nombre, correo, password_hash, rol_id, departamento_id, nivel_seguridad, pais)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, usuarios)

    # 4. Insertar Documentos de Prueba
    documentos = [
        ("Reporte Financiero 2026", "Presupuesto anual de operaciones", 1, 2, "APROBADO", "PERU"),
        ("Contratos Personal RRHH", "Expedientes laborales del personal", 2, 3, "PENDIENTE", "PERU"),
        ("Manual de Servidores TI", "Infraestructura crítica del sistema", 3, 4, "APROBADO", "PERU")
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO documentos (titulo, descripcion, departamento_id, nivel_confidencialidad, estado, pais)
    VALUES (?, ?, ?, ?, ?, ?)
    """, documentos)

    conn.commit()
    conn.close()
    print("Base de datos generada y poblada exitosamente.")

if __name__ == "__main__":
    inicializar_bd()