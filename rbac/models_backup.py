"""
简化的RBAC模型 - 只保留核心表
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class BaseDataPermissionModel(models.Model):
    """
    数据权限基础模型 - 所有需要数据权限控制的业务表都应该继承此模型
    """
    # 数据权限相关字段
    created_by = models.ForeignKey(
        'rbac.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_created', verbose_name='创建人'
    )
    updated_by = models.ForeignKey(
        'rbac.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_updated', verbose_name='更新人'
    )
    owner_department = models.ForeignKey(
        'rbac.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_owned', verbose_name='所属部门'
    )
    
    # 时间字段
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 数据权限控制字段
    is_public = models.BooleanField(default=False, verbose_name='是否公开数据')
    data_level = models.IntegerField(
        choices=[
            (1, '公开数据'),
            (2, '部门数据'), 
            (3, '私有数据'),
            (4, '机密数据'),
        ],
        default=2, verbose_name='数据级别'
    )
    
    class Meta:
        abstract = True  # 抽象模型，不会创建实际的数据库表
        
    def save(self, *args, **kwargs):
        """重写save方法，自动设置数据权限字段"""
        # 如果是新创建的记录且没有设置所属部门，自动设置为创建人的部门
        if not self.pk and not self.owner_department and self.created_by and self.created_by.department:
            self.owner_department = self.created_by.department
            
        super().save(*args, **kwargs)
    
    def get_permission_scope(self):
        """获取当前数据的权限范围信息"""
        return {
            'created_by': self.created_by.username if self.created_by else None,
            'owner_department': self.owner_department.name if self.owner_department else None,
            'is_public': self.is_public,
            'data_level': self.get_data_level_display(),
        }


class DataPermissionModelManager(models.Manager):
    """数据权限模型管理器"""
    
    def for_user(self, user):
        """根据用户权限过滤查询集"""
        return DataPermissionManager.filter_queryset(self.get_queryset(), user)
    
    def public_data(self):
        """获取公开数据"""
        return self.filter(is_public=True)
    
    def department_data(self, department):
        """获取部门数据"""
        return self.filter(owner_department=department)
    
    def by_data_level(self, level):
        """按数据级别过滤"""
        return self.filter(data_level=level)


class Department(models.Model):
    """部门模型"""
    name = models.CharField(max_length=100, verbose_name='部门名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              verbose_name='上级部门', related_name='children')
    level = models.IntegerField(default=1, verbose_name='层级')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    leader = models.CharField(max_length=50, blank=True, null=True, verbose_name='部门负责人')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='联系电话')
    email = models.EmailField(blank=True, null=True, verbose_name='邮箱')
    status = models.BooleanField(default=True, verbose_name='状态')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'rbac_department'
        verbose_name = '部门'
        verbose_name_plural = '部门管理'
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return self.name
    
    def get_children(self):
        """获取所有子部门"""
        return Department.objects.filter(parent=self, status=True)
    
    def get_all_children(self):
        """递归获取所有子部门"""
        children = []
        for child in self.get_children():
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def get_parent_path(self):
        """获取父级路径"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)


class User(AbstractUser):
    """用户模型"""
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    avatar = models.CharField(max_length=200, blank=True, null=True, verbose_name='头像URL')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='所属部门', related_name='users')
    position = models.CharField(max_length=50, blank=True, null=True, verbose_name='职位')
    # 用户级别的数据权限覆盖（可选）
    custom_data_scope = models.IntegerField(
        choices=[(1, '全部数据'), (2, '本部门及以下数据'), (3, '本部门数据'), (4, '本人数据')],
        null=True, blank=True, verbose_name='自定义数据权限'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
        
    def __str__(self):
        return self.username


class Role(models.Model):
    """角色模型"""
    # 数据权限选择
    DATA_SCOPE_CHOICES = [
        (1, '全部数据'),
        (2, '本部门及以下数据'),
        (3, '本部门数据'),
        (4, '本人数据'),
    ]
    
    role_id = models.CharField(max_length=50, unique=True, verbose_name='角色ID', default='0')  # 独立的角色ID
    name = models.CharField(max_length=50, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='角色编码')
    description = models.TextField(blank=True, null=True, verbose_name='角色描述')
    data_scope = models.IntegerField(choices=DATA_SCOPE_CHOICES, default=4, verbose_name='数据权限')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'rbac_role'
        verbose_name = '角色'
        verbose_name_plural = '角色管理'
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.name}({self.role_id})"


