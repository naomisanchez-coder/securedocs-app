from datetime import datetime
from typing import Tuple
from app.models import Documento, Usuario
from app.schemas import ContextoEntorno


class ABACPolicyEngine:

    @staticmethod
    def evaluar_politicas(
        usuario: Usuario,
        documento: Documento,
        accion: str,
        entorno: ContextoEntorno,
    ) -> Tuple[bool, str]:
        """Evalúa las 8 políticas ABAC obligatorias.

        Retorna (True, 'PERMITIDO') o (False, 'Motivo del rechazo')
        """

        # Política 7: Estado del usuario (Aplica globalmente)
        if usuario.estado != "ACTIVO":
            return False, "Política 7: El usuario se encuentra inactivo o suspendido"

        # Política 8: Reglas específicas para Invitados
        if usuario.rol.nombre == "INVITADO":
            if usuario.tipo_contrato != "EXTERNO":
                return False, "Política 8: El invitado debe tener contrato EXTERNO"
            if documento.nivel_confidencialidad > 1:
                return (
                    False,
                    "Política 8: Invitados solo pueden acceder a documentos de nivel de confidencialidad <= 1",
                )
            if documento.estado != "PUBLICADO":
                return False, "Política 8: Invitados solo pueden acceder a documentos en estado PUBLICADO"

        # Política 1: Departamento (Empleados solo acceden a sus documentos)
        if usuario.rol.nombre == "EMPLEADO":
            if usuario.departamento_id != documento.departamento_id:
                return (
                    False,
                    "Política 1: Los empleados solo pueden acceder a documentos de su propio departamento",
                )

        # Política 2: Nivel de seguridad
        if usuario.nivel_seguridad < documento.nivel_confidencialidad:
            return (
                False,
                f"Política 2: Nivel de seguridad del usuario ({usuario.nivel_seguridad}) es inferior a la confidencialidad del documento ({documento.nivel_confidencialidad})",
            )

        # Política 3: Propiedad del documento al modificar
        if accion == "MODIFICAR_DOCUMENTO" and usuario.rol.nombre not in [
            "ADMINISTRADOR",
            "GERENTE",
        ]:
            if documento.propietario_id != usuario.id:
                return (
                    False,
                    "Política 3: Solo el propietario del documento puede modificarlo",
                )

        # Política 4: Horario de acceso para documentos altamente confidenciales
        if documento.nivel_confidencialidad >= 4:
            try:
                hora_actual = datetime.strptime(entorno.hora, "%H:%M").time()
                hora_inicio = datetime.strptime("08:00", "%H:%M").time()
                hora_fin = datetime.strptime("18:00", "%H:%M").time()

                if not (hora_inicio <= hora_actual <= hora_fin):
                    return (
                        False,
                        "Política 4: Documentos de alta confidencialidad (>=4) solo son accesibles de 08:00 a 18:00",
                    )
            except ValueError:
                pass  # Si el formato de hora es inválido, continúa evaluación

        # Política 5: Restricción por País
        if documento.pais == "PERU" and entorno.ubicacion != "PERU":
            return (
                False,
                "Política 5: Documentos de operaciones de Perú solo son accesibles desde Perú",
            )

        # Política 6: Restricción por Dispositivo
        if documento.nivel_confidencialidad >= 4 and entorno.dispositivo != "CORPORATIVO":
            return (
                False,
                "Política 6: Documentos de confidencialidad >= 4 solo pueden accederse desde dispositivos CORPORATIVOS",
            )

        return True, "Acceso concedido por políticas ABAC"