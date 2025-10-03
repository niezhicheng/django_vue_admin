"""
API相关序列化器
"""
from rest_framework import serializers
from ..models import ApiGroup, Api, ApiLog


class ApiGroupSerializer(serializers.ModelSerializer):
    """API分组序列化器"""
    apis_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ApiGroup
        fields = [
            'id', 'name', 'description', 'sort_order',
            'is_active', 'apis_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_apis_count(self, obj):
        """获取API数量"""
        return obj.apis.count()


class ApiSerializer(serializers.ModelSerializer):
    """API序列化器"""
    method_display = serializers.CharField(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = Api
        fields = [
            'id', 'name', 'path', 'method', 'method_display',
            'description', 'group', 'group_name', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApiLogSerializer(serializers.ModelSerializer):
    """API日志序列化器"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    api_name = serializers.CharField(source='api.name', read_only=True)
    
    class Meta:
        model = ApiLog
        fields = [
            'id', 'user', 'user_username', 'api', 'api_name',
            'method', 'path', 'ip_address', 'user_agent',
            'request_data', 'response_data', 'status_code',
            'response_time', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
