"""
部门相关模型
"""
from django.db import models
from django.utils import timezone


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
