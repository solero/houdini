from houdini.handlers import check


def has(permission_name, check_above=True):
    def check_permission(_, p):
        def check_permission_recursive(permissions, permission):
            if permission in permissions:
                return permissions[permission].enabled
            if '.' in permission and check_above:
                check_permission_recursive(permissions, '.'.join(permission.split('.')[:-1]))
            return False
        return check_permission_recursive(p.permissions, permission_name)
    return check(check_permission)
