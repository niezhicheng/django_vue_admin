"""
RBAC视图模块
"""
from .user import UserViewSet
from .role import RoleViewSet
from .department import DepartmentViewSet
from .menu import MenuViewSet
from .api import ApiGroupViewSet, ApiViewSet
from .auth import (
    CustomTokenObtainPairView, CustomTokenRefreshView, 
    jwt_profile_view, user_menus_view
)
from .permission import (
    get_role_api_permissions, assign_role_api_permissions,
    get_role_menu_permissions, assign_role_menu_permissions
)

__all__ = [
    'UserViewSet',
    'RoleViewSet', 
    'DepartmentViewSet',
    'MenuViewSet',
    'ApiGroupViewSet',
    'ApiViewSet',
    'CustomTokenObtainPairView',
    'CustomTokenRefreshView',
    'jwt_profile_view',
    'user_menus_view',
    'get_role_api_permissions',
    'assign_role_api_permissions',
    'get_role_menu_permissions',
    'assign_role_menu_permissions',
]
