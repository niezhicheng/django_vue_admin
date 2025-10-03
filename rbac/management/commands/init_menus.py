"""
重新初始化菜单数据 - 动态对接前端
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from rbac.models import Menu


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
            
            # 用户管理按钮权限
            {
                'name': 'user-add',
                'title': '新增用户',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 1,
                'permission_code': 'system:user:add',
                'parent': 'user',
                'visible': False,  # 按钮不显示在菜单中
                'is_hidden': True,
            },
            {
                'name': 'user-edit',
                'title': '编辑用户',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 2,
                'permission_code': 'system:user:edit',
                'parent': 'user',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'user-delete',
                'title': '删除用户',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 3,
                'permission_code': 'system:user:delete',
                'parent': 'user',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'user-export',
                'title': '导出用户',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 4,
                'permission_code': 'system:user:export',
                'parent': 'user',
                'visible': False,
                'is_hidden': True,
            },
            
            # 角色管理按钮权限
            {
                'name': 'role-add',
                'title': '新增角色',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 1,
                'permission_code': 'system:role:add',
                'parent': 'role',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'role-edit',
                'title': '编辑角色',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 2,
                'permission_code': 'system:role:edit',
                'parent': 'role',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'role-delete',
                'title': '删除角色',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 3,
                'permission_code': 'system:role:delete',
                'parent': 'role',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'role-assign-menu',
                'title': '分配菜单',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 4,
                'permission_code': 'system:role:assign_menu',
                'parent': 'role',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'role-assign-api',
                'title': '分配API',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 5,
                'permission_code': 'system:role:assign_api',
                'parent': 'role',
                'visible': False,
                'is_hidden': True,
            },
            
            # 菜单管理按钮权限
            {
                'name': 'menu-add',
                'title': '新增菜单',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 1,
                'permission_code': 'system:menu:add',
                'parent': 'menu',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'menu-edit',
                'title': '编辑菜单',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 2,
                'permission_code': 'system:menu:edit',
                'parent': 'menu',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'menu-delete',
                'title': '删除菜单',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 3,
                'permission_code': 'system:menu:delete',
                'parent': 'menu',
                'visible': False,
                'is_hidden': True,
            },
            
            # API管理按钮权限
            {
                'name': 'api-add',
                'title': '新增API',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 1,
                'permission_code': 'system:api:add',
                'parent': 'api',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'api-edit',
                'title': '编辑API',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 2,
                'permission_code': 'system:api:edit',
                'parent': 'api',
                'visible': False,
                'is_hidden': True,
            },
            {
                'name': 'api-delete',
                'title': '删除API',
                'icon': None,
                'path': None,
                'component': None,
                'menu_type': 3,  # 按钮
                'sort_order': 3,
                'permission_code': 'system:api:delete',
                'parent': 'api',
                'visible': False,
                'is_hidden': True,
            },
        ]

        # 创建菜单映射，用于处理父子关系
        menu_map = {}
        
        # 第一遍：创建所有菜单（不设置parent）
        for menu_data in menus_data:
            parent_name = menu_data.pop('parent', None)
            
            menu, created = Menu.objects.get_or_create(
                name=menu_data['name'],
                defaults={
                    **menu_data,
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
