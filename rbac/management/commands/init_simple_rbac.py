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
        
        # 为admin角色添加完整的API权限
        self.init_admin_permissions()
        
        if created_count > 0:
            self.stdout.write(f'成功创建 {created_count} 条权限策略')
    
    def init_admin_permissions(self):
        """为admin角色添加完整的API权限"""
        from rbac.models import User, Role, UserRole
        
        # 确保admin用户存在且为超级用户
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': '系统',
                'last_name': '管理员',
                'is_superuser': True,
                'is_staff': True,
                'is_active': True
            }
        )
        
        if not created:
            # 如果用户已存在，确保是超级用户
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.is_active = True
            admin_user.save()
        
        # 设置admin用户密码
        admin_user.set_password('admin123')
        admin_user.save()
        
        # 获取admin角色
        admin_role = Role.objects.get(code='admin')
        
        # 为admin用户分配超级管理员角色
        UserRole.objects.get_or_create(user=admin_user, role=admin_role)
        self.stdout.write('为admin用户分配超级管理员角色')
        
        # 为admin角色添加所有API权限
        api_permissions = [
            # 用户管理API
            ('/rbac/api/users/', 'GET'),
            ('/rbac/api/users/', 'POST'),
            ('/rbac/api/users/{id}/', 'GET'),
            ('/rbac/api/users/{id}/', 'PUT'),
            ('/rbac/api/users/{id}/', 'DELETE'),
            ('/rbac/api/users/{id}/reset-password/', 'POST'),
            ('/rbac/api/users/{id}/set_custom_scope/', 'POST'),
            
            # 角色管理API
            ('/rbac/api/roles/', 'GET'),
            ('/rbac/api/roles/', 'POST'),
            ('/rbac/api/roles/{id}/', 'GET'),
            ('/rbac/api/roles/{id}/', 'PUT'),
            ('/rbac/api/roles/{id}/', 'DELETE'),
            ('/rbac/api/roles/{id}/get-api-permissions/', 'GET'),
            ('/rbac/api/roles/{id}/assign-api-permissions/', 'POST'),
            ('/rbac/api/roles/{id}/get-menu-permissions/', 'GET'),
            ('/rbac/api/roles/{id}/assign-menu-permissions/', 'POST'),
            
            # 部门管理API
            ('/rbac/api/departments/', 'GET'),
            ('/rbac/api/departments/', 'POST'),
            ('/rbac/api/departments/{id}/', 'GET'),
            ('/rbac/api/departments/{id}/', 'PUT'),
            ('/rbac/api/departments/{id}/', 'DELETE'),
            ('/rbac/api/departments/tree/', 'GET'),
            ('/rbac/api/departments/{id}/children/', 'GET'),
            
            # 菜单管理API
            ('/rbac/api/menus/', 'GET'),
            ('/rbac/api/menus/', 'POST'),
            ('/rbac/api/menus/{id}/', 'GET'),
            ('/rbac/api/menus/{id}/', 'PUT'),
            ('/rbac/api/menus/{id}/', 'DELETE'),
            ('/rbac/api/menus/tree/', 'GET'),
            
            # API管理API
            ('/rbac/api/api-groups/', 'GET'),
            ('/rbac/api/api-groups/', 'POST'),
            ('/rbac/api/api-groups/{id}/', 'GET'),
            ('/rbac/api/api-groups/{id}/', 'PUT'),
            ('/rbac/api/api-groups/{id}/', 'DELETE'),
            ('/rbac/api/apis/', 'GET'),
            ('/rbac/api/apis/', 'POST'),
            ('/rbac/api/apis/{id}/', 'GET'),
            ('/rbac/api/apis/{id}/', 'PUT'),
            ('/rbac/api/apis/{id}/', 'DELETE'),
            
            # 认证相关API
            ('/rbac/auth/profile/', 'GET'),
            ('/rbac/auth/user-menus/', 'GET'),
            ('/rbac/auth/token/', 'POST'),
            ('/rbac/auth/token/refresh/', 'POST'),
            ('/rbac/auth/token/verify/', 'POST'),
            
            # 业务管理API
            ('/business_demo/api/articles/', 'GET'),
            ('/business_demo/api/articles/', 'POST'),
            ('/business_demo/api/articles/{id}/', 'GET'),
            ('/business_demo/api/articles/{id}/', 'PUT'),
            ('/business_demo/api/articles/{id}/', 'DELETE'),
            ('/business_demo/api/projects/', 'GET'),
            ('/business_demo/api/projects/', 'POST'),
            ('/business_demo/api/projects/{id}/', 'GET'),
            ('/business_demo/api/projects/{id}/', 'PUT'),
            ('/business_demo/api/projects/{id}/', 'DELETE'),
            ('/business_demo/api/documents/', 'GET'),
            ('/business_demo/api/documents/', 'POST'),
            ('/business_demo/api/documents/{id}/', 'GET'),
            ('/business_demo/api/documents/{id}/', 'PUT'),
            ('/business_demo/api/documents/{id}/', 'DELETE'),
            ('/business_demo/api/tasks/', 'GET'),
            ('/business_demo/api/tasks/', 'POST'),
            ('/business_demo/api/tasks/{id}/', 'GET'),
            ('/business_demo/api/tasks/{id}/', 'PUT'),
            ('/business_demo/api/tasks/{id}/', 'DELETE'),
        ]
        
        admin_permissions_count = 0
        for path, method in api_permissions:
            success = simple_rbac_manager.add_role_policy(admin_role.role_id, path, method)
            if success:
                admin_permissions_count += 1
        
        self.stdout.write(f'为admin角色添加了 {admin_permissions_count} 个API权限')

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
            {'name': '验证Token', 'path': '/rbac/auth/token/verify/', 'method': 'POST', 'group': system_group, 'description': '验证token有效性'},
            {'name': '用户登出', 'path': '/rbac/auth/logout/', 'method': 'POST', 'group': system_group, 'description': '用户登出'},
            {'name': '获取用户菜单', 'path': '/rbac/auth/user-menus/', 'method': 'GET', 'group': system_group, 'description': '获取用户菜单树'},
            
            # 用户管理API
            {'name': '获取用户列表', 'path': '/rbac/api/users/', 'method': 'GET', 'group': user_group, 'description': '获取用户列表'},
            {'name': '创建用户', 'path': '/rbac/api/users/', 'method': 'POST', 'group': user_group, 'description': '创建新用户'},
            {'name': '获取用户详情', 'path': '/rbac/api/users/{id}/', 'method': 'GET', 'group': user_group, 'description': '获取用户详细信息'},
            {'name': '更新用户', 'path': '/rbac/api/users/{id}/', 'method': 'PUT', 'group': user_group, 'description': '更新用户信息'},
            {'name': '删除用户', 'path': '/rbac/api/users/{id}/', 'method': 'DELETE', 'group': user_group, 'description': '删除用户'},
            {'name': '重置用户密码', 'path': '/rbac/api/users/{id}/reset-password/', 'method': 'POST', 'group': user_group, 'description': '重置用户密码'},
            {'name': '设置用户数据权限', 'path': '/rbac/api/users/{id}/set_custom_scope/', 'method': 'POST', 'group': user_group, 'description': '设置用户自定义数据权限'},
            
            # 角色管理API
            {'name': '获取角色列表', 'path': '/rbac/api/roles/', 'method': 'GET', 'group': role_group, 'description': '获取角色列表'},
            {'name': '创建角色', 'path': '/rbac/api/roles/', 'method': 'POST', 'group': role_group, 'description': '创建新角色'},
            {'name': '获取角色详情', 'path': '/rbac/api/roles/{id}/', 'method': 'GET', 'group': role_group, 'description': '获取角色详细信息'},
            {'name': '更新角色', 'path': '/rbac/api/roles/{id}/', 'method': 'PUT', 'group': role_group, 'description': '更新角色信息'},
            {'name': '删除角色', 'path': '/rbac/api/roles/{id}/', 'method': 'DELETE', 'group': role_group, 'description': '删除角色'},
            {'name': '获取角色API权限', 'path': '/rbac/api/roles/{id}/get-api-permissions/', 'method': 'GET', 'group': role_group, 'description': '获取角色的API权限'},
            {'name': '分配角色API权限', 'path': '/rbac/api/roles/{id}/assign-api-permissions/', 'method': 'POST', 'group': role_group, 'description': '为角色分配API权限'},
            {'name': '获取角色菜单权限', 'path': '/rbac/api/roles/{id}/get-menu-permissions/', 'method': 'GET', 'group': role_group, 'description': '获取角色的菜单权限'},
            {'name': '分配角色菜单权限', 'path': '/rbac/api/roles/{id}/assign-menu-permissions/', 'method': 'POST', 'group': role_group, 'description': '为角色分配菜单权限'},
            
            # 部门管理API
            {'name': '获取部门列表', 'path': '/rbac/api/departments/', 'method': 'GET', 'group': user_group, 'description': '获取部门列表'},
            {'name': '创建部门', 'path': '/rbac/api/departments/', 'method': 'POST', 'group': user_group, 'description': '创建新部门'},
            {'name': '获取部门详情', 'path': '/rbac/api/departments/{id}/', 'method': 'GET', 'group': user_group, 'description': '获取部门详细信息'},
            {'name': '更新部门', 'path': '/rbac/api/departments/{id}/', 'method': 'PUT', 'group': user_group, 'description': '更新部门信息'},
            {'name': '删除部门', 'path': '/rbac/api/departments/{id}/', 'method': 'DELETE', 'group': user_group, 'description': '删除部门'},
            {'name': '获取部门树', 'path': '/rbac/api/departments/tree/', 'method': 'GET', 'group': user_group, 'description': '获取部门树结构'},
            {'name': '获取子部门', 'path': '/rbac/api/departments/{id}/children/', 'method': 'GET', 'group': user_group, 'description': '获取子部门列表'},
            
            # 权限管理API
            {'name': '获取菜单列表', 'path': '/rbac/api/menus/', 'method': 'GET', 'group': permission_group, 'description': '获取菜单列表'},
            {'name': '创建菜单', 'path': '/rbac/api/menus/', 'method': 'POST', 'group': permission_group, 'description': '创建新菜单'},
            {'name': '获取菜单详情', 'path': '/rbac/api/menus/{id}/', 'method': 'GET', 'group': permission_group, 'description': '获取菜单详细信息'},
            {'name': '更新菜单', 'path': '/rbac/api/menus/{id}/', 'method': 'PUT', 'group': permission_group, 'description': '更新菜单信息'},
            {'name': '删除菜单', 'path': '/rbac/api/menus/{id}/', 'method': 'DELETE', 'group': permission_group, 'description': '删除菜单'},
            {'name': '获取菜单树', 'path': '/rbac/api/menus/tree/', 'method': 'GET', 'group': permission_group, 'description': '获取菜单树结构'},
            
            # API管理API
            {'name': '获取API分组列表', 'path': '/rbac/api/api-groups/', 'method': 'GET', 'group': permission_group, 'description': '获取API分组列表'},
            {'name': '创建API分组', 'path': '/rbac/api/api-groups/', 'method': 'POST', 'group': permission_group, 'description': '创建新API分组'},
            {'name': '获取API分组详情', 'path': '/rbac/api/api-groups/{id}/', 'method': 'GET', 'group': permission_group, 'description': '获取API分组详细信息'},
            {'name': '更新API分组', 'path': '/rbac/api/api-groups/{id}/', 'method': 'PUT', 'group': permission_group, 'description': '更新API分组信息'},
            {'name': '删除API分组', 'path': '/rbac/api/api-groups/{id}/', 'method': 'DELETE', 'group': permission_group, 'description': '删除API分组'},
            {'name': '获取API列表', 'path': '/rbac/api/apis/', 'method': 'GET', 'group': permission_group, 'description': '获取API列表'},
            {'name': '创建API', 'path': '/rbac/api/apis/', 'method': 'POST', 'group': permission_group, 'description': '创建新API'},
            {'name': '获取API详情', 'path': '/rbac/api/apis/{id}/', 'method': 'GET', 'group': permission_group, 'description': '获取API详细信息'},
            {'name': '更新API', 'path': '/rbac/api/apis/{id}/', 'method': 'PUT', 'group': permission_group, 'description': '更新API信息'},
            {'name': '删除API', 'path': '/rbac/api/apis/{id}/', 'method': 'DELETE', 'group': permission_group, 'description': '删除API'},
            
            # 业务管理API - 文章管理
            {'name': '获取文章列表', 'path': '/business_demo/api/articles/', 'method': 'GET', 'group': business_group, 'description': '获取文章列表'},
            {'name': '创建文章', 'path': '/business_demo/api/articles/', 'method': 'POST', 'group': business_group, 'description': '创建新文章'},
            {'name': '获取文章详情', 'path': '/business_demo/api/articles/{id}/', 'method': 'GET', 'group': business_group, 'description': '获取文章详细信息'},
            {'name': '更新文章', 'path': '/business_demo/api/articles/{id}/', 'method': 'PUT', 'group': business_group, 'description': '更新文章信息'},
            {'name': '删除文章', 'path': '/business_demo/api/articles/{id}/', 'method': 'DELETE', 'group': business_group, 'description': '删除文章'},
            {'name': '发布文章', 'path': '/business_demo/api/articles/{id}/publish/', 'method': 'POST', 'group': business_group, 'description': '发布文章'},
            {'name': '查看文章', 'path': '/business_demo/api/articles/{id}/view/', 'method': 'POST', 'group': business_group, 'description': '查看文章'},
            {'name': '我的文章', 'path': '/business_demo/api/articles/my_articles/', 'method': 'GET', 'group': business_group, 'description': '获取我的文章'},
            {'name': '公开文章', 'path': '/business_demo/api/articles/public_articles/', 'method': 'GET', 'group': business_group, 'description': '获取公开文章'},
            
            # 业务管理API - 项目管理
            {'name': '获取项目列表', 'path': '/business_demo/api/projects/', 'method': 'GET', 'group': business_group, 'description': '获取项目列表'},
            {'name': '创建项目', 'path': '/business_demo/api/projects/', 'method': 'POST', 'group': business_group, 'description': '创建新项目'},
            {'name': '获取项目详情', 'path': '/business_demo/api/projects/{id}/', 'method': 'GET', 'group': business_group, 'description': '获取项目详细信息'},
            {'name': '更新项目', 'path': '/business_demo/api/projects/{id}/', 'method': 'PUT', 'group': business_group, 'description': '更新项目信息'},
            {'name': '删除项目', 'path': '/business_demo/api/projects/{id}/', 'method': 'DELETE', 'group': business_group, 'description': '删除项目'},
            {'name': '更新项目进度', 'path': '/business_demo/api/projects/{id}/update_progress/', 'method': 'POST', 'group': business_group, 'description': '更新项目进度'},
            {'name': '部门项目', 'path': '/business_demo/api/projects/department_projects/', 'method': 'GET', 'group': business_group, 'description': '获取部门项目'},
            {'name': '项目统计', 'path': '/business_demo/api/projects/statistics/', 'method': 'GET', 'group': business_group, 'description': '获取项目统计'},
            
            # 业务管理API - 文档管理
            {'name': '获取文档列表', 'path': '/business_demo/api/documents/', 'method': 'GET', 'group': business_group, 'description': '获取文档列表'},
            {'name': '创建文档', 'path': '/business_demo/api/documents/', 'method': 'POST', 'group': business_group, 'description': '创建新文档'},
            {'name': '获取文档详情', 'path': '/business_demo/api/documents/{id}/', 'method': 'GET', 'group': business_group, 'description': '获取文档详细信息'},
            {'name': '更新文档', 'path': '/business_demo/api/documents/{id}/', 'method': 'PUT', 'group': business_group, 'description': '更新文档信息'},
            {'name': '删除文档', 'path': '/business_demo/api/documents/{id}/', 'method': 'DELETE', 'group': business_group, 'description': '删除文档'},
            {'name': '下载文档', 'path': '/business_demo/api/documents/{id}/download/', 'method': 'POST', 'group': business_group, 'description': '下载文档'},
            {'name': '按类型获取文档', 'path': '/business_demo/api/documents/by_type/', 'method': 'GET', 'group': business_group, 'description': '按类型获取文档'},
            
            # 业务管理API - 任务管理
            {'name': '获取任务列表', 'path': '/business_demo/api/tasks/', 'method': 'GET', 'group': business_group, 'description': '获取任务列表'},
            {'name': '创建任务', 'path': '/business_demo/api/tasks/', 'method': 'POST', 'group': business_group, 'description': '创建新任务'},
            {'name': '获取任务详情', 'path': '/business_demo/api/tasks/{id}/', 'method': 'GET', 'group': business_group, 'description': '获取任务详细信息'},
            {'name': '更新任务', 'path': '/business_demo/api/tasks/{id}/', 'method': 'PUT', 'group': business_group, 'description': '更新任务信息'},
            {'name': '删除任务', 'path': '/business_demo/api/tasks/{id}/', 'method': 'DELETE', 'group': business_group, 'description': '删除任务'},
            {'name': '分配任务', 'path': '/business_demo/api/tasks/{id}/assign/', 'method': 'POST', 'group': business_group, 'description': '分配任务'},
            {'name': '完成任务', 'path': '/business_demo/api/tasks/{id}/complete/', 'method': 'POST', 'group': business_group, 'description': '完成任务'},
            {'name': '我的任务', 'path': '/business_demo/api/tasks/my_tasks/', 'method': 'GET', 'group': business_group, 'description': '获取我的任务'},
        ]
        
        for api_data in apis_data:
            Api.objects.get_or_create(
                path=api_data['path'],
                method=api_data['method'],
                defaults=api_data
            )
