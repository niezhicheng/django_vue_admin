"""
简化的RBAC管理界面
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserRole, PolicyRule, Department, Menu, RoleMenu, ApiGroup, Api, ApiLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """部门管理"""
    list_display = ['name', 'code', 'parent', 'level', 'leader', 'status', 'created_at']
    list_filter = ['status', 'level', 'parent', 'created_at']
    search_fields = ['name', 'code', 'leader']
    ordering = ['sort_order', 'level', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {'fields': ('name', 'code', 'parent', 'level', 'sort_order')}),
        ('联系信息', {'fields': ('leader', 'phone', 'email')}),
        ('状态信息', {'fields': ('status',)}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'department', 'phone', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'department', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('phone', 'avatar', 'department')}),
        ('数据权限', {'fields': ('data_scope',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('department')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理"""
    list_display = ['role_id', 'name', 'code', 'data_scope', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'data_scope', 'created_at']
    search_fields = ['role_id', 'name', 'code', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {'fields': ('role_id', 'name', 'code', 'description')}),
        ('权限设置', {'fields': ('data_scope',)}),
        ('状态信息', {'fields': ('is_active',)}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """用户角色关联管理"""
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'role__name']
    ordering = ['-created_at']
    autocomplete_fields = ['user', 'role']


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    """菜单管理"""
    list_display = ['title', 'name', 'menu_type', 'path', 'parent', 'sort_order', 'visible', 'status', 'created_at']
    list_filter = ['menu_type', 'visible', 'status', 'is_hidden', 'is_frame', 'created_at']
    search_fields = ['title', 'name', 'path', 'component', 'permission_code']
    ordering = ['sort_order', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'title', 'icon', 'menu_type', 'parent', 'sort_order')
        }),
        ('路由配置', {
            'fields': ('path', 'component', 'redirect', 'permission_code')
        }),
        ('显示设置', {
            'fields': ('visible', 'is_hidden', 'is_keep_alive', 'is_affix')
        }),
        ('外链设置', {
            'fields': ('is_frame', 'frame_src'),
            'classes': ('collapse',)
        }),
        ('状态信息', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


@admin.register(RoleMenu)
class RoleMenuAdmin(admin.ModelAdmin):
    """角色菜单关联管理"""
    list_display = ['role', 'menu', 'created_at']
    list_filter = ['role', 'menu__menu_type', 'created_at']
    search_fields = ['role__name', 'menu__title', 'menu__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['role', 'menu']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('role', 'menu')


@admin.register(ApiGroup)
class ApiGroupAdmin(admin.ModelAdmin):
    """API分组管理"""
    list_display = ['name', 'description', 'sort_order', 'is_active', 'api_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    def api_count(self, obj):
        return obj.api_set.count()
    api_count.short_description = 'API数量'


@admin.register(Api)
class ApiAdmin(admin.ModelAdmin):
    """API管理"""
    list_display = ['name', 'method', 'path', 'group', 'is_active', 'created_at']
    list_filter = ['method', 'is_active', 'group', 'created_at']
    search_fields = ['name', 'path', 'description']
    ordering = ['group__sort_order', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'path', 'method', 'description', 'group')
        }),
        ('状态信息', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(ApiLog)
class ApiLogAdmin(admin.ModelAdmin):
    """API日志管理"""
    list_display = ['api', 'method', 'path', 'user', 'status_code', 'response_time', 'ip_address', 'created_at']
    list_filter = ['method', 'status_code', 'created_at']
    search_fields = ['api__name', 'path', 'user__username', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # 禁止手动添加日志
    
    def has_change_permission(self, request, obj=None):
        return False  # 禁止修改日志
    
    def has_delete_permission(self, request, obj=None):
        return False  # 禁止删除日志
