# 🛡️ SecureDocs - Sistema de Gestión de Expedientes con Control de Acceso Combinado (RBAC + ABAC)

**SecureDocs** es una plataforma web para la gestión segura de documentos confidenciales que implementa un modelo híbrido de control de acceso combinando **RBAC (Role-Based Access Control)** y **ABAC (Attribute-Based Access Control)**. El sistema no solo valida *quién* intenta realizar una acción mediante su rol, sino *bajo qué condiciones* (departamento, nivel de confidencialidad, hora, ubicación geográfica y dispositivo).

---

## 📐 Arquitectura del Sistema y Lógica de Negocio

El sistema evalúa las solicitudes HTTP en dos niveles secuenciales antes de permitir el acceso a los datos o registrar eventos:
[ Cliente SPA ]│ (HTTPS + JWT)▼[ FastAPI Backend ]│├──> [ 1. Módulo RBAC ]: ¿El ROL posee la función? (ej: CREAR_DOCUMENTO)│          ││          ├── (NO) ──> [ Auditoría: DENEGADO ] ──> HTTP 403│          └── (SÍ)│                ▼└──> [ 2. Motor ABAC ]: Evalúa contexto (Hora, Ubicación, Dispositivo, Nivel Seguridad vs. Confidencialidad)│├── (NO) ──> [ Auditoría: DENEGADO ] ──> HTTP 403└── (SÍ) ──> [ Data Access Layer (PostgreSQL) ] ──> [ Auditoría: PERMITIDO ]
### 🔐 Modelo de Autenticación y Autorización
* **JWT (JSON Web Tokens):** Firma digital segura (`HS256`) para la sesión del usuario.
* **Filtro Cascadas (RBAC + ABAC):**
  1. **Filtro RBAC:** Valida que el rol (`ADMINISTRADOR`, `EMPLEADO`, `INVITADO`) contenga los permisos en la tabla `rol_permisos`.
  2. **Filtro ABAC:** El `AuthorizationEngine` evalúa 8 reglas dinámicas comparando atributos del sujeto, recurso y entorno.
* **Auditoría Centralizada:** Cada solicitud (permitida o bloqueada) registra automáticamente una traza inmutable en la tabla `auditorias`.

---

## 🗄️ Modelo Entidad-Relación (Base de Datos)

La base de datos relacional (PostgreSQL) se compone de 7 entidades principales:

* **roles:** `id`, `nombre` (`ADMINISTRADOR`, `EMPLEADO`, `INVITADO`), `descripcion`.
* **departamentos:** `id`, `nombre` (`FINANZAS`, `RRHH`, `TI`).
* **permisos:** `id`, `nombre` (`GESTIONAR_USUARIOS`, `CREAR_DOCUMENTO`, `VER_AUDITORIA`, `CONSULTAR_DOCUMENTO`).
* **rol_permisos:** Tabla intermedia M:N entre roles y permisos.
* **usuarios:** `id`, `nombre`, `correo`, `password_hash`, `rol_id`, `departamento_id`, `nivel_seguridad` (1-5), `pais`, `tipo_contrato`, `estado`.
* **documentos:** `id`, `titulo`, `descripcion`, `propietario_id`, `departamento_id`, `nivel_confidencialidad` (1-5), `estado`, `pais`, `fecha_creacion`.
* **auditorias:** `id`, `usuario`, `recurso`, `accion`, `fecha`, `resultado` (`PERMITIDO` / `DENEGADO`), `motivo`.

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3.9+, FastAPI, SQLAlchemy (ORM), PassLib (Bcrypt), PyJWT.
* **Base de Datos:** PostgreSQL (o SQLite para entornos de pruebas locales).
* **Frontend:** HTML5, JavaScript ES6 (Fetch API), CSS3 / Tailwind CSS (SPA en `/static`).
* **Servidor de Aplicación:** Uvicorn (ASGI Server).

---

## 🚀 Guía de Instalación y Ejecución Paso a Paso

### 1. Requisitos Previos
Tener instalado Python 3.9+ y PostgreSQL.

### 2. Clonar el Repositorio e Ingresar a la Carpeta
```bash
git clone <URL_DE_TU_REPOSITORIO>
cd securedocs-app
3. Crear y Activar el Entorno VirtualEn macOS / Linux:Bashpython3 -m venv venv
source venv/bin/activate
En Windows (PowerShell):PowerShellpython -m venv venv
.\venv\Scripts\Activate.ps1
4. Instalar DependenciasBashpip install -r requirements.txt
5. Configurar Variables de Entorno (.env)Crea un archivo .env en la raíz del proyecto con la cadena de conexión a tu base de datos:Fragmento de códigoDATABASE_URL=postgresql://postgres:isabel123@localhost:5432/securedocs_db
SECRET_KEY=clave_secreta_para_jwt_techcorp_2026
6. Poblar la Base de Datos (Seed Data)Ejecuta el módulo de inicialización para crear las tablas e insertar roles, departamentos, usuarios y documentos iniciales:Bashpython -m app.seed

7. Iniciar el Servidor de DesarrolloBashuvicorn app.main:app --reload
Accede a la interfaz web ingresando en tu navegador a: http://127.0.0.1:8000🔑 Credenciales de Acceso para PruebasTodos los usuarios de prueba comparten la contraseña por defecto: password123 Usuario,Correo Electrónico,Rol,Departamento,Nivel Seguridad,Permisos Especiales,Administrador: admin@techcorp.comADMINISTRADORTI Nivel 5 Acceso total, Gestión de Usuarios y Auditoría Juan Pérez:juan@techcorp.comEMPLEADORRHHNivel 3 Acceso exclusivo a expedientes de RRHH María Lópezmaria@techcorp.com EMPLEADOFINANZAS Nivel 2 Acceso exclusivo a expedientes de Finanzas Carlos Gómez carlos@techcorp.como INVITADO NingúnNivel 1 Acceso estrictamente restringido.

📝 Explicación Paso a Paso de lo Realizado en el Proyecto Modelado e Infraestructura ORM:
 Se definieron los modelos relacionales en app/models.py asegurando integridad referencial para roles, permisos, áreas corporativas y auditoría.Encriptación de Seguridad: Implementación de hashing seguro con Bcrypt para almacenar las contraseñas en la base de datos y generación de tokens JWT para el manejo de sesiones sin estado (stateless).Motor de Decisiones Combinado:RBAC (app/authz/rbac.py): Consulta la matriz de permisos para determinar si la acción está permitida para el rol asignado.ABAC (app/authz/engine.py): Evalúa dinámicamente contextos de entorno (dispositivo corporativo vs. personal, horario laboral, nivel de seguridad del usuario vs. confidencialidad del documento).Registro de Trazabilidad (Auditoría): Se automatizó la captura de intentos de acceso denegados e información circunstancial (motivo exacto del rechazo, IP del cliente, fecha y hora).Interfaz de Usuario Web (SPA): Rediseño moderno para la experiencia de inicio de sesión y simulación de contextos dinámicos (cambio de dispositivo u hora) para probar las reglas de seguridad ABAC en vivo.