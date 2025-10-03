"""
RBAC视图模块 - 导入拆分后的视图
"""
from .views.user import UserViewSet
from .views.role import RoleViewSet
from .views.department import DepartmentViewSet
from .views.menu import MenuViewSet
from .views.api import ApiGroupViewSet, ApiViewSet
from .views.auth import (
    CustomTokenObtainPairView, CustomTokenRefreshView, 
    jwt_profile_view, user_menus_view
)
from .views.permission import (
    get_role_api_permissions, assign_role_api_permissions,
    get_role_menu_permissions, assign_role_menu_permissions
)

# 保持向后兼容
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