class UserRole(models.Model):
    """用户角色关联模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='分配时间')
    
    class Meta:
        db_table = 'rbac_user_role'
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色管理'
        unique_together = ['user', 'role']
        
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


# 权限策略存储（可选，用于动态权限）
class Menu(models.Model):
    """菜单模型"""
    MENU_TYPE_CHOICES = [
        (1, '目录'),
        (2, '菜单'), 
        (3, '按钮'),
    ]

    name = models.CharField(max_length=50, verbose_name='菜单名称')
    title = models.CharField(max_length=50, verbose_name='菜单标题')
    icon = models.CharField(max_length=100, blank=True, null=True, verbose_name='菜单图标')
    path = models.CharField(max_length=200, blank=True, null=True, verbose_name='路由路径')
    component = models.CharField(max_length=200, blank=True, null=True, verbose_name='组件路径')
    redirect = models.CharField(max_length=200, blank=True, null=True, verbose_name='重定向路径')
    menu_type = models.IntegerField(choices=MENU_TYPE_CHOICES, default=2, verbose_name='菜单类型')
    permission_code = models.CharField(max_length=100, blank=True, null=True, verbose_name='权限标识')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              verbose_name='上级菜单', related_name='children')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_hidden = models.BooleanField(default=False, verbose_name='是否隐藏')
    is_keep_alive = models.BooleanField(default=True, verbose_name='是否缓存')
    is_affix = models.BooleanField(default=False, verbose_name='是否固定标签')
    is_frame = models.BooleanField(default=False, verbose_name='是否外链')
    frame_src = models.CharField(max_length=500, blank=True, null=True, verbose_name='外链地址')
    visible = models.BooleanField(default=True, verbose_name='是否显示')
    status = models.BooleanField(default=True, verbose_name='状态')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'rbac_menu'
        verbose_name = '菜单'
        verbose_name_plural = '菜单管理'
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return self.title

    def get_children(self):
        """获取所有子菜单"""
        return Menu.objects.filter(parent=self, status=True, visible=True).order_by('sort_order')

    def get_all_children(self):
        """递归获取所有子菜单"""
        children = []
        for child in self.get_children():
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def get_breadcrumb(self):
        """获取面包屑路径"""
        breadcrumb = [self.title]
        parent = self.parent
        while parent:
            breadcrumb.insert(0, parent.title)
            parent = parent.parent
        return breadcrumb


class RoleMenu(models.Model):
    """角色菜单关联模型"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name='菜单')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='分配时间')

    class Meta:
        db_table = 'rbac_role_menu'
        verbose_name = '角色菜单'
        verbose_name_plural = '角色菜单管理'
        unique_together = ['role', 'menu']

    def __str__(self):
        return f"{self.role.name} - {self.menu.title}"


