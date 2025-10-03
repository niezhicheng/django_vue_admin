"""
业务示例Admin - 展示如何使用数据权限基础Admin

这个文件展示了如何在Django Admin中使用数据权限：
1. 继承 BaseDataPermissionAdmin
2. 自动根据用户权限过滤数据
3. 自动设置创建人、更新人等审计字段
4. 统一的字段组织结构
"""
from django.contrib import admin
from rbac.base_views import BaseDataPermissionAdmin
from .models import Article, Project, Document, Task


@admin.register(Article)
class ArticleAdmin(BaseDataPermissionAdmin, admin.ModelAdmin):
    """
    文章管理 - 展示内容管理的数据权限使用
    
    功能特点：
    - 自动根据用户数据权限过滤文章列表
    - 创建时自动设置创建人和所属部门
    - 提供丰富的筛选和搜索功能
    """
    list_display = [
        'title', 'category', 'status', 'view_count', 
        'owner_department', 'created_by', 'is_public', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'owner_department', 
        'is_public', 'data_level', 'created_at'
    ]
    search_fields = ['title', 'content', 'tags']
    ordering = ['-created_at']
    
    # 基础字段组
    fieldsets = [
        ('基本信息', {
            'fields': ('title', 'content', 'category', 'tags')
        }),
        ('状态信息', {
            'fields': ('status',)
        }),
        ('统计信息', {
            'fields': ('view_count',),
            'classes': ['collapse']
        }),
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """动态设置只读字段"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        # 非创建者不能修改标题和内容（示例业务逻辑）
        if obj and obj.created_by != request.user and not request.user.is_superuser:
            readonly.extend(['title', 'content'])
        
        return readonly


@admin.register(Project)
class ProjectAdmin(BaseDataPermissionAdmin, admin.ModelAdmin):
    """
    项目管理 - 展示项目管理的数据权限使用
    
    功能特点：
    - 项目按部门和权限过滤
    - 项目状态和优先级管理
    - 预算和进度跟踪
    """
    list_display = [
        'name', 'status', 'priority', 'progress', 'start_date', 
        'budget', 'owner_department', 'created_by'
    ]
    list_filter = [
        'status', 'priority', 'owner_department', 
        'is_public', 'data_level', 'start_date'
    ]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = [
        ('基本信息', {
            'fields': ('name', 'description')
        }),
        ('项目详情', {
            'fields': ('start_date', 'end_date', 'budget', 'status', 'priority', 'progress')
        }),
    ]
    
    def get_queryset(self, request):
        """项目特殊的查询逻辑"""
        qs = super().get_queryset(request)
        
        # 项目经理可以看到更多项目（示例逻辑）
        if hasattr(request.user, 'position') and '经理' in (request.user.position or ''):
            return qs  # 项目经理看到更多
        
        return qs


@admin.register(Document)
class DocumentAdmin(BaseDataPermissionAdmin, admin.ModelAdmin):
    """
    文档管理 - 展示文档管理的数据权限使用
    
    功能特点：
    - 文档按权限级别过滤
    - 文件类型和版本管理
    - 下载统计
    """
    list_display = [
        'title', 'file_type', 'version', 'file_size_display', 
        'download_count', 'owner_department', 'created_by', 'data_level'
    ]
    list_filter = [
        'file_type', 'data_level', 'owner_department', 
        'is_public', 'created_at'
    ]
    search_fields = ['title', 'summary', 'file_path']
    ordering = ['-created_at']
    
    fieldsets = [
        ('基本信息', {
            'fields': ('title', 'summary')
        }),
        ('文件信息', {
            'fields': ('file_path', 'file_size', 'file_type', 'version')
        }),
        ('统计信息', {
            'fields': ('download_count',),
            'classes': ['collapse']
        }),
    ]
    
    def file_size_display(self, obj):
        """友好显示文件大小"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    file_size_display.short_description = '文件大小'


@admin.register(Task)
class TaskAdmin(BaseDataPermissionAdmin, admin.ModelAdmin):
    """
    任务管理 - 展示任务管理的数据权限使用
    
    功能特点：
    - 任务按创建者和指派人过滤
    - 任务状态流转管理
    - 工时统计
    """
    list_display = [
        'title', 'status', 'priority', 'assigned_to', 
        'due_date', 'estimated_hours', 'actual_hours', 'created_by'
    ]
    list_filter = [
        'status', 'priority', 'assigned_to', 
        'owner_department', 'due_date', 'created_at'
    ]
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'due_date'
    
    fieldsets = [
        ('基本信息', {
            'fields': ('title', 'description', 'assigned_to')
        }),
        ('时间管理', {
            'fields': ('due_date', 'estimated_hours', 'actual_hours')
        }),
        ('状态信息', {
            'fields': ('status', 'priority')
        }),
    ]
    
    def get_queryset(self, request):
        """任务特殊的查询逻辑"""
        from django.db.models import Q
        
        qs = super().get_queryset(request)
        
        # 除了基础权限外，还可以看到指派给自己的任务
        if not request.user.is_superuser:
            additional_filter = Q(assigned_to=request.user)
            qs = qs.filter(additional_filter) | qs
        
        return qs.distinct()
    
    def save_model(self, request, obj, form, change):
        """任务保存时的特殊逻辑"""
        # 如果没有指派人，默认指派给创建者
        if not change and not obj.assigned_to:
            obj.assigned_to = request.user
        
        super().save_model(request, obj, form, change)