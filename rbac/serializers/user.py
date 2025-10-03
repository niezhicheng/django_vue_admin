"""
用户相关序列化器
"""
from rest_framework import serializers
from ..models import User, UserRole


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone',
            'department', 'department_name', 'data_scope', 'is_active',
            'last_login', 'date_joined', 'roles'
        ]
    
    def get_department(self, obj):
        """获取部门信息"""
        if obj.department:
            return {
                'id': obj.department.id,
                'name': obj.department.name
            }
        return None
    
    def get_roles(self, obj):
        """获取用户角色"""
        return [{'id': ur.role.id, 'name': ur.role.name, 'code': ur.role.code, 'data_scope': ur.role.data_scope} 
                for ur in obj.userrole_set.select_related('role').all()]


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情序列化器"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone',
            'department', 'department_name', 'data_scope', 'is_active',
            'last_login', 'date_joined', 'roles'
        ]
    
    def get_roles(self, obj):
        """获取用户角色详细信息"""
        return [{'id': ur.role.id, 'name': ur.role.name, 'code': ur.role.code, 'description': ur.role.description, 'data_scope': ur.role.data_scope} 
                for ur in obj.userrole_set.select_related('role').all()]


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password_confirm = serializers.CharField(write_only=True, required=False)
    roles = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'password', 'password_confirm', 'department', 'data_scope',
            'is_active', 'roles'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, attrs):
        """验证密码确认"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError({'password_confirm': '两次输入的密码不一致'})
        
        return attrs
    
    def create(self, validated_data):
        """创建用户"""
        roles_data = validated_data.pop('roles', [])
        password_confirm = validated_data.pop('password_confirm', None)
        
        user = User.objects.create_user(**validated_data)
        
        # 分配角色
        if roles_data:
            from ..simple_rbac import simple_rbac_manager
            for role_id in roles_data:
                UserRole.objects.create(user=user, role_id=role_id)
                # 同步到Casbin
                role = UserRole.objects.get(user=user, role_id=role_id).role
                simple_rbac_manager.add_user_role(user.username, role.role_id)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器"""
    roles = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'department', 'data_scope', 'is_active', 'roles'
        ]
    
    def update(self, instance, validated_data):
        """更新用户"""
        roles_data = validated_data.pop('roles', None)
        
        # 更新用户基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新角色
        if roles_data is not None:
            from ..simple_rbac import simple_rbac_manager
            from ..models import Role
            
            # 删除现有角色（先同步到Casbin）
            for user_role in instance.userrole_set.all():
                simple_rbac_manager.remove_user_role(instance.username, user_role.role.role_id)
            instance.userrole_set.all().delete()
            
            # 添加新角色
            for role_id in roles_data:
                UserRole.objects.create(user=instance, role_id=role_id)
                # 同步到Casbin
                role = Role.objects.get(id=role_id)
                simple_rbac_manager.add_user_role(instance.username, role.role_id)
        
        return instance


class UserPasswordResetSerializer(serializers.Serializer):
    """用户密码重置序列化器"""
    password = serializers.CharField(min_length=6, write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """验证密码确认"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({'password_confirm': '两次输入的密码不一致'})
        
        return attrs
    
    def save(self, user):
        """保存新密码"""
        user.set_password(self.validated_data['password'])
        user.save()
        return user
