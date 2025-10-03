"""
RBAC序列化器模块 - 导入拆分后的序列化器
"""
from .serializers.base import MultiSerializerMixin, BaseModelViewSet
from .serializers.user import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer, 
    UserUpdateSerializer, UserPasswordResetSerializer
)
from .serializers.role import (
    RoleListSerializer, RoleDetailSerializer, RoleCreateSerializer, 
    RoleUpdateSerializer
)
from .serializers.department import DepartmentSerializer
from .serializers.menu import MenuSerializer, RoleMenuSerializer
from .serializers.api import ApiGroupSerializer, ApiSerializer, ApiLogSerializer

# 保持向后兼容
__all__ = [
    'MultiSerializerMixin',
    'BaseModelViewSet',
    'UserListSerializer',
    'UserDetailSerializer', 
    'UserCreateSerializer',
    'UserUpdateSerializer',
    'UserPasswordResetSerializer',
    'RoleListSerializer',
    'RoleDetailSerializer',
    'RoleCreateSerializer',
    'RoleUpdateSerializer',
    'DepartmentSerializer',
    'MenuSerializer',
    'RoleMenuSerializer',
    'ApiGroupSerializer',
    'ApiSerializer',
    'ApiLogSerializer',
]