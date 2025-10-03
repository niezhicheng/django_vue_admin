"""
认证相关视图
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ..utils import ApiResponse
from ..models import User, UserRole, Menu, RoleMenu


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义JWT序列化器"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # 添加用户信息到响应中
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_superuser': self.user.is_superuser,
        }
        
        # 重命名token字段以匹配前端期望
        data['access_token'] = data.pop('access')
        data['refresh_token'] = data.pop('refresh')
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义JWT登录视图"""
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """自定义JWT刷新视图"""
    pass


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jwt_profile_view(request):
    """JWT用户信息视图"""
    try:
        user = request.user
        
        # 获取用户角色
        user_roles = UserRole.objects.filter(user=user).select_related('role')
        roles = [{'id': ur.role.id, 'name': ur.role.name, 'code': ur.role.code} for ur in user_roles]
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'department': {
                'id': user.department.id,
                'name': user.department.name
            } if user.department else None,
            'data_scope': user.data_scope,
            'is_superuser': user.is_superuser,
            'roles': roles
        }
        
        return ApiResponse.success(data=user_data, message="获取用户信息成功")
    except Exception as e:
        return ApiResponse.error(message="获取用户信息失败")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_menus_view(request):
    """用户菜单视图"""
    try:
        user = request.user
        
        if user.is_superuser:
            # 超级用户返回所有菜单
            menus = Menu.objects.filter(status=True, visible=True).order_by('sort_order')
        else:
            # 普通用户根据角色获取菜单
            user_roles = UserRole.objects.filter(user=user).values_list('role_id', flat=True)
            role_menus = RoleMenu.objects.filter(role_id__in=user_roles).values_list('menu_id', flat=True)
            menus = Menu.objects.filter(
                id__in=role_menus, 
                status=True, 
                visible=True
            ).order_by('sort_order')
        
        menu_data = []
        for menu in menus:
            menu_data.append({
                'id': menu.id,
                'name': menu.name,
                'title': menu.title,
                'icon': menu.icon,
                'path': menu.path,
                'component': menu.component,
                'redirect': menu.redirect,
                'menu_type': menu.menu_type,
                'menu_type_display': menu.menu_type_display,
                'permission_code': menu.permission_code,
                'parent_id': menu.parent.id if menu.parent else None,
                'parent_title': menu.parent.title if menu.parent else None,
                'sort_order': menu.sort_order,
                'is_hidden': menu.is_hidden,
                'is_keep_alive': menu.is_keep_alive,
                'is_affix': menu.is_affix,
                'is_frame': menu.is_frame,
                'frame_src': menu.frame_src,
                'visible': menu.visible,
                'status': menu.status,
                'children_count': menu.children.count(),
                'breadcrumb': [menu.title],
                'created_at': menu.created_at,
                'updated_at': menu.updated_at
            })
        
        return ApiResponse.success(data=menu_data, message="获取用户菜单成功")
    except Exception as e:
        return ApiResponse.error(message="获取用户菜单失败")
