"""
角色相关模型
"""
from django.db import models
from django.utils import timezone


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
    
    @property
    def data_scope_display(self):
        """数据权限显示名称"""
        return dict(self.DATA_SCOPE_CHOICES).get(self.data_scope, '未知')
