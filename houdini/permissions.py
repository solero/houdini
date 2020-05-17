from houdini.handlers import check


def check_permission(p, permission_name, check_above=True):
    def check_permission_recursive(permissions, permission):
        if permission in permissions:
            return p.server.permissions[permission].enabled
        if '.' in permission and check_above:
            return check_permission_recursive(permissions, '.'.join(permission.split('.')[:-1]))
        return False

    return check_permission_recursive(p.permissions, permission_name)


def has(permission_name, check_above=True):
    def has_permission(_, p):
        return check_permission(p, permission_name, check_above)
    return check(has_permission)


def has_or_moderator(permission_name, check_above=True):
    def or_moderator(_, p):
        return p.moderator or check_permission(p, permission_name, check_above)
    return check(or_moderator)


def has_or_mascot(permission_name, check_above=True):
    def or_mascot(_, p):
        return p.character or check_permission(p, permission_name, check_above)
    return check(or_mascot)
