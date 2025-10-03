"""
API相关视图
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import ApiGroup, Api
from ..serializers import ApiGroupSerializer, ApiSerializer
from ..utils import ApiResponse
from ..permissions import CasbinPermission


class ApiGroupViewSet(viewsets.ModelViewSet):
    """API分组管理视图集"""
    model = ApiGroup
    serializer_class = ApiGroupSerializer
    permission_classes = [CasbinPermission]
    
    def get_queryset(self):
        """获取API分组查询集"""
        return ApiGroup.objects.filter(is_active=True).order_by('sort_order', 'created_at')


class ApiViewSet(viewsets.ModelViewSet):
    """API管理视图集"""
    model = Api
    serializer_class = ApiSerializer
    permission_classes = [CasbinPermission]
    
    def get_queryset(self):
        """获取API查询集"""
        return Api.objects.filter(is_active=True).select_related('group').order_by('group', 'path')
