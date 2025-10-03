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
            # 使用内存适配器，启动时从数据库加载
            from django.conf import settings
            self._enforcer = casbin.Enforcer(str(settings.CASBIN_URL_MODEL))
            
            # 从数据库加载策略到内存
            self._load_policies_from_db()
        return self._enforcer
    
    def _load_policies_from_db(self):
        """从数据库加载权限策略到Casbin内存"""
        enforcer = self.get_enforcer()
        
        # 清空现有策略
        enforcer.clear_policy()
        
        # 1. 加载权限策略
        from .models import PolicyRule
        policy_rules = PolicyRule.objects.all()
        for rule in policy_rules:
            enforcer.add_policy(rule.role_id, rule.path, rule.method)
        
        # 2. 加载用户角色绑定
        from .models import UserRole
        user_roles = UserRole.objects.select_related('user', 'role').filter(
            role__is_active=True
        )
        for user_role in user_roles:
            enforcer.add_grouping_policy(user_role.user.username, user_role.role.role_id)
    
    def _load_policies(self):
        """加载权限策略（保持向后兼容）"""
        self._load_policies_from_db()
    
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
        result = enforcer.enforce(user.username, normalized_url, method.upper())
        
        # 调试信息
        print(f"[DEBUG] 权限检查: 用户={user.username}, 路径={normalized_url}, 方法={method.upper()}, 结果={result}")
        
        # 检查用户角色
        user_roles = enforcer.get_roles_for_user(user.username)
        print(f"[DEBUG] 用户角色: {user_roles}")
        
        # 检查角色权限
        for role in user_roles:
            role_policies = [p for p in enforcer.get_policy() if p[0] == role]
            print(f"[DEBUG] 角色{role}的权限数量: {len(role_policies)}")
            for policy in role_policies[:3]:  # 只显示前3个
                print(f"[DEBUG]   {policy}")
        
        return result
    
    def _normalize_url(self, url_path):
        """标准化URL路径"""
        # 移除查询参数
        if '?' in url_path:
            url_path = url_path.split('?')[0]
        
        # 确保以斜杠开头
        if not url_path.startswith('/'):
            url_path = '/' + url_path
        
        # 对于API路径，保持结尾的斜杠以匹配权限策略
        if url_path.startswith('/rbac/api/') and not url_path.endswith('/'):
            url_path = url_path + '/'
        
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
    
    def add_user_role(self, username, role_id, save_to_db=True):
        """为用户添加角色"""
        if save_to_db:
            # 先保存到数据库
            from .models import User, Role, UserRole
            try:
                user = User.objects.get(username=username)
                role = Role.objects.get(role_id=role_id)
                user_role, created = UserRole.objects.get_or_create(user=user, role=role)
                if created:
                    # 同步到Casbin内存
                    self.sync_user_role_to_casbin(username, role_id, 'add')
                    return True
                return False
            except (User.DoesNotExist, Role.DoesNotExist):
                return False
        else:
            # 只添加到Casbin内存
            enforcer = self.get_enforcer()
            return enforcer.add_grouping_policy(username, role_id)
    
    def remove_user_role(self, username, role_id, remove_from_db=True):
        """删除用户角色"""
        if remove_from_db:
            # 先从数据库删除
            from .models import User, Role, UserRole
            try:
                user = User.objects.get(username=username)
                role = Role.objects.get(role_id=role_id)
                deleted_count = UserRole.objects.filter(user=user, role=role).delete()[0]
                if deleted_count > 0:
                    # 同步到Casbin内存
                    self.sync_user_role_to_casbin(username, role_id, 'remove')
                    return True
                return False
            except (User.DoesNotExist, Role.DoesNotExist):
                return False
        else:
            # 只从Casbin内存删除
            enforcer = self.get_enforcer()
            return enforcer.remove_grouping_policy(username, role_id)
    
    def reload_policies(self):
        """重新加载策略"""
        self._load_policies_from_db()
    
    def sync_policy_to_casbin(self, role_id, path, method, action='add'):
        """同步单个权限策略到Casbin内存"""
        enforcer = self.get_enforcer()
        if action == 'add':
            enforcer.add_policy(role_id, path, method)
        elif action == 'remove':
            enforcer.remove_policy(role_id, path, method)
    
    def sync_user_role_to_casbin(self, username, role_id, action='add'):
        """同步用户角色绑定到Casbin内存"""
        enforcer = self.get_enforcer()
        if action == 'add':
            enforcer.add_grouping_policy(username, role_id)
        elif action == 'remove':
            enforcer.remove_grouping_policy(username, role_id)
    
    def add_role_policy(self, role_id, url_pattern, method, save_to_db=True):
        """为角色添加权限策略"""
        if save_to_db:
            # 先保存到数据库
            from .models import PolicyRule
            policy, created = PolicyRule.objects.get_or_create(
                role_id=role_id,
                path=url_pattern,
                method=method.upper()
            )
            if created:
                # 同步到Casbin内存
                self.sync_policy_to_casbin(role_id, url_pattern, method.upper(), 'add')
                return True
            return False
        else:
            # 只添加到Casbin内存
            enforcer = self.get_enforcer()
            return enforcer.add_policy(role_id, url_pattern, method.upper())
    
    def remove_role_policy(self, role_id, url_pattern, method, remove_from_db=True):
        """删除角色权限策略"""
        if remove_from_db:
            # 先从数据库删除
            from .models import PolicyRule
            deleted_count = PolicyRule.objects.filter(
                role_id=role_id,
                path=url_pattern,
                method=method.upper()
            ).delete()[0]
            
            if deleted_count > 0:
                # 同步到Casbin内存
                self.sync_policy_to_casbin(role_id, url_pattern, method.upper(), 'remove')
                return True
            return False
        else:
            # 只从Casbin内存删除
            enforcer = self.get_enforcer()
            return enforcer.remove_policy(role_id, url_pattern, method.upper())
    
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
            '/rbac/auth/profile/',
            '/rbac/auth/user-menus/',
            '/static/',
            '/media/',
            '/rbac/auth/token/',  # JWT token相关
            '/rbac/auth/token/refresh/',
            '/rbac/auth/token/verify/',
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
        
        # 跳过DRF API视图，让DRF自己的认证和权限系统处理
        if path.startswith('/rbac/api/') or path.startswith('/business_demo/api/'):
            return False
        
        return True
    
    def _check_permission(self, request):
        print(f"权限检查: {request.method} {request.path_info}")
        print(f"用户: {request.user}")
        print(f"是否认证: {request.user.is_authenticated if request.user else False}")
        print(f"是否超级用户: {request.user.is_superuser if request.user else False}")
        
        """检查权限"""
        # 检查用户是否登录
        if not request.user or not request.user.is_authenticated:
            print("权限检查失败: 用户未登录")
            return False
        
        # 超级用户拥有所有权限
        if request.user.is_superuser:
            print("权限检查通过: 超级用户")
            return True
        
        # 确保权限策略已加载
        try:
            enforcer = simple_rbac_manager.get_enforcer()
            if not enforcer.get_policy():
                # 如果权限策略为空，重新加载
                simple_rbac_manager.reload_policies()
        except:
            pass
        
        # 使用简化的RBAC检查权限
        return simple_rbac_manager.check_permission(
            request.user,
            request.path_info,
            request.method
        )


