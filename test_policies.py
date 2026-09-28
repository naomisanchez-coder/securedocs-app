from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def obtener_token(correo: str, password: str = "password123"):
    response = client.post(
        "/auth/login", json={"correo": correo, "password": password}
    )
    assert response.status_code == 200, f"Error autenticando {correo}: {response.text}"
    return response.json()["access_token"]


# -------------------------------------------------------------
# AUTENTICACIÓN Y ROLES BASE (PRUEBAS 1 Y 2)
# -------------------------------------------------------------
def test_01_login_exitoso():
    response = client.post(
        "/auth/login",
        json={"correo": "admin@techcorp.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_02_login_fallido_credenciales_incorrectas():
    response = client.post(
        "/auth/login",
        json={"correo": "admin@techcorp.com", "password": "clave_erronea"},
    )
    assert response.status_code == 401


# -------------------------------------------------------------
# CONTROL DE ACCESO RBAC (PRUEBAS 3 Y 4)
# -------------------------------------------------------------
def test_03_rbac_empleado_crear_documento_permitido():
    token = obtener_token("ana.finanzas@techcorp.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "titulo": "Presupuesto Q3",
        "descripcion": "Detalles",
        "departamento_id": 1,
        "nivel_confidencialidad": 1,
        "pais": "PERU",
    }
    response = client.post("/documentos", json=payload, headers=headers)
    assert response.status_code == 200


def test_04_rbac_invitado_crear_documento_denegado():
    token = obtener_token("invitado@techcorp.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "titulo": "Doc no permitido",
        "departamento_id": 1,
        "nivel_confidencialidad": 1,
    }
    response = client.post("/documentos", json=payload, headers=headers)
    assert response.status_code == 403


# -------------------------------------------------------------
# POLÍTICA 1: DEPARTAMENTO (PRUEBAS 5 Y 6)
# -------------------------------------------------------------
def test_05_politica_1_mismo_departamento_permitido():
    token = obtener_token("ana.finanzas@techcorp.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/documentos/1", headers=headers)
    assert response.status_code == 200


def test_06_politica_1_diferente_departamento_denegado():
    token = obtener_token("ana.finanzas@techcorp.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/documentos/2", headers=headers)  # Doc 2 es de RRHH
    assert response.status_code == 403
    assert "Política 1" in response.json()["detail"]


# -------------------------------------------------------------
# POLÍTICA 2: NIVEL DE SEGURIDAD (PRUEBAS 7 Y 8)
# -------------------------------------------------------------
def test_07_politica_2_nivel_seguridad_suficiente():
    token = obtener_token("admin@techcorp.com")  # Nivel 5
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Hora": "10:00",             # Evita el bloqueo de la Política 4
        "X-Dispositivo": "CORPORATIVO", # Evita el bloqueo de la Política 6
    }
    response = client.get("/documentos/2", headers=headers)  # Doc confidencialidad 4
    assert response.status_code == 200


def test_08_politica_2_nivel_seguridad_insuficiente():
    token = obtener_token("pedro.ventas@techcorp.com")  # Nivel 1
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/documentos/2", headers=headers)  # Doc confidencialidad 4
    assert response.status_code == 403


# -------------------------------------------------------------
# POLÍTICA 3: PROPIEDAD DEL RECURSO (PRUEBAS 9 Y 10)
# -------------------------------------------------------------
def test_09_politica_3_propietario_modifica_permitido():
    token = obtener_token("ana.finanzas@techcorp.com")  # Propietaria del doc 1
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "titulo": "Balance Modificado",
        "departamento_id": 1,
        "nivel_confidencialidad": 2,
    }
    response = client.put("/documentos/1", json=payload, headers=headers)
    assert response.status_code == 200


def test_10_politica_3_no_propietario_modifica_denegado():
    token = obtener_token("pedro.ventas@techcorp.com")  # No es propietario
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "titulo": "Intento Modificacion",
        "departamento_id": 1,
        "nivel_confidencialidad": 2,
    }
    response = client.put("/documentos/1", json=payload, headers=headers)
    assert response.status_code == 403


# -------------------------------------------------------------
# POLÍTICA 4: HORARIO DE ACCESO (PRUEBAS 11 Y 12)
# -------------------------------------------------------------
def test_11_politica_4_horario_permitido():
    token = obtener_token("admin@techcorp.com")
    headers = {"Authorization": f"Bearer {token}", "X-Hora": "10:00"}
    response = client.get("/documentos/2", headers=headers)
    assert response.status_code == 200


def test_12_politica_4_horario_fuera_de_rango_denegado():
    token = obtener_token("admin@techcorp.com")
    headers = {"Authorization": f"Bearer {token}", "X-Hora": "22:00"}
    response = client.get("/documentos/2", headers=headers)
    assert response.status_code == 403
    assert "Política 4" in response.json()["detail"]


# -------------------------------------------------------------
# POLÍTICA 5: RESTRICCIÓN GEOGRÁFICA (PRUEBAS 13 Y 14)
# -------------------------------------------------------------
def test_13_politica_5_ubicacion_peru_permitido():
    token = obtener_token("ana.finanzas@techcorp.com")
    headers = {"Authorization": f"Bearer {token}", "X-Ubicacion": "PERU"}
    response = client.get("/documentos/1", headers=headers)
    assert response.status_code == 200


def test_14_politica_5_ubicacion_extranjero_denegado():
    token = obtener_token("ana.finanzas@techcorp.com")
    headers = {"Authorization": f"Bearer {token}", "X-Ubicacion": "ESPANA"}
    response = client.get("/documentos/1", headers=headers)
    assert response.status_code == 403
    assert "Política 5" in response.json()["detail"]


# -------------------------------------------------------------
# POLÍTICA 6: DISPOSITIVO PERMITIDO (PRUEBA 15)
# -------------------------------------------------------------
def test_15_politica_6_dispositivo_personal_alta_confidencialidad_denegado():
    token = obtener_token("admin@techcorp.com")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Dispositivo": "PERSONAL",
        "X-Hora": "10:00",
    }
    response = client.get("/documentos/2", headers=headers)  # Doc confidencialidad 4
    assert response.status_code == 403
    assert "Política 6" in response.json()["detail"]


# -------------------------------------------------------------
# POLÍTICA 7: ESTADO DEL USUARIO (PRUEBA 16)
# -------------------------------------------------------------
def test_16_politica_7_usuario_inactivo_denegado():
    response = client.post(
        "/auth/login",
        json={"correo": "inactivo@techcorp.com", "password": "password123"},
    )
    assert response.status_code in [401, 403]


# -------------------------------------------------------------
# POLÍTICA 8 Y AUDITORÍA (PRUEBA 17)
# -------------------------------------------------------------
def test_17_politica_8_invitado_confidencialidad_alta_denegado_y_auditoria():
    token = obtener_token("invitado@techcorp.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/documentos/2", headers=headers)
    assert response.status_code == 403

    # Verificar que el intento fue registrado en auditoría
    token_admin = obtener_token("admin@techcorp.com")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    res_auditoria = client.get("/auditoria", headers=headers_admin)
    assert res_auditoria.status_code == 200
    assert len(res_auditoria.json()) > 0