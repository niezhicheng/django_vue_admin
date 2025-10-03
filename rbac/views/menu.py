"""
菜单相关视图
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Menu
from ..serializers import MenuSerializer
from ..utils import ApiResponse
from ..permissions import CasbinPermission


class MenuViewSet(viewsets.ModelViewSet):
    """菜单管理视图集"""
    model = Menu
    serializer_class = MenuSerializer
    permission_classes = [CasbinPermission]
    
    def get_queryset(self):
        """获取菜单查询集 - 只返回菜单和目录类型，不包含按钮"""
        return Menu.objects.filter(
            status=True,
            menu_type__in=[1, 2]  # 1=目录, 2=菜单, 3=按钮
        ).order_by('sort_order', 'created_at')
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取菜单树"""
        def build_tree(menus, parent_id=None):
            tree = []
            for menu in menus:
                if menu.parent_id == parent_id:
                    children = build_tree(menus, menu.id)
                    tree.append({
                        'id': menu.id,
                        'name': menu.name,
                        'title': menu.title,
                        'icon': menu.icon,
                        'path': menu.path,
                        'component': menu.component,
                        'menu_type': menu.menu_type,
                        'menu_type_display': menu.menu_type_display,
                        'permission_code': menu.permission_code,
                        'sort_order': menu.sort_order,
                        'visible': menu.visible,
                        'children': children
                    })
            return tree
        
        menus = list(self.get_queryset())
        tree_data = build_tree(menus)
        
        return ApiResponse.success(data=tree_data, message="获取菜单树成功")
