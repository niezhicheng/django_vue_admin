"""
RBAC模型模块 - 导入拆分后的模型
"""
from .models.base import BaseDataPermissionModel, DataPermissionModelManager, DataPermissionManager
from .models.user import User, UserRole
from .models.role import Role
from .models.department import Department
from .models.menu import Menu, RoleMenu
from .models.api import ApiGroup, Api, ApiLog
from .models.permission import PolicyRule

# 保持向后兼容
__all__ = [
    'BaseDataPermissionModel',
    'DataPermissionModelManager', 
    'DataPermissionManager',
    'User',
    'UserRole',
    'Role',
    'Department',
    'Menu',
    'RoleMenu',
    'ApiGroup',
    'Api',
    'ApiLog',
    'PolicyRule',
]
