"""
RBAC序列化器
"""
from rest_framework import serializers, viewsets
from .models import User, Role, Department, Menu, RoleMenu, ApiGroup, Api, ApiLog


class MultiSerializerMixin:
    """
    多序列化器混入类
    支持不同操作使用不同的序列化器
    
    使用方式：
    class MyViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
        model = MyModel
        serializer_class = MyListSerializer  # 默认序列化器（用于list和retrieve）
        create_serializer_class = MyCreateSerializer  # 创建时使用
        update_serializer_class = MyUpdateSerializer  # 更新时使用
        detail_serializer_class = MyDetailSerializer  # 详情时使用（可选）
    """
    
    def get_serializer_class(self):
        """根据操作类型返回对应的序列化器"""
        action = self.action
        
        # 按优先级查找序列化器
        if action == 'create' and hasattr(self, 'create_serializer_class'):
            return self.create_serializer_class
        elif action in ['update', 'partial_update'] and hasattr(self, 'update_serializer_class'):
            return self.update_serializer_class
        elif action == 'retrieve' and hasattr(self, 'detail_serializer_class'):
            return self.detail_serializer_class
        elif action == 'list' and hasattr(self, 'list_serializer_class'):
            return self.list_serializer_class
        elif hasattr(self, 'serializer_class'):
            return self.serializer_class
        else:
            raise AssertionError(
                f"'{self.__class__.__name__}' should either include a `serializer_class` attribute, "
                f"or define specific serializer classes like `create_serializer_class`, "
                f"`update_serializer_class`, etc."
            )


class BaseModelViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """
    基础模型视图集
    提供更简洁的配置方式
    
    使用方式：
    class MyViewSet(BaseModelViewSet):
        model = MyModel
        serializer_class = MyListSerializer
        create_serializer_class = MyCreateSerializer
        update_serializer_class = MyUpdateSerializer
        detail_serializer_class = MyDetailSerializer
        
        # 可选配置
        permission_classes = [IsAuthenticated]
        filter_fields = ['name', 'status']
        search_fields = ['name', 'description']
        ordering_fields = ['created_at', 'updated_at']
        ordering = ['-created_at']
    """
    
    def get_queryset(self):
        """获取查询集"""
        if hasattr(self, 'model'):
            return self.model.objects.all()
        return super().get_queryset()
    
    def get_permissions(self):
        """获取权限类"""
        if hasattr(self, 'permission_classes'):
            return [permission() for permission in self.permission_classes]
        return super().get_permissions()


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器（用于列表查询）"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    roles_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser',
            'department', 'department_name', 'custom_data_scope',
            'roles_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles_display(self, obj):
        """获取角色显示名称"""
        return [role.name for role in obj.roles.all()]


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情序列化器（用于详情查询）"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    roles_display = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser',
            'department', 'department_name', 'custom_data_scope',
            'roles', 'roles_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles_display(self, obj):
        """获取角色显示名称"""
        return [role.name for role in obj.roles.all()]
    
    def get_roles(self, obj):
        """获取角色详细信息"""
        return [{'id': role.id, 'name': role.name, 'code': role.code} for role in obj.roles.all()]


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, required=False)
    roles = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser',
            'department', 'custom_data_scope', 'password', 'password_confirm', 'roles'
        ]
    
    def validate(self, attrs):
        """验证密码确认"""
        password_confirm = attrs.get('password_confirm')
        if password_confirm and attrs['password'] != password_confirm:
            raise serializers.ValidationError("密码和确认密码不匹配")
        return attrs
    
    def create(self, validated_data):
        """创建用户"""
        validated_data.pop('password_confirm', None)  # 安全地移除password_confirm
        roles_data = validated_data.pop('roles', [])  # 获取角色ID列表
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # 分配角色
        if roles_data:
            from .models import UserRole
            for role_id in roles_data:
                UserRole.objects.get_or_create(user=user, role_id=role_id)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器（不包含密码字段）"""
    roles = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser',
            'department', 'custom_data_scope', 'roles'
        ]
    
    def update(self, instance, validated_data):
        """更新用户"""
        roles_data = validated_data.pop('roles', None)  # 获取角色ID列表
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # 更新角色分配
        if roles_data is not None:  # 只有当roles字段被提供时才更新
            from .models import UserRole
            # 删除现有角色
            UserRole.objects.filter(user=instance).delete()
            # 添加新角色
            for role_id in roles_data:
                UserRole.objects.get_or_create(user=instance, role_id=role_id)
        
        return instance


class UserPasswordResetSerializer(serializers.Serializer):
    """用户密码重置序列化器"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """验证密码确认"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码和确认密码不匹配")
        return attrs
    
    def save(self, user):
        """重置用户密码"""
        password = self.validated_data['password']
        user.set_password(password)
        user.save()
        return user


