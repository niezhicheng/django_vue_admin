"""
部门相关序列化器
"""
from rest_framework import serializers
from ..models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'parent', 'parent_name',
            'level', 'sort_order', 'leader', 'phone', 'email',
            'status', 'children_count', 'user_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children_count(self, obj):
        """获取子部门数量"""
        return obj.children.count()
    
    def get_user_count(self, obj):
        """获取用户数量"""
        return obj.users.count()
