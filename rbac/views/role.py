"""
角色相关视图
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Role
from ..serializers import (
    RoleListSerializer, RoleDetailSerializer, RoleCreateSerializer,
    RoleUpdateSerializer
)
from ..utils import ApiResponse
from ..permissions import CasbinPermission


class RoleViewSet(viewsets.ModelViewSet):
    """角色管理视图集"""
    queryset = Role.objects.all()
    serializer_class = RoleListSerializer
    permission_classes = [CasbinPermission]
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'create':
            return RoleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RoleUpdateSerializer
        elif self.action == 'retrieve':
            return RoleDetailSerializer
        return RoleListSerializer
    
    @action(detail=True, methods=['get'], url_path='get-api-permissions')
    def get_api_permissions(self, request, pk=None):
        """获取角色的API权限"""
        role = self.get_object()
        
        # 获取角色的权限策略
        from ..models import PolicyRule
        policies = PolicyRule.objects.filter(role_id=role.role_id)
        
        # 获取API信息
        from ..models import Api
        apis = []
        for policy in policies:
            # 模糊匹配API路径
            matching_apis = Api.objects.filter(
                path__icontains=policy.path.replace('*', ''),
                method__iexact=policy.method
            )
            for api in matching_apis:
                apis.append({
                    'id': api.id,
                    'name': api.name,
                    'path': api.path,
                    'method': api.method,
                    'description': api.description or 'API已删除或不存在'
                })
        
        return ApiResponse.success(data=apis, message="获取API权限成功")
    
    @action(detail=True, methods=['post'], url_path='assign-api-permissions')
    def assign_api_permissions(self, request, pk=None):
        """分配角色的API权限"""
        role = self.get_object()
        api_ids = request.data.get('api_ids', [])
        
        # 去重
        api_ids = list(set(api_ids))
        
        # 删除现有权限
        from ..models import PolicyRule
        from ..simple_rbac import simple_rbac_manager
        
        # 先获取现有权限，然后同步删除到Casbin
        existing_policies = PolicyRule.objects.filter(role_id=role.role_id)
        for policy in existing_policies:
            # 同步删除到Casbin
            simple_rbac_manager.sync_policy_to_casbin(role.role_id, policy.path, policy.method, 'remove')
        
        # 删除数据库中的权限
        PolicyRule.objects.filter(role_id=role.role_id).delete()
        
        # 添加新权限
        from ..models import Api
        for api_id in api_ids:
            try:
                api = Api.objects.get(id=api_id)
                # 先保存到数据库
                PolicyRule.objects.create(
                    role_id=role.role_id,
                    path=api.path,
                    method=api.method
                )
                # 同步到Casbin
                simple_rbac_manager.sync_policy_to_casbin(role.role_id, api.path, api.method, 'add')
            except Api.DoesNotExist:
                continue
        
        # 权限更新后，强制重新加载Casbin权限策略
        simple_rbac_manager.reload_policies()
        
        return ApiResponse.success(message="API权限分配成功")
