"""
用户相关视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import User
from ..serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, UserPasswordResetSerializer
)
from ..utils import ApiResponse
from ..models import DataPermissionManager
from ..permissions import CasbinPermission


class UserViewSet(viewsets.ModelViewSet):
    """用户管理视图集"""
    model = User
    serializer_class = UserListSerializer
    create_serializer_class = UserCreateSerializer
    update_serializer_class = UserUpdateSerializer
    detail_serializer_class = UserDetailSerializer
    permission_classes = [CasbinPermission]
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'create':
            return self.create_serializer_class
        elif self.action in ['update', 'partial_update']:
            return self.update_serializer_class
        elif self.action == 'retrieve':
            return self.detail_serializer_class
        return self.serializer_class
    
    def get_queryset(self):
        """获取用户查询集"""
        queryset = User.objects.select_related('department').prefetch_related('userrole_set__role')
        
        # 应用数据权限过滤
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # 对于User模型，使用自定义过滤逻辑
            user = self.request.user
            if user.is_superuser:
                return queryset
            else:
                # 根据用户的数据权限范围过滤
                # 优先使用角色的数据权限，如果没有角色则使用用户的数据权限
                data_scope = getattr(user, 'data_scope', 4)
                
                # 获取用户角色的最高数据权限
                from ..models import UserRole
                user_roles = UserRole.objects.filter(user=user).select_related('role')
                if user_roles.exists():
                    # 取角色中最高的数据权限（数字越小权限越高）
                    role_data_scopes = [ur.role.data_scope for ur in user_roles]
                    data_scope = min(role_data_scopes)
                if data_scope == 1:  # 全部数据
                    return queryset
                elif data_scope == 2:  # 本部门及以下数据
                    user_dept = getattr(user, 'department', None)
                    if not user_dept:
                        return queryset.none()
                    dept_ids = [user_dept.id] + [child.id for child in user_dept.get_all_children()]
                    return queryset.filter(department_id__in=dept_ids)
                elif data_scope == 3:  # 本部门数据
                    user_dept = getattr(user, 'department', None)
                    if not user_dept:
                        return queryset.none()
                    return queryset.filter(department=user_dept)
                else:  # 本人数据
                    return queryset.filter(id=user.id)
        
        return queryset.none()
    
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """重置用户密码"""
        user = self.get_object()
        serializer = UserPasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user)
            return ApiResponse.success(message="密码重置成功")
        else:
            return ApiResponse.error(message="密码重置失败", data=serializer.errors)
    
    @action(detail=True, methods=['post'], url_path='set_custom_scope')
    def set_custom_scope(self, request, pk=None):
        """设置用户自定义数据权限"""
        user = self.get_object()
        data_scope = request.data.get('data_scope')
        
        if data_scope is None:
            return ApiResponse.error(message="无效的数据权限值")
        
        if data_scope not in [1, 2, 3, 4]:
            return ApiResponse.error(message="无效的数据权限值")
        
        user.data_scope = data_scope
        user.save()
        
        return ApiResponse.success(message="数据权限设置成功")
