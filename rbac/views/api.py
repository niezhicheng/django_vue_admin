"""
API相关视图
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

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
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """获取API查询集"""
        return Api.objects.filter(is_active=True).select_related('group').order_by('group', 'path')
    
    def list(self, request, *args, **kwargs):
        """重写list方法，支持动态page_size"""
        # 获取page_size参数，如果没有则使用默认值
        page_size = request.query_params.get('page_size')
        if page_size:
            try:
                page_size = int(page_size)
                # 限制最大page_size为1000，防止性能问题
                if page_size > 1000:
                    page_size = 1000
                # 临时设置分页大小
                self.pagination_class.page_size = page_size
            except ValueError:
                pass
        
        return super().list(request, *args, **kwargs)
