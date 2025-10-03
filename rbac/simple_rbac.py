import casbin
from django.conf import settings

# 最简单的权限检查 - 几行代码解决
def check_permission(user, url_path, method):
    """最简单的权限检查"""
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # 直接检查数据库中的权限
    from .models import UserRole, PolicyRule
    
    # 获取用户角色
    user_roles = UserRole.objects.filter(user=user, role__is_active=True).values_list('role__role_id', flat=True)
    
    # 检查是否有权限
    normalized_url = url_path.split('?')[0]  # 移除查询参数
    if not normalized_url.endswith('/') and normalized_url.startswith('/rbac/api/'):
        normalized_url += '/'
    
    return PolicyRule.objects.filter(
        role_id__in=user_roles,
        path=normalized_url,
        method=method.upper()
    ).exists()

# 最简单的权限类
class SimplePermission:
    def has_permission(self, request, view):
        return check_permission(request.user, request.path_info, request.method)

# 为了兼容现有代码，保留一些基础方法
def add_role_policy(role_id, url_pattern, method):
    """添加角色权限"""
    from .models import PolicyRule
    PolicyRule.objects.get_or_create(
        role_id=role_id,
        path=url_pattern,
        method=method.upper()
    )

def remove_role_policy(role_id, url_pattern, method):
    """删除角色权限"""
    from .models import PolicyRule
    PolicyRule.objects.filter(
        role_id=role_id,
        path=url_pattern,
        method=method.upper()
    ).delete()

def get_role_policies(role_id):
    """获取角色权限"""
    from .models import PolicyRule
    return PolicyRule.objects.filter(role_id=role_id).values_list('path', 'method')