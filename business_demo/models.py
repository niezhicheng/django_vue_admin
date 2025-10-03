"""
业务示例模型 - 展示如何使用RBAC的数据权限基础模型

这个app展示了如何在实际业务中使用数据权限系统：
1. 继承 BaseDataPermissionModel
2. 使用 DataPermissionModelManager
3. 自动获得完整的数据权限功能
"""
from django.db import models
from rbac.models import BaseDataPermissionModel, DataPermissionModelManager


class Article(BaseDataPermissionModel):
    """
    文章表 - 展示内容管理场景的数据权限使用
    
    业务场景：
    - 记者可以创建和编辑自己的文章
    - 编辑可以管理本部门的文章
    - 主编可以管理全部文章
    - 发布的文章可以设为公开，所有人可见
    """
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    category = models.CharField(max_length=50, verbose_name='分类')
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('review', '待审核'),
            ('published', '已发布'),
            ('archived', '已归档'),
        ],
        default='draft',
        verbose_name='状态'
    )
    view_count = models.IntegerField(default=0, verbose_name='浏览次数')
    tags = models.CharField(max_length=200, blank=True, verbose_name='标签')
    
    # 使用数据权限管理器
    objects = DataPermissionModelManager()
    
    class Meta:
        db_table = 'demo_article'
        verbose_name = '文章'
        verbose_name_plural = '文章管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Project(BaseDataPermissionModel):
    """
    项目表 - 展示项目管理场景的数据权限使用
    
    业务场景：
    - 项目成员只能查看自己参与的项目
    - 项目经理可以管理本部门的项目
    - 总监可以查看下属部门的项目
    - 重要项目可以设为机密，限制访问
    """
    name = models.CharField(max_length=100, verbose_name='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='预算')
    status = models.CharField(
        max_length=20,
        choices=[
            ('planning', '规划中'),
            ('in_progress', '进行中'),
            ('testing', '测试中'),
            ('completed', '已完成'),
            ('cancelled', '已取消'),
        ],
        default='planning',
        verbose_name='项目状态'
    )
    priority = models.IntegerField(
        choices=[
            (1, '低'),
            (2, '中'),
            (3, '高'),
            (4, '紧急'),
        ],
        default=2,
        verbose_name='优先级'
    )
    progress = models.IntegerField(default=0, verbose_name='进度百分比')
    
    # 使用数据权限管理器
    objects = DataPermissionModelManager()
    
    class Meta:
        db_table = 'demo_project'
        verbose_name = '项目'
        verbose_name_plural = '项目管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Document(BaseDataPermissionModel):
    """
    文档表 - 展示文档管理场景的数据权限使用
    
    业务场景：
    - 个人文档只有创建者可见
    - 部门文档部门内可见
    - 公开文档所有人可见
    - 机密文档需要特殊权限
    """
    title = models.CharField(max_length=200, verbose_name='文档标题')
    file_path = models.CharField(max_length=500, verbose_name='文件路径')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    file_type = models.CharField(max_length=20, verbose_name='文件类型')
    version = models.CharField(max_length=20, default='1.0', verbose_name='版本号')
    download_count = models.IntegerField(default=0, verbose_name='下载次数')
    summary = models.TextField(blank=True, verbose_name='文档摘要')
    
    # 使用数据权限管理器
    objects = DataPermissionModelManager()
    
    class Meta:
        db_table = 'demo_document'
        verbose_name = '文档'
        verbose_name_plural = '文档管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Task(BaseDataPermissionModel):
    """
    任务表 - 展示任务管理场景的数据权限使用
    
    业务场景：
    - 任务创建者和指派人员可以查看
    - 上级可以查看下属的任务
    - 团队任务团队成员可见
    """
    title = models.CharField(max_length=200, verbose_name='任务标题')
    description = models.TextField(blank=True, verbose_name='任务描述')
    assigned_to = models.ForeignKey(
        'rbac.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks',
        verbose_name='指派给'
    )
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    status = models.CharField(
        max_length=20,
        choices=[
            ('todo', '待办'),
            ('in_progress', '进行中'),
            ('review', '待审核'),
            ('completed', '已完成'),
            ('cancelled', '已取消'),
        ],
        default='todo',
        verbose_name='任务状态'
    )
    priority = models.IntegerField(
        choices=[
            (1, '低'),
            (2, '中'),
            (3, '高'),
            (4, '紧急'),
        ],
        default=2,
        verbose_name='优先级'
    )
    estimated_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='预估工时'
    )
    actual_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='实际工时'
    )
    
    # 使用数据权限管理器
    objects = DataPermissionModelManager()
    
    class Meta:
        db_table = 'demo_task'
        verbose_name = '任务'
        verbose_name_plural = '任务管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title