from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class RolePermissionsBackend(ModelBackend):
    def get_user_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings that this user has through their role.
        """
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        if hasattr(user_obj, 'role') and user_obj.role:
            role_perms = user_obj.role.permissions.all().values_list(
                'content_type__app_label', 'codename'
            )
            return {f"{app_label}.{codename}" for app_label, codename in role_perms}
        
        return set()

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        
        return super().get_all_permissions(user_obj, obj) | self.get_user_permissions(user_obj, obj)

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)
