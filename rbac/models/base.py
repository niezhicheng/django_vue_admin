"""
基础模型和权限管理
"""
from django.db import models
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


class DataPermissionModelManager(models.Manager):
    """
    数据权限管理器 - 用于过滤用户有权限访问的数据
    """
    
    def filter_queryset(self, queryset, user, id_field='id'):
        """
        根据用户权限过滤查询集
        
        Args:
            queryset: 要过滤的查询集
            user: 当前用户
            id_field: ID字段名，默认为'id'
        
        Returns:
            过滤后的查询集
        """
        if not user or user.is_anonymous:
            return queryset.none()
        
        # 超级用户可以看到所有数据
        if user.is_superuser:
            return queryset
        
        # 获取用户的数据权限范围
        data_scope = getattr(user, 'data_scope', 4)  # 默认为本人数据
        
        # 根据数据权限范围过滤
        if data_scope == 1:  # 全部数据
            return queryset
        elif data_scope == 2:  # 本部门及以下数据
            # 获取用户部门及其所有子部门
            user_dept = getattr(user, 'department', None)
            if not user_dept:
                return queryset.filter(**{f'{id_field}__in': []})
            
            # 获取部门及其子部门ID列表
            dept_ids = [user_dept.id] + [child.id for child in user_dept.get_all_children()]
            return queryset.filter(owner_department_id__in=dept_ids)
        elif data_scope == 3:  # 本部门数据
            user_dept = getattr(user, 'department', None)
            if not user_dept:
                return queryset.filter(**{f'{id_field}__in': []})
            return queryset.filter(owner_department=user_dept)
        else:  # 本人数据 (data_scope == 4)
            return queryset.filter(created_by=user)
    
    def by_data_level(self, level):
        """按数据级别过滤"""
        return self.filter(data_level=level)


class DataPermissionManager:
    """
    数据权限管理器 - 用于处理复杂的数据权限逻辑
    """
    
    @staticmethod
    def filter_queryset(queryset, user, id_field='id'):
        """
        根据用户权限过滤查询集
        
        Args:
            queryset: 要过滤的查询集
            user: 当前用户
            id_field: ID字段名，默认为'id'
        
        Returns:
            过滤后的查询集
        """
        if not user or user.is_anonymous:
            return queryset.none()
        
        # 超级用户可以看到所有数据
        if user.is_superuser:
            return queryset
        
        # 获取用户的数据权限范围
        data_scope = getattr(user, 'data_scope', 4)  # 默认为本人数据
        
        # 根据数据权限范围过滤
        if data_scope == 1:  # 全部数据
            return queryset
        elif data_scope == 2:  # 本部门及以下数据
            # 获取用户部门及其所有子部门
            user_dept = getattr(user, 'department', None)
            if not user_dept:
                return queryset.filter(**{f'{id_field}__in': []})
            
            # 获取部门及其子部门ID列表
            dept_ids = [user_dept.id] + [child.id for child in user_dept.get_all_children()]
            return queryset.filter(owner_department_id__in=dept_ids)
        elif data_scope == 3:  # 本部门数据
            user_dept = getattr(user, 'department', None)
            if not user_dept:
                return queryset.filter(**{f'{id_field}__in': []})
            return queryset.filter(owner_department=user_dept)
        else:  # 本人数据 (data_scope == 4)
            return queryset.filter(created_by=user)
