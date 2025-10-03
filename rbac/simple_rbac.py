"""
简化的RBAC权限控制 - 类似gin-vue-admin
直接通过 角色 + URL + 方法 进行权限检查
"""
import casbin
from django.conf import settings
from django.db import models
from .models import User, Role, UserRole


class SimpleRBACManager:
    """简化的RBAC管理器"""
    
    _instance = None
    _enforcer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_enforcer(self):
        """获取Casbin enforcer实例"""
        if self._enforcer is None:
            # 使用内存适配器，策略直接写在代码中
            self._enforcer = casbin.Enforcer(str(settings.CASBIN_URL_MODEL))
        return self._enforcer
    
    def _load_policies(self):
        """加载权限策略"""
        # 确保enforcer已初始化
        enforcer = self.get_enforcer()
        
        # 获取权限策略
        policies = self._get_policies_from_config()
        
        # 如果没有配置策略，使用默认策略
        if not policies:
            policies = self._get_default_policies()
        
        # 添加策略
        for policy in policies:
            if not enforcer.has_policy(*policy):
                enforcer.add_policy(*policy)
        
        # 添加用户角色绑定（从数据库读取）
        self._load_user_roles()
    
    def _get_policies_from_config(self):
        """从配置和数据库获取权限策略"""
        policies = []
        
        # 1. 从PolicyRule表读取动态策略
        from .models import PolicyRule
        policy_rules = PolicyRule.objects.all()
        for rule in policy_rules:
            policies.append([rule.role_id, rule.path, rule.method])
        
        # 2. 从配置类读取静态策略（已移除，直接使用默认策略）
        
        return policies
    
    def _get_default_policies(self):
        """获取默认权限策略（基于角色ID）"""
        return [
            # 超级管理员 - 拥有所有权限 (role_id = 1)
            ['1', '/rbac/api/*', 'GET'],
            ['1', '/rbac/api/*', 'POST'],
            ['1', '/rbac/api/*', 'PUT'],
            ['1', '/rbac/api/*', 'DELETE'],
            ['1', '/rbac/auth/profile', 'GET'],
            
            # 管理员 - 部分权限 (role_id = 2)
            ['2', '/rbac/api/users', 'GET'],
            ['2', '/rbac/api/users/*', 'GET'],
            ['2', '/rbac/api/users/*', 'PUT'],
            ['2', '/rbac/api/roles', 'GET'],
            ['2', '/rbac/api/roles/*', 'GET'],
            ['2', '/rbac/auth/profile', 'GET'],
            
            # 普通用户 - 只读权限 (role_id = 3)
            ['3', '/rbac/api/users', 'GET'],
            ['3', '/rbac/api/users/*', 'GET'],
            ['3', '/rbac/auth/profile', 'GET'],
        ]
    
    def _load_user_roles(self):
        """从数据库加载用户角色绑定"""
        enforcer = self.get_enforcer()
        
        # 从数据库读取用户角色关系
        user_roles = UserRole.objects.select_related('user', 'role').filter(
            role__is_active=True
        )
        
        for user_role in user_roles:
            # 检查是否已存在，避免重复添加
            if not enforcer.has_grouping_policy(user_role.user.username, user_role.role.role_id):
                enforcer.add_grouping_policy(
                    user_role.user.username, 
                    user_role.role.role_id  # 使用role_id而不是code
                )
    
    def check_permission(self, user, url_path, method):
        """检查用户权限"""
        if not user or not user.is_authenticated:
            return False
        
        # 超级用户拥有所有权限
        if user.is_superuser:
            return True
        
        # 标准化URL路径
        normalized_url = self._normalize_url(url_path)
        
        # 使用Casbin检查权限
        enforcer = self.get_enforcer()
        return enforcer.enforce(user.username, normalized_url, method.upper())
    
    def _normalize_url(self, url_path):
        """标准化URL路径"""
        # 移除开头的斜杠
        if url_path.startswith('/'):
            url_path = url_path[1:]
        
        # 移除结尾的斜杠
        if url_path.endswith('/'):
            url_path = url_path[:-1]
        
        # 添加开头的斜杠
        if not url_path.startswith('/'):
            url_path = '/' + url_path
        
        return url_path
    
    def add_policy(self, role_code, url_path, method):
        """添加权限策略"""
        enforcer = self.get_enforcer()
        return enforcer.add_policy(role_code, url_path, method.upper())
    
    def remove_policy(self, role_code, url_path, method):
        """删除权限策略"""
        enforcer = self.get_enforcer()
        return enforcer.remove_policy(role_code, url_path, method.upper())
    
    def get_user_roles(self, username):
        """获取用户角色"""
        enforcer = self.get_enforcer()
        return enforcer.get_roles_for_user(username)
    
    def add_user_role(self, username, role_code):
        """为用户添加角色"""
        enforcer = self.get_enforcer()
        return enforcer.add_grouping_policy(username, role_code)
    
    def remove_user_role(self, username, role_code):
        """删除用户角色"""
        enforcer = self.get_enforcer()
        return enforcer.remove_grouping_policy(username, role_code)
    
    def reload_policies(self):
        """重新加载策略"""
        self._load_policies()
    
    def add_role_policy(self, role_id, url_pattern, method, save_to_db=True):
        """为角色添加权限策略"""
        enforcer = self.get_enforcer()
        success = enforcer.add_policy(role_id, url_pattern, method.upper())
        
        if success and save_to_db:
            # 保存到数据库
            from .models import PolicyRule
            PolicyRule.objects.get_or_create(
                role_id=role_id,
                url_pattern=url_pattern,
                method=method.upper(),
                defaults={'is_active': True}
            )
        
        return success
    
    def remove_role_policy(self, role_id, url_pattern, method, remove_from_db=True):
        """删除角色权限策略"""
        enforcer = self.get_enforcer()
        success = enforcer.remove_policy(role_id, url_pattern, method.upper())
        
        if success and remove_from_db:
            # 从数据库删除
            from .models import PolicyRule
            PolicyRule.objects.filter(
                role_id=role_id,
                url_pattern=url_pattern,
                method=method.upper()
            ).delete()
        
        return success
    
    def get_role_policies(self, role_id):
        """获取角色的所有权限策略"""
        enforcer = self.get_enforcer()
        return enforcer.get_permissions_for_user(role_id)


