"""
权限相关模型
"""
from django.db import models
from django.utils import timezone


class PolicyRule(models.Model):
    """权限策略规则模型"""
    role_id = models.CharField(max_length=50, verbose_name='角色ID')
    path = models.CharField(max_length=200, default='', verbose_name='路径')
    method = models.CharField(max_length=10, verbose_name='请求方法')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'rbac_policy_rule'
        verbose_name = '权限策略规则'
        verbose_name_plural = '权限策略规则管理'
        unique_together = ['role_id', 'path', 'method']
        ordering = ['role_id', 'path']
    
    def __str__(self):
        return f"{self.role_id} - {self.method} {self.path}"
