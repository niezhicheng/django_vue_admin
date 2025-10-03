"""
重新初始化菜单数据 - 动态对接前端
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from rbac.models import Menu, User, Role, UserRole
from rbac.simple_rbac import simple_rbac_manager


class Command(BaseCommand):
    help = '重新初始化菜单数据，动态对接前端'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除现有菜单数据',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('清除现有菜单数据...')
            Menu.objects.all().delete()
            self.stdout.write('菜单数据已清除')

        self.stdout.write('正在初始化菜单数据...')
        self.init_menus()
        self.stdout.write('菜单数据初始化完成')

    def init_menus(self):
        """初始化菜单数据 - 重新设计为动态对接前端"""
        menus_data = [
            # 仪表板 - 首页
            {
                'name': 'dashboard',
                'title': '仪表板',
                'icon': 'Dashboard',
                'path': '/dashboard',
                'component': 'dashboard/index',
                'menu_type': 2,  # 菜单
                'sort_order': 1,
                'permission_code': 'dashboard',
                'parent': None,
                'visible': True,
                'is_hidden': False,
            },
            
            # 系统管理目录
            {
                'name': 'system',
                'title': '系统管理',
                'icon': 'Setting',
                'path': '/system',
                'component': 'Layout',
                'redirect': '/system/user',
                'menu_type': 1,  # 目录
                'sort_order': 2,
                'permission_code': 'system',
                'parent': None,
                'visible': True,
                'is_hidden': False,
            },
            
            # 系统管理下的菜单
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
                'visible': True,
                'is_hidden': False,
            },
            {
                'name': 'role',
                'title': '角色管理',
                'icon': 'UserGroup',
                'path': '/system/role',
                'component': 'system/role/index',
                'menu_type': 2,  # 菜单
                'sort_order': 2,
                'permission_code': 'system:role:list',
                'parent': 'system',
                'visible': True,
                'is_hidden': False,
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
                'visible': True,
                'is_hidden': False,
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
                'visible': True,
                'is_hidden': False,
            },
            
            # API管理
            {
                'name': 'api',
                'title': 'API管理',
                'icon': 'Api',
                'path': '/system/api',
                'component': 'system/api/index',
                'menu_type': 2,  # 菜单
                'sort_order': 5,
                'permission_code': 'system:api:list',
                'parent': 'system',
                'visible': True,
                'is_hidden': False,
            },
            
            # 业务管理目录
            {
                'name': 'business',
                'title': '业务管理',
                'icon': 'Document',
                'path': '/business',
                'component': 'Layout',
                'redirect': '/business/article',
                'menu_type': 1,  # 目录
                'sort_order': 3,
                'permission_code': 'business',
                'parent': None,
                'visible': True,
                'is_hidden': False,
            },
            
            # 业务管理下的菜单
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
                'visible': True,
                'is_hidden': False,
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
                'visible': True,
                'is_hidden': False,
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
                'visible': True,
                'is_hidden': False,
            },
            
            # 注意：按钮权限已移除，菜单管理只显示菜单和目录类型
        ]

        # 创建菜单映射，用于处理父子关系
        menu_map = {}
        
        # 第一遍：创建所有菜单（不设置parent）
        for menu_data in menus_data:
            # 保存parent信息，但不从menu_data中移除
            parent_name = menu_data.get('parent')
            
            # 创建菜单时排除parent字段
            menu_create_data = {k: v for k, v in menu_data.items() if k != 'parent'}
            
            menu, created = Menu.objects.get_or_create(
                name=menu_data['name'],
                defaults={
                    **menu_create_data,
                    'created_at': timezone.now(),
                }
            )
            
            if created:
                self.stdout.write(f'创建菜单: {menu.title} ({menu.get_menu_type_display()})')
            
            menu_map[menu_data['name']] = menu
        
        # 第二遍：设置父子关系
        for menu_data in menus_data:
            parent_name = menu_data.get('parent')
            if parent_name and parent_name in menu_map:
                menu = menu_map[menu_data['name']]
                parent_menu = menu_map[parent_name]
                menu.parent = parent_menu
                menu.save()
                self.stdout.write(f'设置菜单关系: {parent_menu.title} -> {menu.title}')

        self.stdout.write(f'菜单初始化完成，共创建 {len(menu_map)} 个菜单项')
        
        # 初始化用户和权限
        self.init_users_and_permissions()
    
    def init_users_and_permissions(self):
        """初始化用户和权限"""
        self.stdout.write('正在初始化用户和权限...')
        
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
            self.stdout.write('更新admin用户为超级用户')
        else:
            self.stdout.write('创建admin用户')
        
        # 设置admin用户密码
        admin_user.set_password('admin123')
        admin_user.save()
        
        # 初始化角色权限
        self.init_role_permissions()
        
        self.stdout.write('用户和权限初始化完成')
    
    def init_role_permissions(self):
        """初始化角色权限"""
        # 给admin角色添加所有菜单管理权限
        menu_permissions = [
            ('/rbac/api/menus/', 'GET'),
            ('/rbac/api/menus/', 'POST'),
            ('/rbac/api/menus/{id}/', 'PUT'),
            ('/rbac/api/menus/{id}/', 'DELETE'),
            ('/rbac/api/menus/tree/', 'GET'),
        ]
        
        for path, method in menu_permissions:
            simple_rbac_manager.add_role_policy('admin', path, method)
        
        self.stdout.write('已为admin角色添加菜单管理权限')
