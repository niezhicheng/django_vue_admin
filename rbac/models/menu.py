"""
菜单相关模型
"""
from django.db import models
from django.utils import timezone


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

    @property
    def menu_type_display(self):
        """菜单类型显示名称"""
        return dict(self.MENU_TYPE_CHOICES).get(self.menu_type, '未知')


class RoleMenu(models.Model):
    """角色菜单关联模型"""
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, verbose_name='角色')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name='菜单')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='分配时间')
    
    class Meta:
        db_table = 'rbac_role_menu'
        verbose_name = '角色菜单'
        verbose_name_plural = '角色菜单管理'
        unique_together = ['role', 'menu']
        
    def __str__(self):
        return f"{self.role.name} - {self.menu.title}"
