"""
基础序列化器和视图集
"""
from rest_framework import serializers, viewsets


class MultiSerializerMixin:
    """
    多序列化器混入类 - 允许为不同的操作使用不同的序列化器
    """
    def get_serializer_class(self):
        """
        根据操作类型返回对应的序列化器类
        """
        if self.action == 'create' and hasattr(self, 'create_serializer_class'):
            return self.create_serializer_class
        elif self.action in ['update', 'partial_update'] and hasattr(self, 'update_serializer_class'):
            return self.update_serializer_class
        elif self.action == 'retrieve' and hasattr(self, 'detail_serializer_class'):
            return self.detail_serializer_class
        elif self.action == 'list' and hasattr(self, 'list_serializer_class'):
            return self.list_serializer_class
        return super().get_serializer_class()


class BaseModelViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """
    基础模型视图集 - 支持多序列化器和自动权限设置
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'model'):
            self.queryset = self.model.objects.all()
            self.permission_classes = [self.permission_classes[0]] if self.permission_classes else []
