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
    
    def create(self, validated_data):
        """创建部门时处理parent字段"""
        parent_id = self.initial_data.get('parent')
        if parent_id:
            try:
                parent_dept = Department.objects.get(id=parent_id)
                validated_data['parent'] = parent_dept
                # 自动设置层级
                validated_data['level'] = parent_dept.level + 1
            except Department.DoesNotExist:
                pass
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新部门时处理parent字段"""
        parent_id = self.initial_data.get('parent')
        if parent_id is not None:
            if parent_id:
                try:
                    parent_dept = Department.objects.get(id=parent_id)
                    validated_data['parent'] = parent_dept
                    # 自动设置层级
                    validated_data['level'] = parent_dept.level + 1
                except Department.DoesNotExist:
                    pass
            else:
                validated_data['parent'] = None
                validated_data['level'] = 1
        return super().update(instance, validated_data)
    
    def get_children_count(self, obj):
        """获取子部门数量"""
        return obj.children.count()
    
    def get_user_count(self, obj):
        """获取用户数量"""
        return obj.users.count()