class ApiGroup(models.Model):
    """API分组"""
    name = models.CharField(max_length=100, verbose_name='分组名称')
    description = models.TextField(blank=True, verbose_name='分组描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'rbac_api_group'
        verbose_name = 'API分组'
        verbose_name_plural = 'API分组'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Api(models.Model):
    """API管理 - 纯粹管理API接口信息，不直接关联角色"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('OPTIONS', 'OPTIONS'),
        ('HEAD', 'HEAD'),
    ]
    
    STATUS_CHOICES = [
        (0, '禁用'),
        (1, '启用'),
    ]
    
    # 基本信息
    name = models.CharField(max_length=200, verbose_name='API名称')
    path = models.CharField(max_length=500, verbose_name='API路径')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name='请求方法')
    description = models.TextField(blank=True, verbose_name='API描述')
    
    # 分组
    group = models.ForeignKey(ApiGroup, on_delete=models.CASCADE, verbose_name='API分组')
    
    # 权限控制（通过Casbin PolicyRule表管理，这里只是标记）
    require_auth = models.BooleanField(default=True, verbose_name='需要认证')
    require_permission = models.BooleanField(default=True, verbose_name='需要权限')
    
    # 状态控制
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name='状态')
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    
    # 时间字段
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'rbac_api'
        verbose_name = 'API管理'
        verbose_name_plural = 'API管理'
        unique_together = ('path', 'method')
        ordering = ['group__sort_order', 'name']
    
    def __str__(self):
        return f"{self.method} {self.path}"
    
    @property
    def full_path(self):
        """完整路径"""
        return f"{self.method} {self.path}"
    
    def get_roles_from_casbin(self):
        """从Casbin PolicyRule表获取关联的角色"""
        from .models import PolicyRule
        policies = PolicyRule.objects.filter(
            url_pattern=self.path,
            method=self.method,
            is_active=True
        )
        return [policy.role_id for policy in policies]


class ApiLog(models.Model):
    """API访问日志"""
    LOG_TYPE_CHOICES = [
        ('request', '请求'),
        ('response', '响应'),
        ('error', '错误'),
    ]
    
    # 基本信息
    api = models.ForeignKey(Api, on_delete=models.CASCADE, verbose_name='API')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='用户')
    
    # 请求信息
    method = models.CharField(max_length=10, verbose_name='请求方法')
    path = models.CharField(max_length=500, verbose_name='请求路径')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    # 请求/响应数据
    request_data = models.JSONField(null=True, blank=True, verbose_name='请求数据')
    response_data = models.JSONField(null=True, blank=True, verbose_name='响应数据')
    
    # 状态信息
    status_code = models.IntegerField(verbose_name='状态码')
    response_time = models.FloatField(verbose_name='响应时间(ms)')
    
    # 日志类型
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES, default='request', verbose_name='日志类型')
    
    # 时间字段
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'rbac_api_log'
        verbose_name = 'API访问日志'
        verbose_name_plural = 'API访问日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"


class PolicyRule(models.Model):
    """权限策略规则"""
    role_id = models.CharField(max_length=50, verbose_name='角色ID', default='0')  # 使用角色ID
    url_pattern = models.CharField(max_length=200, verbose_name='URL模式')
    method = models.CharField(max_length=10, verbose_name='HTTP方法')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')

    class Meta:
        db_table = 'rbac_policy_rule'
        verbose_name = '权限策略'
        verbose_name_plural = '权限策略管理'
        unique_together = ['role_id', 'url_pattern', 'method']

    def __str__(self):
        return f"{self.role_id} -> {self.method} {self.url_pattern}"


class DataPermissionManager:
    """数据权限管理器"""
    
    @staticmethod
    def get_user_data_scope(user):
        """
        获取用户的数据权限范围 - 混合模式
        优先级：用户自定义权限 > 角色权限 > 默认权限
        """
        if not user or not user.is_authenticated:
            return 4, []  # 默认只能查看本人数据
        
        # 超级用户拥有全部数据权限
        if user.is_superuser:
            return 1, []
        
        # 1. 优先使用用户自定义数据权限
        if user.custom_data_scope is not None:
            scope = user.custom_data_scope
            department_ids = DataPermissionManager._get_accessible_departments(user, scope)
            return scope, department_ids
        
        # 2. 使用角色数据权限（取最高权限）
        user_roles = UserRole.objects.filter(user=user, role__is_active=True).select_related('role')
        if user_roles.exists():
            # 获取最高权限级别（数字越小权限越大）
            max_scope = min(role.role.data_scope for role in user_roles)
            department_ids = DataPermissionManager._get_accessible_departments(user, max_scope)
            return max_scope, department_ids
        
        # 3. 兜底：只能查看本人数据
        return 4, []
    
    @staticmethod
    def _get_accessible_departments(user, data_scope):
        """根据数据权限获取可访问的部门ID列表"""
        if data_scope == 1:  # 全部数据
            return []  # 空列表表示不限制部门
        
        if not user.department:
            return []  # 用户没有部门，返回空列表
        
        if data_scope == 2:  # 本部门及以下数据
            departments = [user.department]
            departments.extend(user.department.get_all_children())
            return [dept.id for dept in departments]
        
        elif data_scope == 3:  # 本部门数据
            return [user.department.id]
        
        elif data_scope == 4:  # 本人数据
            return []  # 特殊标记，需要在查询时过滤为当前用户
        
        return []
    
    @staticmethod
    def filter_queryset(queryset, user, user_field_name='created_by'):
        """
        根据用户数据权限过滤查询集（优化版，支持基础数据权限模型）
        
        Args:
            queryset: 要过滤的查询集
            user: 当前用户
            user_field_name: 模型中表示创建者的字段名，默认为'created_by'
        
        Returns:
            过滤后的查询集
        """
        data_scope, department_ids = DataPermissionManager.get_user_data_scope(user)
        
        if data_scope == 1:  # 全部数据
            return queryset
        
        # 检查模型是否继承自BaseDataPermissionModel
        is_base_model = hasattr(queryset.model, 'owner_department') and \
                       hasattr(queryset.model, 'is_public') and \
                       hasattr(queryset.model, 'data_level')
        
        if data_scope == 2 or data_scope == 3:  # 部门数据
            if not department_ids:
                return queryset.none()
            
            filters = models.Q()
            
            if is_base_model:
                # 基础模型的复合过滤逻辑
                filters |= models.Q(is_public=True)  # 公开数据
                filters |= models.Q(owner_department_id__in=department_ids)  # 本部门数据
                filters |= models.Q(**{f'{user_field_name}__department_id__in': department_ids})  # 创建者部门数据
                
                # 根据数据级别进一步过滤
                if data_scope == 3:  # 仅本部门
                    user_dept_id = user.department.id if user.department else None
                    if user_dept_id:
                        filters &= (
                            models.Q(is_public=True) |
                            models.Q(owner_department_id=user_dept_id) |
                            models.Q(**{f'{user_field_name}__department_id': user_dept_id})
                        )
                
                return queryset.filter(filters)
            else:
                # 传统模型的过滤逻辑
                if hasattr(queryset.model, 'department'):
                    return queryset.filter(department_id__in=department_ids)
                elif hasattr(queryset.model, 'user'):
                    return queryset.filter(user__department_id__in=department_ids)
                elif hasattr(queryset.model, user_field_name):
                    filter_dict = {f'{user_field_name}__department_id__in': department_ids}
                    return queryset.filter(**filter_dict)
                return queryset.none()
        
        elif data_scope == 4:  # 本人数据
            filters = models.Q()
            
            if is_base_model:
                # 基础模型：公开数据 + 本人创建的数据
                filters |= models.Q(is_public=True)
                filters |= models.Q(**{user_field_name: user})
                return queryset.filter(filters)
            else:
                # 传统模型
                if hasattr(queryset.model, user_field_name):
                    filter_dict = {user_field_name: user}
                    return queryset.filter(**filter_dict)
                elif hasattr(queryset.model, 'user'):
                    return queryset.filter(user=user)
                elif queryset.model == User:
                    return queryset.filter(id=user.id)
                return queryset.none()
        
        return queryset.none()
    
    @staticmethod
    def set_user_custom_scope(user, data_scope=None):
        """
        设置用户自定义数据权限
        
        Args:
            user: 用户对象
            data_scope: 数据权限级别，None表示清除自定义权限
        """
        user.custom_data_scope = data_scope
        user.save(update_fields=['custom_data_scope'])
        return user
    
    @staticmethod
    def get_permission_description(user):
        """获取用户权限描述"""
        data_scope, department_ids = DataPermissionManager.get_user_data_scope(user)
        
        scope_choices = {
            1: '全部数据',
            2: '本部门及以下数据', 
            3: '本部门数据',
            4: '本人数据'
        }
        
        desc = scope_choices.get(data_scope, '未知权限')
        
        # 权限来源
        if user.is_superuser:
            source = '超级用户'
        elif user.custom_data_scope is not None:
            source = '用户自定义'
        else:
            user_roles = UserRole.objects.filter(user=user, role__is_active=True).select_related('role')
            if user_roles.exists():
                role_names = [ur.role.name for ur in user_roles]
                source = f"角色权限({', '.join(role_names)})"
            else:
                source = '默认权限'
        
        return {
            'scope': data_scope,
            'scope_desc': desc,
            'source': source,
            'department_ids': department_ids,
            'department_count': len(department_ids) if department_ids else 0
        }


