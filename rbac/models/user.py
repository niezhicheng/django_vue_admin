"""
用户相关模型
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """用户模型"""
    # 扩展用户字段
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    department = models.ForeignKey(
        'rbac.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users', verbose_name='所属部门'
    )
    
    # 数据权限相关字段
    data_scope = models.IntegerField(
        choices=[
            (1, '全部数据'),
            (2, '本部门及以下数据'),
            (3, '本部门数据'),
            (4, '本人数据'),
        ],
        default=4, verbose_name='数据权限'
    )
    
    # 用户状态
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    last_login_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='最后登录IP')
    last_login_time = models.DateTimeField(blank=True, null=True, verbose_name='最后登录时间')
    
    class Meta:
        db_table = 'rbac_user'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username}({self.get_full_name()})"
    
    def get_full_name(self):
        """获取用户全名"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_short_name(self):
        """获取用户简称"""
        return self.first_name or self.username


class UserRole(models.Model):
    """用户角色关联模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, verbose_name='角色')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='分配时间')
    
    class Meta:
        db_table = 'rbac_user_role'
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色管理'
        unique_together = ['user', 'role']
        
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