# 全局实例
simple_rbac_manager = SimpleRBACManager()


class SimpleRBACPermission:
    """简化的权限检查类"""
    
    def has_permission(self, request, view):
        """检查权限"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 超级用户拥有所有权限
        if request.user.is_superuser:
            return True
        
        # 检查权限
        return simple_rbac_manager.check_permission(
            request.user,
            request.path_info,
            request.method
        )


class SimpleRBACMiddleware:
    """简化的权限中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # 豁免URL列表
        self.exempt_urls = [
            '/admin/',
            '/rbac/auth/login/',
            '/rbac/auth/logout/',
            '/static/',
            '/media/',
            '/',
        ]
    
    def __call__(self, request):
        # 检查是否需要权限验证
        if self._should_check_permission(request):
            if not self._check_permission(request):
                from .response import ApiResponse
                return ApiResponse.forbidden(f"权限不足，无法访问 {request.method} {request.path_info}")
        
        response = self.get_response(request)
        return response
    
    def _should_check_permission(self, request):
        """判断是否需要检查权限"""
        path = request.path_info
        
        # 检查豁免URL
        for exempt_url in self.exempt_urls:
            if path.startswith(exempt_url):
                return False
        
        return True
    
    def _check_permission(self, request):
        """检查权限"""
        # 检查用户是否登录
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 超级用户拥有所有权限
        if request.user.is_superuser:
            return True
        
        # 使用简化的RBAC检查权限
        return simple_rbac_manager.check_permission(
            request.user,
            request.path_info,
            request.method
        )


