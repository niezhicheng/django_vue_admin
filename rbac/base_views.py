"""
数据权限基础视图 - 所有业务ViewSet都应该继承这些基础类
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from .models import DataPermissionManager
from .response import ApiResponse


class BaseDataPermissionViewSet(viewsets.ModelViewSet):
    """
    数据权限基础ViewSet - 所有业务ViewSet都应该继承此类
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """根据用户数据权限过滤查询集"""
        queryset = super().get_queryset()
        return DataPermissionManager.filter_queryset(queryset, self.request.user)
    
    def perform_create(self, serializer):
        """创建时自动设置创建人和所属部门"""
        with transaction.atomic():
            # 设置创建人
            serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user,
                # 如果没有指定所属部门，使用创建人的部门
                owner_department=serializer.validated_data.get(
                    'owner_department', 
                    self.request.user.department
                )
            )
    
    def perform_update(self, serializer):
        """更新时自动设置更新人"""
        serializer.save(updated_by=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """重写list方法，返回统一格式"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return ApiResponse.success(data=serializer.data, message="获取数据成功")
        except Exception as e:
            return ApiResponse.server_error(f"获取数据失败: {str(e)}")
    
    def create(self, request, *args, **kwargs):
        """重写create方法，返回统一格式"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return ApiResponse.success(
                data=serializer.data, 
                message="创建成功",
                code=201
            )
        except Exception as e:
            return ApiResponse.validation_error(f"创建失败: {str(e)}")
    
    def retrieve(self, request, *args, **kwargs):
        """重写retrieve方法，返回统一格式"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            # 添加权限信息
            data = serializer.data
            if hasattr(instance, 'get_permission_scope'):
                data['permission_scope'] = instance.get_permission_scope()
            
            return ApiResponse.success(data=data, message="获取详情成功")
        except Exception as e:
            return ApiResponse.not_found(f"数据不存在: {str(e)}")
    
    def update(self, request, *args, **kwargs):
        """重写update方法，返回统一格式"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return ApiResponse.success(
                data=serializer.data, 
                message="更新成功"
            )
        except Exception as e:
            return ApiResponse.validation_error(f"更新失败: {str(e)}")
    
    def destroy(self, request, *args, **kwargs):
        """重写destroy方法，返回统一格式"""
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return ApiResponse.success(message="删除成功")
        except Exception as e:
            return ApiResponse.server_error(f"删除失败: {str(e)}")


class BaseDataPermissionAdmin:
    """
    数据权限基础Admin类 - 所有业务Admin都应该继承此类
    """
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        """管理后台也需要根据数据权限过滤"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return DataPermissionManager.filter_queryset(qs, request.user)
    
    def save_model(self, request, obj, form, change):
        """保存时自动设置创建人/更新人"""
        if not change:  # 新建
            obj.created_by = request.user
            obj.updated_by = request.user
            # 如果没有设置所属部门，使用创建人的部门
            if not obj.owner_department and request.user.department:
                obj.owner_department = request.user.department
        else:  # 更新
            obj.updated_by = request.user
        
        super().save_model(request, obj, form, change)
    
    def get_fieldsets(self, request, obj=None):
        """动态添加数据权限字段组"""
        fieldsets = list(super().get_fieldsets(request, obj) or [])
        
        # 添加数据权限字段组
        permission_fields = ('owner_department', 'is_public', 'data_level')
        audit_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
        
        fieldsets.extend([
            ('数据权限', {'fields': permission_fields}),
            ('审计信息', {'fields': audit_fields, 'classes': ['collapse']}),
        ])
        
        return fieldsets


# ===== 使用示例 =====

class BaseDataPermissionSerializer:
    """数据权限基础序列化器 Mixin"""
    
    def to_representation(self, instance):
        """添加权限信息到序列化结果"""
        data = super().to_representation(instance)
        
        # 添加权限范围信息
        if hasattr(instance, 'get_permission_scope'):
            data['permission_scope'] = instance.get_permission_scope()
        
        # 添加创建人信息
        if hasattr(instance, 'created_by') and instance.created_by:
            data['created_by_info'] = {
                'id': instance.created_by.id,
                'username': instance.created_by.username,
                'name': f"{instance.created_by.first_name} {instance.created_by.last_name}".strip() or instance.created_by.username,
            }
        
        # 添加部门信息
        if hasattr(instance, 'owner_department') and instance.owner_department:
            data['owner_department_info'] = {
                'id': instance.owner_department.id,
                'name': instance.owner_department.name,
                'code': instance.owner_department.code,
            }
        
        return data
