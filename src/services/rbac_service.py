from dataclasses import dataclass


@dataclass(frozen=True)
class RoleProfile:
    name: str
    fallback_permissions: tuple[str, ...]


ROLE_PROFILES: dict[str, RoleProfile] = {
    "administrador": RoleProfile(
        name="Administrador",
        fallback_permissions=(
            "usuarios:gestionar",
            "usuarios:crear",
            "reportes:descargar",
            "rutas:administrar",
            "rutas:visualizar_propias",
            "sectores:administrar",
            "estadisticas:ver",
            "configuracion:gestionar",
            "auditoria:visualizar",
            "notificaciones:registrar",
            "etl:ejecutar",
        ),
    ),
    "trabajador": RoleProfile(
        name="Trabajador",
        fallback_permissions=(
            "pedidos:ver_asignados",
            "pedidos:actualizar_estado",
            "rutas:visualizar_propias",
            "perfil:ver",
            "actividades:registrar",
        ),
    ),
    "supervisor": RoleProfile(
        name="Supervisor",
        fallback_permissions=(
            "trabajadores:monitorear",
            "pedidos:validar",
            "cambios:aprobar",
            "reportes:parciales",
            "rutas:visualizar_propias",
        ),
    ),
    "jefe cobranza": RoleProfile(
        name="Jefe Cobranza",
        fallback_permissions=(
            "rutas:visualizar_propias",
            "notificaciones:registrar",
            "reportes:descargar",
            "cobranza:ver",
            "cobranza:gestionar",
        ),
    ),
    "notificador": RoleProfile(
        name="Notificador",
        fallback_permissions=(
            "rutas:visualizar_propias",
            "notificaciones:registrar",
        ),
    ),
    "soporte ti": RoleProfile(
        name="Soporte TI",
        fallback_permissions=(
            "usuarios:gestionar",
            "usuarios:crear",
            "configuracion:gestionar",
            "auditoria:visualizar",
            "etl:ejecutar",
        ),
    ),
}


def normalize_role_name(role_name: str | None) -> str:
    if not role_name:
        return ""
    return role_name.strip().lower()


def get_role_profile(role_name: str | None) -> RoleProfile | None:
    normalized = normalize_role_name(role_name)
    if normalized in ROLE_PROFILES:
        return ROLE_PROFILES[normalized]
    if "administr" in normalized:
        return ROLE_PROFILES["administrador"]
    if "jefe" in normalized and "cobran" in normalized:
        return ROLE_PROFILES["jefe cobranza"]
    if "super" in normalized:
        return ROLE_PROFILES["supervisor"]
    if "notific" in normalized or "normal" in normalized:
        return ROLE_PROFILES["notificador"]
    if "ti" in normalized or "soporte" in normalized:
        return ROLE_PROFILES["soporte ti"]
    if "trabaj" in normalized or "operador" in normalized:
        return ROLE_PROFILES["trabajador"]
    return None


def permissions_for_role(role_name: str | None, db_permissions: list[str] | None = None) -> list[str]:
    permissions = list(db_permissions or [])
    if permissions:
        return permissions
    profile = get_role_profile(role_name)
    if profile:
        return list(profile.fallback_permissions)
    return []