# 保持向后兼容
UserSerializer = UserListSerializer


class RoleListSerializer(serializers.ModelSerializer):
    """角色列表序列化器（用于列表查询）"""
    data_scope_display = serializers.CharField(source='get_data_scope_display', read_only=True)
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'role_id', 'name', 'code', 'description', 
            'data_scope', 'data_scope_display', 'is_active',
            'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        """获取用户数量"""
        return obj.users.count()


class RoleDetailSerializer(serializers.ModelSerializer):
    """角色详情序列化器（用于详情查询）"""
    data_scope_display = serializers.CharField(source='get_data_scope_display', read_only=True)
    user_count = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'role_id', 'name', 'code', 'description', 
            'data_scope', 'data_scope_display', 'is_active',
            'user_count', 'users', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
            raise serializers.ValidationError("角色ID已存在")
        return value
    
    def validate_name(self, value):
        """验证角色名称唯一性"""
        if Role.objects.filter(name=value).exists():
            raise serializers.ValidationError("角色名称已存在")
        return value
    
    def validate_code(self, value):
        """验证角色编码唯一性"""
        if Role.objects.filter(code=value).exists():
            raise serializers.ValidationError("角色编码已存在")
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
        if Role.objects.filter(role_id=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("角色ID已存在")
        return value
    
    def validate_name(self, value):
        """验证角色名称唯一性"""
        if Role.objects.filter(name=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("角色名称已存在")
        return value
    
    def validate_code(self, value):
        """验证角色编码唯一性"""
        if Role.objects.filter(code=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("角色编码已存在")
        return value


# 保持向后兼容
RoleSerializer = RoleListSerializer


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'parent', 'parent_name',
            'manager', 'phone', 'email', 'sort_order', 'is_active',
            'children_count', 'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children_count(self, obj):
        """获取子部门数量"""
        return obj.children.count()
    
    def get_user_count(self, obj):
        """获取用户数量"""
        return obj.users.count()


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    menu_type_display = serializers.CharField(source='get_menu_type_display', read_only=True)
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True)
    children_count = serializers.SerializerMethodField()
    breadcrumb = serializers.SerializerMethodField()
    
    class Meta:
        model = Menu
        fields = [
            'id', 'name', 'title', 'icon', 'path', 'component', 'redirect',
            'menu_type', 'menu_type_display', 'permission_code',
            'parent_id', 'parent_title', 'sort_order', 'is_hidden',
            'is_keep_alive', 'is_affix', 'is_frame', 'frame_src',
            'visible', 'status', 'children_count', 'breadcrumb', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children_count(self, obj):
        """获取子菜单数量"""
        return obj.children.count()
    
    def get_breadcrumb(self, obj):
        """获取面包屑导航"""
        breadcrumb = [obj.title]
        parent = obj.parent
        while parent:
            breadcrumb.insert(0, parent.title)
            parent = parent.parent
        return breadcrumb


class ApiGroupSerializer(serializers.ModelSerializer):
    """API分组序列化器"""
    api_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ApiGroup
        fields = [
            'id', 'name', 'description', 'sort_order', 'is_active',
            'api_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_api_count(self, obj):
        """获取API数量"""
        return obj.api_set.count()


class ApiSerializer(serializers.ModelSerializer):
    """API序列化器"""
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    roles_from_casbin = serializers.SerializerMethodField()
    
    class Meta:
        model = Api
        fields = [
            'id', 'name', 'path', 'method', 'method_display', 'description',
            'group', 'group_name', 'require_auth', 'require_permission',
            'status', 'status_display', 'is_public', 'roles_from_casbin',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles_from_casbin(self, obj):
        """从Casbin PolicyRule表获取关联的角色"""
        return obj.get_roles_from_casbin()


class ApiLogSerializer(serializers.ModelSerializer):
    """API日志序列化器"""
    api_name = serializers.CharField(source='api.name', read_only=True)
    api_path = serializers.CharField(source='api.path', read_only=True)
    api_method = serializers.CharField(source='api.method', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    log_type_display = serializers.CharField(source='get_log_type_display', read_only=True)
    
    class Meta:
        model = ApiLog
        fields = [
            'id', 'api', 'api_name', 'api_path', 'api_method',
            'user', 'user_name', 'method', 'path', 'ip_address',
            'user_agent', 'request_data', 'response_data',
            'status_code', 'response_time', 'log_type',
            'log_type_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RoleMenuSerializer(serializers.ModelSerializer):
    """角色菜单关联序列化器"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    menu_title = serializers.CharField(source='menu.title', read_only=True)
    
    class Meta:
        model = RoleMenu
        fields = ['id', 'role', 'role_name', 'menu', 'menu_title', 'created_at']
        read_only_fields = ['id', 'created_at']
