"""
自定义权限类 - 集成Casbin权限系统
"""
from rest_framework.permissions import BasePermission
from .simple_rbac import check_permission


class CasbinPermission(BasePermission):
    """最简单的权限检查类"""
    
    def has_permission(self, request, view):
        return check_permission(request.user, request.path_info, request.method)


class CasbinObjectPermission(BasePermission):
    """
    基于Casbin的对象级权限检查类
    """
    
    def has_permission(self, request, view):
        """检查用户是否有权限访问该视图"""
        return CasbinPermission().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定对象"""
        # 对于对象级权限，我们也可以使用相同的权限检查逻辑
        # 或者根据具体需求实现更细粒度的权限控制
        return self.has_permission(request, view)
