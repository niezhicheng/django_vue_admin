"""
权限相关视图
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Role, PolicyRule, RoleMenu
from ..utils import ApiResponse


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_role_api_permissions(request, role_id):
    """获取角色的API权限"""
    try:
        role = get_object_or_404(Role, id=role_id)
        
        # 获取角色的权限策略
        policies = PolicyRule.objects.filter(role_id=role.role_id)
        
        # 获取API信息
        from ..models import Api
        apis = []
        for policy in policies:
            # 模糊匹配API路径
            matching_apis = Api.objects.filter(
                path__icontains=policy.path.replace('*', ''),
                method__iexact=policy.method
            )
            for api in matching_apis:
                apis.append({
                    'id': api.id,
                    'name': api.name,
                    'path': api.path,
                    'method': api.method,
                    'description': api.description or 'API已删除或不存在'
                })
        
        return ApiResponse.success(data=apis, message="获取API权限成功")
    except Exception as e:
        return ApiResponse.error(message="获取API权限失败")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_role_api_permissions(request, role_id):
    """分配角色的API权限"""
    try:
        role = get_object_or_404(Role, id=role_id)
        api_ids = request.data.get('api_ids', [])
        
        # 去重
        api_ids = list(set(api_ids))
        
        # 删除现有权限
        PolicyRule.objects.filter(role_id=role.role_id).delete()
        
        # 添加新权限
        from ..models import Api
        for api_id in api_ids:
            try:
                api = Api.objects.get(id=api_id)
                PolicyRule.objects.create(
                    role_id=role.role_id,
                    path=api.path,
                    method=api.method
                )
            except Api.DoesNotExist:
                continue
        
        return ApiResponse.success(message="API权限分配成功")
    except Exception as e:
        return ApiResponse.error(message="API权限分配失败")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_role_menu_permissions(request, role_id):
    """获取角色的菜单权限"""
    try:
        role = get_object_or_404(Role, id=role_id)
        
        # 获取角色的菜单权限
        role_menus = RoleMenu.objects.filter(role=role).select_related('menu')
        
        menus = []
        for rm in role_menus:
            menu = rm.menu
            menus.append({
                'id': menu.id,
                'name': menu.name,
                'title': menu.title,
                'icon': menu.icon,
                'path': menu.path,
                'component': menu.component,
                'menu_type': menu.menu_type,
                'menu_type_display': menu.menu_type_display,
                'permission_code': menu.permission_code,
                'parent_id': menu.parent.id if menu.parent else None,
                'parent_title': menu.parent.title if menu.parent else None,
                'sort_order': menu.sort_order,
                'visible': menu.visible,
                'status': menu.status
            })
        
        return ApiResponse.success(data=menus, message="获取菜单权限成功")
    except Exception as e:
        return ApiResponse.error(message="获取菜单权限失败")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_role_menu_permissions(request, role_id):
    """分配角色的菜单权限"""
    try:
        role = get_object_or_404(Role, id=role_id)
        menu_ids = request.data.get('menu_ids', [])
        
        # 去重
        menu_ids = list(set(menu_ids))
        
        # 删除现有权限
        RoleMenu.objects.filter(role=role).delete()
        
        # 添加新权限
        for menu_id in menu_ids:
            try:
                from ..models import Menu
                menu = Menu.objects.get(id=menu_id)
                RoleMenu.objects.create(role=role, menu=menu)
            except Menu.DoesNotExist:
                continue
        
        return ApiResponse.success(message="菜单权限分配成功")
    except Exception as e:
        return ApiResponse.error(message="菜单权限分配失败")
