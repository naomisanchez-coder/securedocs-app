from sqlalchemy.orm import Session
from app.models import Permiso, RolPermiso, Usuario


class RBACEngine:

    @staticmethod
    def verificar_permiso(usuario: Usuario, operacion: str, db: Session) -> bool:
        """Verifica si el rol del usuario posee el permiso base para realizar la operación."""
        permisos = (
            db.query(Permiso.nombre)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .filter(RolPermiso.rol_id == usuario.rol_id)
            .all()
        )
        lista_permisos = [p[0] for p in permisos]
        return operacion in lista_permisos