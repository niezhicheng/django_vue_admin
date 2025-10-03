"""
角色相关序列化器
"""
from rest_framework import serializers
from ..models import Role, UserRole


class RoleListSerializer(serializers.ModelSerializer):
    """角色列表序列化器"""
    data_scope_display = serializers.CharField(read_only=True)
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'role_id', 'name', 'code', 'description',
            'data_scope', 'data_scope_display', 'is_active',
            'user_count', 'created_at', 'updated_at'
        ]
    
    def get_user_count(self, obj):
        """获取用户数量"""
        return obj.userrole_set.count()


class RoleDetailSerializer(serializers.ModelSerializer):
    """角色详情序列化器"""
    data_scope_display = serializers.CharField(read_only=True)
    user_count = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'role_id', 'name', 'code', 'description',
            'data_scope', 'data_scope_display', 'is_active',
            'user_count', 'users', 'created_at', 'updated_at'
        ]
    
    def get_user_count(self, obj):
        """获取用户数量"""
        return obj.userrole_set.count()
    
    def get_users(self, obj):
        """获取用户详细信息"""
        user_roles = obj.userrole_set.select_related('user').all()
        return [{'id': ur.user.id, 'username': ur.user.username, 'name': ur.user.get_full_name()} for ur in user_roles]


class RoleCreateSerializer(serializers.ModelSerializer):
    """角色创建序列化器"""
    
    class Meta:
        model = Role
        fields = [
            'role_id', 'name', 'code', 'description',
            'data_scope', 'is_active'
        ]
    
    def validate_role_id(self, value):
        """验证角色ID唯一性"""
        if Role.objects.filter(role_id=value).exists():
            raise serializers.ValidationError('角色ID已存在')
        return value
    
    def validate_name(self, value):
        """验证角色名称唯一性"""
        if Role.objects.filter(name=value).exists():
            raise serializers.ValidationError('角色名称已存在')
        return value
    
    def validate_code(self, value):
        """验证角色代码唯一性"""
        if Role.objects.filter(code=value).exists():
            raise serializers.ValidationError('角色代码已存在')
        return value


class RoleUpdateSerializer(serializers.ModelSerializer):
    """角色更新序列化器"""
    
    class Meta:
        model = Role
        fields = [
            'role_id', 'name', 'code', 'description',
            'data_scope', 'is_active'
        ]
    
    def validate_role_id(self, value):
        """验证角色ID唯一性"""
        if Role.objects.filter(role_id=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('角色ID已存在')
        return value
    
    def validate_name(self, value):
        """验证角色名称唯一性"""
        if Role.objects.filter(name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('角色名称已存在')
        return value
    
    def validate_code(self, value):
        """验证角色代码唯一性"""
        if Role.objects.filter(code=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('角色代码已存在')
        return value
