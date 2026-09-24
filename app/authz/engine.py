from sqlalchemy.orm import Session
from app.authz.abac import ABACPolicyEngine
from app.authz.rbac import RBACEngine
from app.models import Documento, RegistroAuditoria, Usuario
from app.schemas import ContextoEntorno


class AuthorizationEngine:

    @staticmethod
    def evaluar_solicitud(
        usuario: Usuario,
        operacion: str,
        documento: Documento,
        entorno: ContextoEntorno,
        db: Session,
    ) -> bool:
        """Coordinador en cascada RBAC + ABAC con registro automático de auditoría."""

        # 1. Evaluación RBAC
        rbac_permitido = RBACEngine.verificar_permiso(usuario, operacion, db)
        if not rbac_permitido:
            motivo = f"Denegado por RBAC: El rol '{usuario.rol.nombre}' no tiene el permiso '{operacion}'"
            AuthorizationEngine._registrar_auditoria(
                usuario.correo, documento.titulo, operacion, "DENEGADO", motivo, db
            )
            return False, motivo

        # 2. Evaluación ABAC
        abac_permitido, motivo_abac = ABACPolicyEngine.evaluar_politicas(
            usuario, documento, operacion, entorno
        )
        if not abac_permitido:
            motivo = f"Denegado por ABAC: {motivo_abac}"
            AuthorizationEngine._registrar_auditoria(
                usuario.correo, documento.titulo, operacion, "DENEGADO", motivo, db
            )
            return False, motivo

        # 3. Acceso Concedido
        motivo_exito = "Acceso autorizado por evaluación combinada RBAC + ABAC"
        AuthorizationEngine._registrar_auditoria(
            usuario.correo, documento.titulo, operacion, "PERMITIDO", motivo_exito, db
        )
        return True, motivo_exito

    @staticmethod
    def _registrar_auditoria(
        usuario: str,
        recurso: str,
        accion: str,
        resultado: str,
        motivo: str,
        db: Session,
    ):
        log = RegistroAuditoria(
            usuario=usuario,
            recurso=recurso,
            accion=accion,
            resultado=resultado,
            motivo=motivo,
        )
        db.add(log)
        db.commit()