"""
API相关模型
"""
from django.db import models
from django.utils import timezone


class ApiGroup(models.Model):
    """API分组模型"""
    name = models.CharField(max_length=100, verbose_name='分组名称')
    description = models.TextField(blank=True, null=True, verbose_name='分组描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'rbac_api_group'
        verbose_name = 'API分组'
        verbose_name_plural = 'API分组管理'
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return self.name


class Api(models.Model):
    """API模型"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='API名称')
    path = models.CharField(max_length=200, verbose_name='API路径')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name='请求方法')
    description = models.TextField(blank=True, null=True, verbose_name='API描述')
    group = models.ForeignKey(ApiGroup, on_delete=models.CASCADE, related_name='apis', verbose_name='所属分组')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'rbac_api'
        verbose_name = 'API'
        verbose_name_plural = 'API管理'
        unique_together = ['path', 'method']
        ordering = ['group', 'path']
    
    def __str__(self):
        return f"{self.method} {self.path}"
    
    @property
    def method_display(self):
        """请求方法显示名称"""
        return dict(self.METHOD_CHOICES).get(self.method, self.method)


class ApiLog(models.Model):
    """API日志模型"""
    user = models.ForeignKey('rbac.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='用户')
    api = models.ForeignKey(Api, on_delete=models.CASCADE, verbose_name='API')
    method = models.CharField(max_length=10, verbose_name='请求方法')
    path = models.CharField(max_length=200, verbose_name='请求路径')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.TextField(blank=True, null=True, verbose_name='用户代理')
    request_data = models.TextField(blank=True, null=True, verbose_name='请求数据')
    response_data = models.TextField(blank=True, null=True, verbose_name='响应数据')
    status_code = models.IntegerField(verbose_name='状态码')
    response_time = models.FloatField(verbose_name='响应时间(秒)')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        db_table = 'rbac_api_log'
        verbose_name = 'API日志'
        verbose_name_plural = 'API日志管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"
