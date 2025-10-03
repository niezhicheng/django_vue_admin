"""
初始化简化RBAC数据的管理命令
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from rbac.models import User, Role, UserRole, Department, Menu, RoleMenu, PolicyRule, ApiGroup, Api
from rbac.simple_rbac import simple_rbac_manager


class Command(BaseCommand):
    help = '初始化简化RBAC权限数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='重置所有数据（删除现有数据）',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('正在重置RBAC数据...')
            self.reset_data()
        
        self.stdout.write('正在初始化简化RBAC数据...')
        self.init_data()
        self.stdout.write(
            self.style.SUCCESS('简化RBAC数据初始化完成！')
        )

    def reset_data(self):
        """重置数据"""
        from rbac.models import PolicyRule
        
        with transaction.atomic():
            PolicyRule.objects.all().delete()
            RoleMenu.objects.all().delete()
            Menu.objects.all().delete()
            UserRole.objects.all().delete()
            Role.objects.all().delete()
            Department.objects.all().delete()
            # 只删除非超级用户
            User.objects.filter(is_superuser=False).delete()

    def init_data(self):
        """初始化数据"""
        with transaction.atomic():
            # 创建部门
            departments_data = [
                {'name': '总公司', 'code': 'HQ', 'level': 1, 'sort_order': 1, 'parent': None},
                {'name': '技术部', 'code': 'TECH', 'level': 2, 'sort_order': 1, 'parent': 'HQ', 'leader': '技术总监'},
                {'name': '前端组', 'code': 'FRONTEND', 'level': 3, 'sort_order': 1, 'parent': 'TECH', 'leader': '前端组长'},
                {'name': '后端组', 'code': 'BACKEND', 'level': 3, 'sort_order': 2, 'parent': 'TECH', 'leader': '后端组长'},
                {'name': '市场部', 'code': 'MARKET', 'level': 2, 'sort_order': 2, 'parent': 'HQ', 'leader': '市场总监'},
                {'name': '销售部', 'code': 'SALES', 'level': 2, 'sort_order': 3, 'parent': 'HQ', 'leader': '销售总监'},
            ]
            
            departments = {}
            for dept_data in departments_data:
                parent_code = dept_data.pop('parent', None)
                parent = departments.get(parent_code) if parent_code else None
                
                dept, created = Department.objects.get_or_create(
                    code=dept_data['code'],
                    defaults={**dept_data, 'parent': parent}
                )
                departments[dept.code] = dept
                if created:
                    self.stdout.write(f'创建部门: {dept.name} (编码: {dept.code})')
            
            # 创建角色
            roles_data = [
                {'role_id': '1', 'name': '超级管理员', 'code': 'admin', 'description': '系统最高权限', 'data_scope': 1},
                {'role_id': '2', 'name': '部门经理', 'code': 'manager', 'description': '部门管理权限', 'data_scope': 2},
                {'role_id': '3', 'name': '普通员工', 'code': 'user', 'description': '普通用户权限', 'data_scope': 4},
                {'role_id': '4', 'name': '部门主管', 'code': 'supervisor', 'description': '本部门数据权限', 'data_scope': 3},
            ]
            
            roles = {}
            for role_data in roles_data:
                role, created = Role.objects.get_or_create(
                    role_id=role_data['role_id'],
                    defaults=role_data
                )
                roles[role.role_id] = role
                if created:
                    self.stdout.write(f'创建角色: {role.name} (ID: {role.role_id})')

            # 创建测试用户
            users_data = [
                {
                    'username': 'admin',
                    'email': 'admin@example.com',
                    'first_name': '系统',
                    'last_name': '管理员',
                    'password': 'admin123',
                    'is_staff': True,
                    'department': 'HQ',
                    'roles': ['1']
                },
                {
                    'username': 'tech_manager',
                    'email': 'tech.manager@example.com',
                    'first_name': '技术',
                    'last_name': '总监',
                    'password': 'manager123',
                    'department': 'TECH',
                    'roles': ['2']
                },
                {
                    'username': 'frontend_lead',
                    'email': 'frontend.lead@example.com',
                    'first_name': '前端',
                    'last_name': '组长',
                    'password': 'lead123',
                    'department': 'FRONTEND',
                    'roles': ['4']
                },
                {
                    'username': 'backend_dev',
                    'email': 'backend.dev@example.com',
                    'first_name': '后端',
                    'last_name': '开发',
                    'password': 'dev123',
                    'department': 'BACKEND',
                    'roles': ['3']
                },
                {
                    'username': 'market_staff',
                    'email': 'market.staff@example.com',
                    'first_name': '市场',
                    'last_name': '专员',
                    'password': 'staff123',
                    'department': 'MARKET',
                    'roles': ['3']
                },
            ]
            
            for user_data in users_data:
                user_roles = user_data.pop('roles')
                password = user_data.pop('password')
                department_code = user_data.pop('department', None)
                
                # 设置部门
                if department_code and department_code in departments:
                    user_data['department'] = departments[department_code]
                
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults=user_data
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    dept_info = f" - 部门: {user.department.name}" if user.department else ""
                    self.stdout.write(f'创建用户: {user.username}{dept_info}')
                    
                    # 分配角色
                    for role_id in user_roles:
                        if role_id in roles:
                            role = roles[role_id]
                            UserRole.objects.get_or_create(user=user, role=role)
                            self.stdout.write(f'分配角色 {role.name} (数据权限: {role.get_data_scope_display()}) 给用户 {user.username}')

                # 初始化菜单
                self.stdout.write('正在初始化菜单...')
                self.init_menus()

                # 初始化角色菜单关联
                self.stdout.write('正在初始化角色菜单关联...')
                self.init_role_menus()

                # 初始化API分组和API
                self.stdout.write('正在初始化API分组和API...')
                self.init_api_groups()
                self.init_apis()

                # 初始化权限策略到数据库
                self.stdout.write('正在初始化权限策略...')
                self.init_policies()

                # 重新加载权限策略
                self.stdout.write('正在加载权限策略...')
                simple_rbac_manager.reload_policies()
                self.stdout.write('权限策略加载完成')

    def init_menus(self):
        """初始化菜单数据"""
        menus_data = [
            # 系统管理
            {
                'name': 'system',
                'title': '系统管理',
                'icon': 'Setting',
                'path': '/system',
                'component': 'Layout',
                'redirect': '/system/user',
                'menu_type': 1,  # 目录
                'sort_order': 1,
                'permission_code': 'system',
                'parent': None,
            },
            {
                'name': 'user',
                'title': '用户管理',
                'icon': 'User',
                'path': '/system/user',
                'component': 'system/user/index',
                'menu_type': 2,  # 菜单
                'sort_order': 1,
                'permission_code': 'system:user:list',
                'parent': 'system',
            },
            {
                'name': 'role',
                'title': '角色管理',
                'icon': 'UserFilled',
                'path': '/system/role',
                'component': 'system/role/index',
                'menu_type': 2,  # 菜单
                'sort_order': 2,
                'permission_code': 'system:role:list',
                'parent': 'system',
            },
            {
                'name': 'menu',
                'title': '菜单管理',
                'icon': 'Menu',
                'path': '/system/menu',
                'component': 'system/menu/index',
                'menu_type': 2,  # 菜单
                'sort_order': 3,
                'permission_code': 'system:menu:list',
                'parent': 'system',
            },
            {
                'name': 'dept',
                'title': '部门管理',
                'icon': 'OfficeBuilding',
                'path': '/system/dept',
                'component': 'system/dept/index',
                'menu_type': 2,  # 菜单
                'sort_order': 4,
                'permission_code': 'system:dept:list',
                'parent': 'system',
            },
            {
                'name': 'api',
                'title': 'API管理',
                'icon': 'Code',
                'path': '/system/api',
                'component': 'system/api/index',
                'menu_type': 2,  # 菜单
                'sort_order': 5,
                'permission_code': 'system:api:list',
                'parent': 'system',
            },
            {
                'name': 'api-group',
                'title': 'API分组管理',
                'icon': 'Folder',
                'path': '/system/api-group',
                'component': 'system/api-group/index',
                'menu_type': 2,  # 菜单
                'sort_order': 6,
                'permission_code': 'system:api-group:list',
                'parent': 'system',
            },
            
            # 业务管理
            {
                'name': 'business',
                'title': '业务管理',
                'icon': 'Document',
                'path': '/business',
                'component': 'Layout',
                'redirect': '/business/article',
                'menu_type': 1,  # 目录
                'sort_order': 2,
                'permission_code': 'business',
                'parent': None,
            },
            {
                'name': 'article',
                'title': '文章管理',
                'icon': 'Document',
                'path': '/business/article',
                'component': 'business/article/index',
                'menu_type': 2,  # 菜单
                'sort_order': 1,
                'permission_code': 'business:article:list',
                'parent': 'business',
            },
            {
                'name': 'project',
                'title': '项目管理',
                'icon': 'Folder',
                'path': '/business/project',
                'component': 'business/project/index',
                'menu_type': 2,  # 菜单
                'sort_order': 2,
                'permission_code': 'business:project:list',
                'parent': 'business',
            },
            {
                'name': 'document',
                'title': '文档管理',
                'icon': 'Files',
                'path': '/business/document',
                'component': 'business/document/index',
                'menu_type': 2,  # 菜单
                'sort_order': 3,
                'permission_code': 'business:document:list',
                'parent': 'business',
            },
            
            # 数据统计
            {
                'name': 'dashboard',
                'title': '数据统计',
                'icon': 'DataAnalysis',
                'path': '/dashboard',
                'component': 'dashboard/index',
                'menu_type': 2,  # 菜单
                'sort_order': 0,
                'permission_code': 'dashboard',
                'parent': None,
            },
        ]

        # 按钮权限
        button_permissions = [
            # 用户管理按钮
            {'name': 'user-add', 'title': '新增用户', 'menu_type': 3, 'permission_code': 'system:user:add', 'parent': 'user'},
            {'name': 'user-edit', 'title': '编辑用户', 'menu_type': 3, 'permission_code': 'system:user:edit', 'parent': 'user'},
            {'name': 'user-delete', 'title': '删除用户', 'menu_type': 3, 'permission_code': 'system:user:delete', 'parent': 'user'},
            {'name': 'user-export', 'title': '导出用户', 'menu_type': 3, 'permission_code': 'system:user:export', 'parent': 'user'},
            
            # 角色管理按钮
            {'name': 'role-add', 'title': '新增角色', 'menu_type': 3, 'permission_code': 'system:role:add', 'parent': 'role'},
            {'name': 'role-edit', 'title': '编辑角色', 'menu_type': 3, 'permission_code': 'system:role:edit', 'parent': 'role'},
            {'name': 'role-delete', 'title': '删除角色', 'menu_type': 3, 'permission_code': 'system:role:delete', 'parent': 'role'},
            {'name': 'role-assign-menu', 'title': '分配菜单', 'menu_type': 3, 'permission_code': 'system:role:assign_menu', 'parent': 'role'},
            
            # 菜单管理按钮
            {'name': 'menu-add', 'title': '新增菜单', 'menu_type': 3, 'permission_code': 'system:menu:add', 'parent': 'menu'},
            {'name': 'menu-edit', 'title': '编辑菜单', 'menu_type': 3, 'permission_code': 'system:menu:edit', 'parent': 'menu'},
            {'name': 'menu-delete', 'title': '删除菜单', 'menu_type': 3, 'permission_code': 'system:menu:delete', 'parent': 'menu'},
        ]

        # 创建菜单
        menus = {}
        created_count = 0
        
        # 先创建目录和菜单
        for menu_data in menus_data:
            parent_name = menu_data.pop('parent', None)
            parent = menus.get(parent_name) if parent_name else None

            menu, created = Menu.objects.get_or_create(
                name=menu_data['name'],
                defaults={**menu_data, 'parent': parent}
            )
            menus[menu.name] = menu
            if created:
                created_count += 1
                self.stdout.write(f'创建菜单: {menu.title} (类型: {menu.get_menu_type_display()})')

        # 再创建按钮权限
        for button_data in button_permissions:
            parent_name = button_data.pop('parent', None)
            parent = menus.get(parent_name) if parent_name else None

            button_data.update({
                'path': None,
                'component': None,
                'icon': None,
                'sort_order': 99,
                'visible': False,  # 按钮权限不显示在菜单中
            })

            menu, created = Menu.objects.get_or_create(
                name=button_data['name'],
                defaults={**button_data, 'parent': parent}
            )
            menus[menu.name] = menu
            if created:
                created_count += 1
                self.stdout.write(f'创建按钮权限: {menu.title} (权限码: {menu.permission_code})')

        self.stdout.write(f'成功创建 {created_count} 个菜单/权限')
        return menus

    def init_role_menus(self):
        """初始化角色菜单关联"""
        # 定义角色菜单关联
        role_menu_mapping = {
            '1': 'all',  # 超级管理员 - 所有菜单
            '2': [  # 部门经理
                'dashboard', 'system', 'user', 'dept', 'business', 'article', 'project', 'document',
                'user-add', 'user-edit', 'user-export'
            ],
            '3': [  # 普通员工
                'dashboard', 'business', 'article', 'project', 'document'
            ],
            '4': [  # 部门主管
                'dashboard', 'system', 'user', 'dept', 'business', 'article', 'project', 'document',
                'user-edit', 'user-export'
            ],
        }

        # 获取所有角色和菜单
        roles = {role.role_id: role for role in Role.objects.all()}
        menus = {menu.name: menu for menu in Menu.objects.all()}

        assigned_count = 0
        for role_id, menu_names in role_menu_mapping.items():
            if role_id in roles:
                role = roles[role_id]
                
                if menu_names == 'all':
                    # 超级管理员分配所有菜单
                    for menu in menus.values():
                        role_menu, created = RoleMenu.objects.get_or_create(role=role, menu=menu)
                        if created:
                            assigned_count += 1
                else:
                    # 其他角色分配指定菜单
                    for menu_name in menu_names:
                        if menu_name in menus:
                            menu = menus[menu_name]
                            role_menu, created = RoleMenu.objects.get_or_create(role=role, menu=menu)
                            if created:
                                assigned_count += 1

                self.stdout.write(f'为角色 {role.name} 分配菜单权限')

        self.stdout.write(f'成功创建 {assigned_count} 个角色菜单关联')

    def init_policies(self):
        """初始化权限策略到数据库"""
        from rbac.models import PolicyRule
        
        # 获取默认策略
        default_policies = simple_rbac_manager._get_default_policies()
        
        # 创建角色ID映射：硬编码的role_id -> 实际的角色ID
        role_mapping = {
            '1': '5',  # 超级管理员
            '2': '6',  # 部门经理
            '3': '7',  # 普通员工
        }
        
        created_count = 0
        for hardcoded_role_id, url_pattern, method in default_policies:
            # 映射到实际的角色ID
            actual_role_id = role_mapping.get(hardcoded_role_id, hardcoded_role_id)
            
            policy_rule, created = PolicyRule.objects.get_or_create(
                role_id=actual_role_id,
                path=url_pattern,
                method=method,
                defaults={}
            )
            if created:
                created_count += 1
                self.stdout.write(f'创建权限策略: {actual_role_id} -> {method} {url_pattern}')
        
        if created_count > 0:
            self.stdout.write(f'成功创建 {created_count} 条权限策略')
        else:
            self.stdout.write('权限策略已存在，无需创建')

    def test_permissions(self):
        """测试权限"""
        test_cases = [
            ('admin', '/rbac/api/users', 'GET'),      # ✅ 应该通过 (role_id=1)
            ('admin', '/rbac/api/users/123', 'DELETE'), # ✅ 应该通过 (role_id=1)
            ('manager', '/rbac/api/users', 'GET'),    # ✅ 应该通过 (role_id=2)
            ('manager', '/rbac/api/users/123', 'DELETE'), # ❌ 应该失败 (role_id=2)
            ('user', '/rbac/api/users', 'GET'),       # ✅ 应该通过 (role_id=3)
            ('user', '/rbac/api/users', 'POST'),      # ❌ 应该失败 (role_id=3)
        ]
        
        self.stdout.write('\n权限测试结果:')
        for username, url_path, method in test_cases:
            try:
                user = User.objects.get(username=username)
                result = simple_rbac_manager.check_permission(user, url_path, method)
                
                # 获取用户角色信息
                user_roles = simple_rbac_manager.get_user_roles(username)
                role_info = f"(role_id: {','.join(user_roles)})" if user_roles else "(无角色)"
                
                status = '✓' if result else '✗'
                self.stdout.write(f'{status} {username} {role_info} -> {method} {url_path}: {result}')
            except User.DoesNotExist:
                self.stdout.write(f'✗ 用户 {username} 不存在')

    def show_policies(self):
        """显示当前权限策略"""
        self.stdout.write('\n当前权限策略:')
        
        # 显示默认策略
        policies = simple_rbac_manager._get_default_policies()
        for role_id, url_pattern, method in policies:
            self.stdout.write(f'  {role_id} -> {method} {url_pattern}')
        
        self.stdout.write(f'\n总计: {len(policies)} 条策略')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('正在重置RBAC数据...')
            self.reset_data()
        
        self.stdout.write('正在初始化简化RBAC数据...')
        self.init_data()
        
        # 显示策略
        self.show_policies()
        
        self.stdout.write(
            self.style.SUCCESS('\n简化RBAC数据初始化完成！')
        )

    def init_api_groups(self):
        """初始化API分组"""
        api_groups_data = [
            {'name': '系统管理', 'description': '系统管理相关API', 'sort_order': 1},
            {'name': '用户管理', 'description': '用户管理相关API', 'sort_order': 2},
            {'name': '角色管理', 'description': '角色管理相关API', 'sort_order': 3},
            {'name': '权限管理', 'description': '权限管理相关API', 'sort_order': 4},
            {'name': '业务管理', 'description': '业务管理相关API', 'sort_order': 5},
        ]
        
        for group_data in api_groups_data:
            ApiGroup.objects.get_or_create(
                name=group_data['name'],
                defaults=group_data
            )

    def init_apis(self):
        """初始化API"""
        # 获取API分组
        system_group = ApiGroup.objects.get(name='系统管理')
        user_group = ApiGroup.objects.get(name='用户管理')
        role_group = ApiGroup.objects.get(name='角色管理')
        permission_group = ApiGroup.objects.get(name='权限管理')
        business_group = ApiGroup.objects.get(name='业务管理')
        
        apis_data = [
            # 系统管理API
            {'name': '获取用户信息', 'path': '/rbac/auth/profile/', 'method': 'GET', 'group': system_group, 'description': '获取当前用户信息'},
            {'name': '用户登录', 'path': '/rbac/auth/token/', 'method': 'POST', 'group': system_group, 'description': '用户登录获取token'},
            {'name': '刷新Token', 'path': '/rbac/auth/token/refresh/', 'method': 'POST', 'group': system_group, 'description': '刷新访问token'},
            {'name': '用户登出', 'path': '/rbac/auth/logout/', 'method': 'POST', 'group': system_group, 'description': '用户登出'},
            
            # 用户管理API
            {'name': '获取用户列表', 'path': '/rbac/api/users/', 'method': 'GET', 'group': user_group, 'description': '获取用户列表'},
            {'name': '创建用户', 'path': '/rbac/api/users/', 'method': 'POST', 'group': user_group, 'description': '创建新用户'},
            {'name': '更新用户', 'path': '/rbac/api/users/{id}/', 'method': 'PUT', 'group': user_group, 'description': '更新用户信息'},
            {'name': '删除用户', 'path': '/rbac/api/users/{id}/', 'method': 'DELETE', 'group': user_group, 'description': '删除用户'},
            
            # 角色管理API
            {'name': '获取角色列表', 'path': '/rbac/api/roles/', 'method': 'GET', 'group': role_group, 'description': '获取角色列表'},
            {'name': '创建角色', 'path': '/rbac/api/roles/', 'method': 'POST', 'group': role_group, 'description': '创建新角色'},
            {'name': '更新角色', 'path': '/rbac/api/roles/{id}/', 'method': 'PUT', 'group': role_group, 'description': '更新角色信息'},
            {'name': '删除角色', 'path': '/rbac/api/roles/{id}/', 'method': 'DELETE', 'group': role_group, 'description': '删除角色'},
            {'name': '分配角色菜单', 'path': '/rbac/api/roles/{id}/assign_menus/', 'method': 'POST', 'group': role_group, 'description': '为角色分配菜单权限'},
            
            # 权限管理API
            {'name': '获取菜单列表', 'path': '/rbac/api/menus/', 'method': 'GET', 'group': permission_group, 'description': '获取菜单列表'},
            {'name': '获取菜单树', 'path': '/rbac/api/menus/tree/', 'method': 'GET', 'group': permission_group, 'description': '获取菜单树结构'},
            {'name': '获取菜单路由', 'path': '/rbac/api/menus/routes/', 'method': 'GET', 'group': permission_group, 'description': '获取用户菜单路由'},
            {'name': '创建菜单', 'path': '/rbac/api/menus/', 'method': 'POST', 'group': permission_group, 'description': '创建新菜单'},
            {'name': '更新菜单', 'path': '/rbac/api/menus/{id}/', 'method': 'PUT', 'group': permission_group, 'description': '更新菜单信息'},
            {'name': '删除菜单', 'path': '/rbac/api/menus/{id}/', 'method': 'DELETE', 'group': permission_group, 'description': '删除菜单'},
            
            # 业务管理API
            {'name': '获取文章列表', 'path': '/business_demo/api/articles/', 'method': 'GET', 'group': business_group, 'description': '获取文章列表'},
            {'name': '创建文章', 'path': '/business_demo/api/articles/', 'method': 'POST', 'group': business_group, 'description': '创建新文章'},
            {'name': '更新文章', 'path': '/business_demo/api/articles/{id}/', 'method': 'PUT', 'group': business_group, 'description': '更新文章信息'},
            {'name': '删除文章', 'path': '/business_demo/api/articles/{id}/', 'method': 'DELETE', 'group': business_group, 'description': '删除文章'},
        ]
        
        for api_data in apis_data:
            Api.objects.get_or_create(
                path=api_data['path'],
                method=api_data['method'],
                defaults=api_data
            )
