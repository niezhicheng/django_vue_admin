"""
简化的RBAC视图
"""
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
import json

from .models import User, Role, UserRole, Department, Menu, RoleMenu, DataPermissionManager, ApiGroup, Api, ApiLog, PolicyRule
from .response import ApiResponse
from .simple_rbac import simple_rbac_manager, SimpleRBACPermission
from .serializers import (
    MultiSerializerMixin, BaseModelViewSet,
    UserListSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer, UserPasswordResetSerializer,
    RoleListSerializer, RoleDetailSerializer, RoleCreateSerializer, RoleUpdateSerializer,
    DepartmentSerializer, MenuSerializer, ApiGroupSerializer, ApiSerializer, ApiLogSerializer, RoleMenuSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义JWT Token获取视图"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # 获取用户信息
            username = request.data.get('username')
            try:
                user = User.objects.get(username=username)
                roles = simple_rbac_manager.get_user_roles(user.username)
                
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': getattr(user, 'phone', ''),
                    'avatar': getattr(user, 'avatar', ''),
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'roles': roles,
                }
                
                # 将用户信息添加到响应中，并重命名字段以匹配前端期望
                response.data['access_token'] = response.data['access']
                response.data['refresh_token'] = response.data['refresh']
                response.data['user'] = user_data
                response.data['message'] = '登录成功'
                # 删除原始字段
                del response.data['access']
                del response.data['refresh']
                
            except User.DoesNotExist:
                pass
        
        return response


class AuthView:
    """认证视图"""
    
    @staticmethod
    @csrf_exempt
    def login_view(request):
        """用户登录（JWT版本）"""
        if request.method != 'POST':
            return ApiResponse.method_not_allowed()
        
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return ApiResponse.validation_error("用户名和密码不能为空")
            
            user = authenticate(request, username=username, password=password)
            if user:
                if not user.is_active:
                    return ApiResponse.error("账户已被禁用")
                
                # 生成JWT token
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                # 获取用户角色信息
                roles = simple_rbac_manager.get_user_roles(user.username)
                
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': getattr(user, 'phone', ''),
                    'avatar': getattr(user, 'avatar', ''),
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'roles': roles,
                }
                
                response_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user_data,
                }
                
                return ApiResponse.success(data=response_data, message="登录成功")
            else:
                return ApiResponse.unauthorized("用户名或密码错误")
        
        except json.JSONDecodeError:
            return ApiResponse.validation_error("无效的JSON数据")
        except Exception as e:
            return ApiResponse.server_error(f"登录失败: {str(e)}")
    
    @staticmethod
    @csrf_exempt
    def logout_view(request):
        """用户登出（JWT版本）"""
        # JWT是无状态的，登出主要在前端处理（删除token）
        return ApiResponse.success(message="登出成功")
    
    @staticmethod
    @csrf_exempt
    def profile_view(request):
        """获取用户信息"""
        if not request.user.is_authenticated:
            return ApiResponse.unauthorized()
        
        user = request.user
        roles = simple_rbac_manager.get_user_roles(user.username)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', ''),
            'avatar': getattr(user, 'avatar', ''),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'roles': roles,
        }
        
        return ApiResponse.success(data=user_data, message="获取用户信息成功")


@csrf_exempt
def check_permission_view(request):
    """检查权限API"""
    if request.method != 'POST':
        return ApiResponse.method_not_allowed()
    
    if not request.user.is_authenticated:
        return ApiResponse.unauthorized()
    
    try:
        data = json.loads(request.body)
        url_path = data.get('url_path')
        method = data.get('method', 'GET')
        
        if not url_path:
            return ApiResponse.validation_error("url_path参数不能为空")
        
        has_permission = simple_rbac_manager.check_permission(
            request.user, url_path, method
        )
        
        check_result = {
            'has_permission': has_permission,
            'url_path': url_path,
            'method': method,
            'user': request.user.username
        }
        
        return ApiResponse.success(data=check_result, message="权限检查完成")
    
    except json.JSONDecodeError:
        return ApiResponse.validation_error("无效的JSON数据")
    except Exception as e:
        return ApiResponse.server_error(f"权限检查失败: {str(e)}")


# 简化的API视图集（可选）
class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理视图集"""
    queryset = Department.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """根据数据权限过滤查询集"""
        queryset = Department.objects.filter(status=True).select_related('parent')
        # Department模型没有created_by字段，使用特殊处理
        data_scope, department_ids = DataPermissionManager.get_user_data_scope(self.request.user)
        
        if data_scope == 1:  # 全部数据
            return queryset
        elif data_scope == 2 or data_scope == 3:  # 部门数据
            if not department_ids:
                return queryset.none()
            return queryset.filter(id__in=department_ids)
        elif data_scope == 4:  # 本人数据
            # 部门数据权限为本人时，只能看到自己所属的部门
            if self.request.user.department:
                return queryset.filter(id=self.request.user.department.id)
            return queryset.none()
        
        return queryset.none()
    
    def list(self, request, *args, **kwargs):
        """获取部门列表"""
        queryset = self.get_queryset()
        departments = []
        
        for dept in queryset:
            departments.append({
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'parent_id': dept.parent.id if dept.parent else None,
                'parent_name': dept.parent.name if dept.parent else None,
                'level': dept.level,
                'sort_order': dept.sort_order,
                'leader': dept.leader,
                'phone': dept.phone,
                'email': dept.email,
                'status': dept.status,
                'created_at': dept.created_at,
                'path': dept.get_parent_path(),
            })
        
        return ApiResponse.success(data=departments, message="获取部门列表成功")
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """获取子部门"""
        try:
            department = self.get_object()
            children = department.get_children()
            
            children_data = []
            for child in children:
                children_data.append({
                    'id': child.id,
                    'name': child.name,
                    'code': child.code,
                    'level': child.level,
                    'sort_order': child.sort_order,
                    'leader': child.leader,
                    'status': child.status,
                })
            
            return ApiResponse.success(data=children_data, message="获取子部门成功")
        except Department.DoesNotExist:
            return ApiResponse.not_found("部门不存在")
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取部门树"""
        def build_tree(departments, parent_id=None):
            tree = []
            for dept in departments:
                if dept.parent_id == parent_id:
                    children = build_tree(departments, dept.id)
                    tree.append({
                        'id': dept.id,
                        'name': dept.name,
                        'code': dept.code,
                        'level': dept.level,
                        'sort_order': dept.sort_order,
                        'leader': dept.leader,
                        'status': dept.status,
                        'children': children
                    })
            return tree
        
        departments = list(self.get_queryset().order_by('sort_order', 'level'))
        tree_data = build_tree(departments)
        
        return ApiResponse.success(data=tree_data, message="获取部门树成功")


class UserViewSet(BaseModelViewSet):
    """
    用户管理视图集 - 使用新的基类
    
    使用示例：
    class MyViewSet(BaseModelViewSet):
        model = MyModel  # 只需要定义模型
        serializer_class = MyListSerializer  # 默认序列化器
        create_serializer_class = MyCreateSerializer  # 创建时使用
        update_serializer_class = MyUpdateSerializer  # 更新时使用
        detail_serializer_class = MyDetailSerializer  # 详情时使用（可选）
        
        # 可选配置
        permission_classes = [IsAuthenticated]
        filter_fields = ['name', 'status']
        search_fields = ['name', 'description']
        ordering_fields = ['created_at', 'updated_at']
        ordering = ['-created_at']
    """
    model = User
    permission_classes = [IsAuthenticated]
    
    # 定义序列化器
    serializer_class = UserListSerializer  # 默认序列化器（用于list和retrieve）
    create_serializer_class = UserCreateSerializer  # 创建时使用
    update_serializer_class = UserUpdateSerializer  # 更新时使用
    detail_serializer_class = UserDetailSerializer  # 详情时使用
    
    def get_queryset(self):
        """根据数据权限过滤查询集"""
        queryset = User.objects.select_related('department').filter(is_active=True)
        # User模型没有created_by字段，使用特殊处理
        data_scope, department_ids = DataPermissionManager.get_user_data_scope(self.request.user)
        
        if data_scope == 1:  # 全部数据
            return queryset
        elif data_scope == 2 or data_scope == 3:  # 部门数据
            if not department_ids:
                return queryset.none()
            return queryset.filter(department_id__in=department_ids)
        elif data_scope == 4:  # 本人数据
            return queryset.filter(id=self.request.user.id)
        
        return queryset.none()
    
    def list(self, request, *args, **kwargs):
        """获取用户列表"""
        queryset = self.get_queryset()
        users = []
        
        for user in queryset:
            # 获取用户角色
            user_roles = UserRole.objects.filter(user=user).select_related('role')
            roles_data = []
            for ur in user_roles:
                roles_data.append({
                    'id': ur.role.id,
                    'role_id': ur.role.role_id,
                    'name': ur.role.name,
                    'data_scope': ur.role.data_scope,
                })
            
            # 获取用户数据权限
            data_scope, _ = DataPermissionManager.get_user_data_scope(user)
            
            users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'avatar': user.avatar,
                'position': user.position,
                'department': {
                    'id': user.department.id,
                    'name': user.department.name,
                    'code': user.department.code,
                } if user.department else None,
                'roles': roles_data,
                'data_scope': data_scope,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'created_at': user.created_at,
            })
        
        return ApiResponse.success(data=users, message="获取用户列表成功")
    
    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """重置用户密码"""
        user = self.get_object()
        serializer = UserPasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user)
            return ApiResponse.success(message="密码重置成功")
        else:
            return ApiResponse.error(message="密码重置失败", data=serializer.errors)
    
    @action(detail=True, methods=['get'])
    def data_scope(self, request, pk=None):
        """获取用户数据权限范围"""
        try:
            user = self.get_object()
            data_scope, department_ids = DataPermissionManager.get_user_data_scope(user)
            
            # 获取数据权限描述
            scope_desc = dict(Role.DATA_SCOPE_CHOICES).get(data_scope, '未知')
            
            return ApiResponse.success(
                data={
                    'user_id': user.id,
                    'username': user.username,
                    'data_scope': data_scope,
                    'data_scope_desc': scope_desc,
                    'department_ids': department_ids,
                    'department': {
                        'id': user.department.id,
                        'name': user.department.name,
                    } if user.department else None,
                },
                message="获取用户数据权限成功"
            )
        except User.DoesNotExist:
            return ApiResponse.not_found("用户不存在")
    
    @action(detail=True, methods=['post'])
    def set_custom_scope(self, request, pk=None):
        """设置用户自定义数据权限"""
        try:
            user = self.get_object()
            data = json.loads(request.body) if request.body else {}
            data_scope = data.get('data_scope')
            
            # 验证数据权限值
            valid_scopes = [1, 2, 3, 4, None]
            if data_scope not in valid_scopes:
                return ApiResponse.validation_error("无效的数据权限值")
            
            # 设置自定义权限
            DataPermissionManager.set_user_custom_scope(user, data_scope)
            
            # 获取权限描述
            perm_desc = DataPermissionManager.get_permission_description(user)
            
            return ApiResponse.success(
                data=perm_desc,
                message="用户数据权限设置成功"
            )
        except User.DoesNotExist:
            return ApiResponse.not_found("用户不存在")
        except json.JSONDecodeError:
            return ApiResponse.validation_error("无效的JSON数据")
        except Exception as e:
            return ApiResponse.server_error(f"设置权限失败: {str(e)}")
    
    @action(detail=True, methods=['get'])
    def permission_info(self, request, pk=None):
        """获取用户完整权限信息"""
        try:
            user = self.get_object()
            perm_desc = DataPermissionManager.get_permission_description(user)
            
            # 获取用户角色信息
            user_roles = UserRole.objects.filter(user=user).select_related('role')
            roles_info = []
            for ur in user_roles:
                roles_info.append({
                    'id': ur.role.id,
                    'role_id': ur.role.role_id,
                    'name': ur.role.name,
                    'data_scope': ur.role.data_scope,
                    'data_scope_desc': ur.role.get_data_scope_display(),
                })
            
            return ApiResponse.success(
                data={
                    'user_id': user.id,
                    'username': user.username,
                    'department': {
                        'id': user.department.id,
                        'name': user.department.name,
                        'code': user.department.code,
                    } if user.department else None,
                    'custom_data_scope': user.custom_data_scope,
                    'roles': roles_info,
                    'effective_permission': perm_desc,
                },
                message="获取用户权限信息成功"
            )
        except User.DoesNotExist:
            return ApiResponse.not_found("用户不存在")


class MenuViewSet(viewsets.ModelViewSet):
    """菜单管理视图集"""
    queryset = Menu.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取菜单查询集"""
        return Menu.objects.filter(status=True).select_related('parent').order_by('sort_order')

    def list(self, request, *args, **kwargs):
        """获取菜单列表"""
        queryset = self.get_queryset()
        menus = []

        for menu in queryset:
            menus.append({
                'id': menu.id,
                'name': menu.name,
                'title': menu.title,
                'icon': menu.icon,
                'path': menu.path,
                'component': menu.component,
                'redirect': menu.redirect,
                'menu_type': menu.menu_type,
                'menu_type_display': menu.get_menu_type_display(),
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
                'created_at': menu.created_at,
                'breadcrumb': menu.get_breadcrumb(),
            })

        return ApiResponse.success(data=menus, message="获取菜单列表成功")

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取菜单树"""
        def build_menu_tree(menus, parent_id=None):
            tree = []
            for menu in menus:
                if menu.parent_id == parent_id:
                    children = build_menu_tree(menus, menu.id)
                    menu_data = {
                        'id': menu.id,
                        'name': menu.name,
                        'title': menu.title,
                        'icon': menu.icon,
                        'path': menu.path,
                        'component': menu.component,
                        'redirect': menu.redirect,
                        'menu_type': menu.menu_type,
                        'permission_code': menu.permission_code,
                        'sort_order': menu.sort_order,
                        'is_hidden': menu.is_hidden,
                        'is_keep_alive': menu.is_keep_alive,
                        'is_affix': menu.is_affix,
                        'is_frame': menu.is_frame,
                        'frame_src': menu.frame_src,
                        'visible': menu.visible,
                        'status': menu.status,
                        'children': children
                    }
                    tree.append(menu_data)
            return tree

        menus = list(self.get_queryset())
        tree_data = build_menu_tree(menus)

        return ApiResponse.success(data=tree_data, message="获取菜单树成功")

    @action(detail=False, methods=['get'])
    def routes(self, request):
        """获取路由菜单（前端路由用）"""
        def build_routes(menus, parent_id=None):
            routes = []
            for menu in menus:
                if menu.parent_id == parent_id and menu.visible and menu.status:
                    # 只返回目录和菜单类型，按钮类型不返回
                    if menu.menu_type in [1, 2]:
                        children = build_routes(menus, menu.id)
                        route_data = {
                            'id': menu.id,
                            'name': menu.name,
                            'path': menu.path,
                            'component': menu.component,
                            'redirect': menu.redirect,
                            'meta': {
                                'title': menu.title,
                                'icon': menu.icon,
                                'hidden': menu.is_hidden,
                                'keepAlive': menu.is_keep_alive,
                                'affix': menu.is_affix,
                                'frameSrc': menu.frame_src if menu.is_frame else None,
                                'permission': menu.permission_code,
                            }
                        }
                        if children:
                            route_data['children'] = children
                        routes.append(route_data)
            return routes

        # 只返回当前用户有权限的菜单
        user_menus = self.get_user_menus(request.user)
        routes_data = build_routes(user_menus)

        return ApiResponse.success(data=routes_data, message="获取路由菜单成功")

    def get_user_menus(self, user):
        """获取用户可访问的菜单"""
        if user.is_superuser:
            # 超级用户可以访问所有菜单
            return list(Menu.objects.filter(status=True, visible=True).order_by('sort_order'))
        
        # 获取用户角色对应的菜单
        user_roles = UserRole.objects.filter(user=user).select_related('role')
        role_ids = [ur.role.id for ur in user_roles]
        
        # 获取角色菜单关联
        role_menus = RoleMenu.objects.filter(role_id__in=role_ids).select_related('menu')
        menu_ids = [rm.menu.id for rm in role_menus]
        
        return list(Menu.objects.filter(
            id__in=menu_ids, 
            status=True, 
            visible=True
        ).order_by('sort_order'))


class RoleViewSet(BaseModelViewSet):
    """角色管理视图集 - 使用新的基类"""
    model = Role
    permission_classes = [IsAuthenticated]
    
    # 定义序列化器
    serializer_class = RoleListSerializer  # 默认序列化器（用于list和retrieve）
    create_serializer_class = RoleCreateSerializer  # 创建时使用
    update_serializer_class = RoleUpdateSerializer  # 更新时使用
    detail_serializer_class = RoleDetailSerializer  # 详情时使用
    
    def list(self, request, *args, **kwargs):
        """获取角色列表"""
        queryset = self.get_queryset()
        roles = []

        for role in queryset:
            # 获取角色关联的菜单
            role_menus = RoleMenu.objects.filter(role=role).select_related('menu')
            menus_data = []
            for rm in role_menus:
                menus_data.append({
                    'id': rm.menu.id,
                    'title': rm.menu.title,
                    'path': rm.menu.path,
                    'menu_type': rm.menu.menu_type,
                })

            roles.append({
                'id': role.id,
                'role_id': role.role_id,
                'name': role.name,
                'code': role.code,
                'description': role.description,
                'data_scope': role.data_scope,
                'data_scope_display': role.get_data_scope_display() if hasattr(role, 'get_data_scope_display') else '未知',
                'is_active': role.is_active,
                'created_at': role.created_at,
                'menus': menus_data,
                'menu_count': len(menus_data),
            })

        return ApiResponse.success(data=roles, message="获取角色列表成功")

    @action(detail=True, methods=['post'])
    def assign_menus(self, request, pk=None):
        """为角色分配菜单"""
        try:
            role = self.get_object()
            data = json.loads(request.body) if request.body else {}
            menu_ids = data.get('menu_ids', [])

            # 删除现有的菜单关联
            RoleMenu.objects.filter(role=role).delete()

            # 添加新的菜单关联
            created_count = 0
            for menu_id in menu_ids:
                try:
                    menu = Menu.objects.get(id=menu_id)
                    RoleMenu.objects.create(role=role, menu=menu)
                    created_count += 1
                except Menu.DoesNotExist:
                    pass

            return ApiResponse.success(
                data={'role_id': role.id, 'menu_count': created_count},
                message=f"角色菜单分配成功，共分配 {created_count} 个菜单"
            )
        except Role.DoesNotExist:
            return ApiResponse.not_found("角色不存在")
        except json.JSONDecodeError:
            return ApiResponse.validation_error("无效的JSON数据")
        except Exception as e:
            return ApiResponse.server_error(f"分配菜单失败: {str(e)}")

    @action(detail=True, methods=['get'])
    def get_menus(self, request, pk=None):
        """获取角色菜单"""
        try:
            role = self.get_object()
            role_menus = RoleMenu.objects.filter(role=role).select_related('menu')
            
            menus_data = []
            for rm in role_menus:
                menu = rm.menu
                menus_data.append({
                    'id': menu.id,
                    'name': menu.name,
                    'title': menu.title,
                    'icon': menu.icon,
                    'path': menu.path,
                    'component': menu.component,
                    'menu_type': menu.menu_type,
                    'menu_type_display': menu.get_menu_type_display(),
                    'permission_code': menu.permission_code,
                    'parent_id': menu.parent.id if menu.parent else None,
                    'sort_order': menu.sort_order,
                    'status': menu.status,
                })

            return ApiResponse.success(
                data={
                    'role_id': role.id,
                    'role_name': role.name,
                    'menus': menus_data,
                    'menu_count': len(menus_data),
                },
                message="获取角色菜单成功"
            )
        except Role.DoesNotExist:
            return ApiResponse.not_found("角色不存在")

    @csrf_exempt
    def assign_permissions(self, request, pk=None):
        """为角色分配权限"""
        if request.method != 'POST':
            return ApiResponse.method_not_allowed()
        
        try:
            role = self.get_object()
            data = json.loads(request.body)
            permissions = data.get('permissions', [])
            
            if not isinstance(permissions, list):
                return ApiResponse.validation_error("permissions必须是数组格式")
            
            success_count = 0
            for perm in permissions:
                url_pattern = perm.get('url_pattern')
                method = perm.get('method')
                
                if url_pattern and method:
                    success = simple_rbac_manager.add_role_policy(
                        role.code, url_pattern, method
                    )
                    if success:
                        success_count += 1
            
            return ApiResponse.success(
                data={'assigned_count': success_count},
                message=f"成功分配 {success_count} 个权限"
            )
            
        except json.JSONDecodeError:
            return ApiResponse.validation_error("无效的JSON数据")
        except Exception as e:
            return ApiResponse.server_error(f"分配权限失败: {str(e)}")
    
    @csrf_exempt
    @action(detail=True, methods=['get'])
    def get_role_permissions(self, request, pk=None):
        """获取角色权限"""
        try:
            role = self.get_object()
            policies = simple_rbac_manager.get_role_policies(role.code)
            
            permissions = []
            for policy in policies:
                if len(policy) >= 3:
                    permissions.append({
                        'url_pattern': policy[1],
                        'method': policy[2]
                    })
            
            return ApiResponse.success(
                data={'permissions': permissions},
                message="获取角色权限成功"
            )
            
        except Exception as e:
            return ApiResponse.server_error(f"获取权限失败: {str(e)}")


@csrf_exempt
def manage_role_permissions(request):
    """管理角色权限API"""
    if not request.user.is_authenticated:
        return ApiResponse.unauthorized()
    
    if request.method == 'POST':
        # 添加角色权限
        try:
            data = json.loads(request.body)
            role_code = data.get('role_code')
            url_pattern = data.get('url_pattern')
            method = data.get('method')
            
            if not all([role_code, url_pattern, method]):
                return ApiResponse.validation_error("role_code, url_pattern, method 都不能为空")
            
            success = simple_rbac_manager.add_role_policy(role_code, url_pattern, method)
            
            if success:
                return ApiResponse.success(message="权限添加成功")
            else:
                return ApiResponse.error("权限添加失败，可能已存在")
                
        except json.JSONDecodeError:
            return ApiResponse.validation_error("无效的JSON数据")
        except Exception as e:
            return ApiResponse.server_error(f"添加权限失败: {str(e)}")
    
    elif request.method == 'DELETE':
        # 删除角色权限
        try:
            data = json.loads(request.body)
            role_code = data.get('role_code')
            url_pattern = data.get('url_pattern')
            method = data.get('method')
            
            if not all([role_code, url_pattern, method]):
                return ApiResponse.validation_error("role_code, url_pattern, method 都不能为空")
            
            success = simple_rbac_manager.remove_role_policy(role_code, url_pattern, method)
            
            if success:
                return ApiResponse.success(message="权限删除成功")
            else:
                return ApiResponse.error("权限删除失败，可能不存在")
                
        except json.JSONDecodeError:
            return ApiResponse.validation_error("无效的JSON数据")
        except Exception as e:
            return ApiResponse.server_error(f"删除权限失败: {str(e)}")
    
    elif request.method == 'GET':
        # 获取角色权限
        role_code = request.GET.get('role_code')
        if not role_code:
            return ApiResponse.validation_error("role_code参数不能为空")
        
        try:
            policies = simple_rbac_manager.get_role_policies(role_code)
            permissions = []
            for policy in policies:
                if len(policy) >= 3:
                    permissions.append({
                        'role_code': policy[0],
                        'url_pattern': policy[1],
                        'method': policy[2]
                    })
            
            return ApiResponse.success(
                data={'permissions': permissions},
                message="获取角色权限成功"
            )
            
        except Exception as e:
            return ApiResponse.server_error(f"获取权限失败: {str(e)}")

    @action(detail=True, methods=['get'])
    def get_api_permissions(self, request, pk=None):
        """获取角色的API权限"""
        try:
            role = self.get_object()
            # 从PolicyRule表获取该角色的API权限
            policies = PolicyRule.objects.filter(
                role_id=str(role.id),
                is_active=True
            )
            
            api_permissions = []
            for policy in policies:
                # 查找对应的API
                try:
                    api = Api.objects.get(path=policy.url_pattern, method=policy.method)
                    api_permissions.append({
                        'id': api.id,
                        'name': api.name,
                        'path': api.path,
                        'method': api.method,
                        'method_display': api.get_method_display(),
                        'group_name': api.group.name if api.group else '',
                        'description': api.description
                    })
                except Api.DoesNotExist:
                    # 如果API不存在，仍然显示权限规则
                    api_permissions.append({
                        'id': f"policy_{policy.id}",
                        'name': f"{policy.method} {policy.url_pattern}",
                        'path': policy.url_pattern,
                        'method': policy.method,
                        'method_display': policy.method,
                        'group_name': '未知分组',
                        'description': 'API已删除或不存在'
                    })
            
            return ApiResponse.success(data=api_permissions, message="获取角色API权限成功")
        except Exception as e:
            return ApiResponse.server_error(f"获取API权限失败: {str(e)}")

    @action(detail=True, methods=['post'])
    def assign_api_permissions(self, request, pk=None):
        """为角色分配API权限"""
        try:
            role = self.get_object()
            api_ids = request.data.get('api_ids', [])
            
            # 去重API IDs
            api_ids = list(set(api_ids))
            
            # 删除现有的API权限规则
            PolicyRule.objects.filter(role_id=str(role.id)).delete()
            
            # 添加新的API权限规则
            for api_id in api_ids:
                try:
                    api = Api.objects.get(id=api_id)
                    PolicyRule.objects.create(
                        role_id=str(role.id),
                        url_pattern=api.path,
                        method=api.method,
                        is_active=True
                    )
                except Api.DoesNotExist:
                    continue
            
            return ApiResponse.success(message="角色API权限分配成功")
        except Exception as e:
            return ApiResponse.server_error(f"分配API权限失败: {str(e)}")


class ApiGroupViewSet(viewsets.ModelViewSet):
    """API分组管理视图集"""
    queryset = ApiGroup.objects.all()
    serializer_class = ApiGroupSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """获取API分组列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(data=serializer.data, message="获取API分组列表成功")


class ApiViewSet(viewsets.ModelViewSet):
    """API管理视图集"""
    queryset = Api.objects.all()
    serializer_class = ApiSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """获取API列表"""
        queryset = self.get_queryset()
        
        # 支持按分组筛选
        group_id = request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        # 支持按方法筛选
        method = request.query_params.get('method')
        if method:
            queryset = queryset.filter(method=method)
        
        # 支持按状态筛选
        status = request.query_params.get('status')
        if status is not None:
            queryset = queryset.filter(status=int(status))
        
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(data=serializer.data, message="获取API列表成功")

    @action(detail=True, methods=['post'])
    def assign_roles(self, request, pk=None):
        """为API分配角色权限"""
        try:
            api = self.get_object()
            role_ids = request.data.get('role_ids', [])
            
            # 删除现有的权限规则
            PolicyRule.objects.filter(
                url_pattern=api.path,
                method=api.method
            ).delete()
            
            # 添加新的权限规则
            for role_id in role_ids:
                PolicyRule.objects.create(
                    role_id=str(role_id),
                    url_pattern=api.path,
                    method=api.method,
                    is_active=True
                )
            
            return ApiResponse.success(message="API角色权限分配成功")
        except Exception as e:
            return ApiResponse.server_error(f"分配权限失败: {str(e)}")

    @action(detail=True, methods=['get'])
    def get_roles(self, request, pk=None):
        """获取API关联的角色"""
        try:
            api = self.get_object()
            roles = api.get_roles_from_casbin()
            return ApiResponse.success(data=roles, message="获取API角色成功")
        except Exception as e:
            return ApiResponse.server_error(f"获取角色失败: {str(e)}")


class ApiLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API日志视图集（只读）"""
    queryset = ApiLog.objects.all()
    serializer_class = ApiLogSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """获取API日志列表"""
        queryset = self.get_queryset()
        
        # 支持按API筛选
        api_id = request.query_params.get('api_id')
        if api_id:
            queryset = queryset.filter(api_id=api_id)
        
        # 支持按用户筛选
        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 支持按状态码筛选
        status_code = request.query_params.get('status_code')
        if status_code:
            queryset = queryset.filter(status_code=int(status_code))
        
        # 支持按时间范围筛选
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(data=serializer.data, message="获取API日志成功")


# 独立的API权限管理视图函数
def get_role_api_permissions(request, role_id):
    """获取角色的API权限 - 独立视图函数"""
    try:
        role = get_object_or_404(Role, id=role_id)
        # 从PolicyRule表获取该角色的API权限
        policies = PolicyRule.objects.filter(
            role_id=str(role.id),
            is_active=True
        )
        
        api_permissions = []
        for policy in policies:
            # 查找对应的API - 尝试多种匹配方式
            api = None
            
            # 1. 精确匹配
            try:
                api = Api.objects.get(path=policy.url_pattern, method=policy.method)
            except Api.DoesNotExist:
                pass
            
            # 2. 如果精确匹配失败，尝试添加/删除末尾斜杠
            if not api:
                # 尝试添加末尾斜杠
                if not policy.url_pattern.endswith('/'):
                    try:
                        api = Api.objects.get(path=policy.url_pattern + '/', method=policy.method)
                    except Api.DoesNotExist:
                        pass
                
                # 尝试删除末尾斜杠
                if not api and policy.url_pattern.endswith('/'):
                    try:
                        api = Api.objects.get(path=policy.url_pattern[:-1], method=policy.method)
                    except Api.DoesNotExist:
                        pass
            
            # 3. 如果仍然没有找到，尝试模糊匹配（处理通配符）
            if not api and '*' in policy.url_pattern:
                # 将通配符转换为正则表达式进行匹配
                pattern = policy.url_pattern.replace('*', '.*')
                try:
                    import re
                    matching_apis = Api.objects.filter(method=policy.method)
                    for candidate_api in matching_apis:
                        if re.match(pattern, candidate_api.path):
                            api = candidate_api
                            break
                except:
                    pass
            
            if api:
                api_permissions.append({
                    'id': api.id,
                    'name': api.name,
                    'path': api.path,
                    'method': api.method,
                    'method_display': api.get_method_display(),
                    'group_name': api.group.name if api.group else '',
                    'description': api.description
                })
            else:
                # 如果API不存在，仍然显示权限规则
                api_permissions.append({
                    'id': f"policy_{policy.id}",
                    'name': f"{policy.method} {policy.url_pattern}",
                    'path': policy.url_pattern,
                    'method': policy.method,
                    'method_display': policy.method,
                    'group_name': '未知分组',
                    'description': 'API已删除或不存在'
                })
        
        return ApiResponse.success(data=api_permissions, message="获取角色API权限成功")
    except Exception as e:
        return ApiResponse.server_error(f"获取API权限失败: {str(e)}")


@csrf_exempt
def assign_role_api_permissions(request, pk):
    """为角色分配API权限 - 独立视图函数"""
    try:
        role = get_object_or_404(Role, id=pk)
        
        # 解析JSON数据
        import json
        body = request.body.decode('utf-8')
        data = json.loads(body) if body else {}
        api_ids = data.get('api_ids', [])
        
        # 去重API IDs
        api_ids = list(set(api_ids))
        
        # 删除现有的API权限规则
        PolicyRule.objects.filter(role_id=str(role.id)).delete()
        
        # 添加新的API权限规则
        for api_id in api_ids:
            try:
                api = Api.objects.get(id=api_id)
                PolicyRule.objects.create(
                    role_id=str(role.id),
                    url_pattern=api.path,
                    method=api.method,
                    is_active=True
                )
            except Api.DoesNotExist:
                continue
        
        return ApiResponse.success(message="角色API权限分配成功")
    except Exception as e:
        return ApiResponse.server_error(f"分配API权限失败: {str(e)}")


def get_role_menu_permissions(request, role_id):
    """获取角色的菜单权限 - 独立视图函数"""
    try:
        role = get_object_or_404(Role, id=role_id)
        
        # 从RoleMenu表获取该角色的菜单权限
        role_menus = RoleMenu.objects.filter(role=role).select_related('menu')
        
        menu_permissions = []
        for role_menu in role_menus:
            menu = role_menu.menu
            menu_permissions.append({
                'id': menu.id,
                'name': menu.name,
                'title': menu.title,
                'path': menu.path,
                'component': menu.component,
                'icon': menu.icon,
                'menu_type': menu.menu_type,
                'menu_type_display': menu.get_menu_type_display(),
                'permission_code': menu.permission_code,
                'parent_id': menu.parent.id if menu.parent else None,
                'sort_order': menu.sort_order,
                'is_hidden': menu.is_hidden,
                'visible': menu.visible,
                'status': menu.status
            })
        
        return ApiResponse.success(data=menu_permissions, message="获取角色菜单权限成功")
    except Exception as e:
        return ApiResponse.server_error(f"获取菜单权限失败: {str(e)}")


@csrf_exempt
def assign_role_menu_permissions(request, pk):
    """为角色分配菜单权限 - 独立视图函数"""
    try:
        role = get_object_or_404(Role, id=pk)
        
        # 解析JSON数据
        import json
        body = request.body.decode('utf-8')
        data = json.loads(body) if body else {}
        menu_ids = data.get('menu_ids', [])
        
        # 去重菜单IDs
        menu_ids = list(set(menu_ids))
        
        # 删除现有的菜单权限
        RoleMenu.objects.filter(role=role).delete()
        
        # 添加新的菜单权限
        for menu_id in menu_ids:
            try:
                menu = Menu.objects.get(id=menu_id)
                RoleMenu.objects.create(role=role, menu=menu)
            except Menu.DoesNotExist:
                continue
        
        return ApiResponse.success(message="角色菜单权限分配成功")
    except Exception as e:
        return ApiResponse.server_error(f"分配菜单权限失败: {str(e)}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jwt_profile_view(request):
    """JWT版本的用户信息获取视图"""
    try:
        user = request.user
        roles = simple_rbac_manager.get_user_roles(user.username)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'avatar': user.avatar.url if user.avatar else None,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'roles': roles
        }
        
        return ApiResponse.success(data=user_data, message="获取用户信息成功")
    except Exception as e:
        return ApiResponse.server_error(f"获取用户信息失败: {str(e)}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_menus_view(request):
    """获取用户菜单权限"""
    try:
        user = request.user
        
        # 获取用户有权限的菜单
        user_menus = []
        
        # 如果是超级用户，返回所有菜单
        if user.is_superuser:
            user_menus = Menu.objects.filter(status=True, visible=True).order_by('sort_order')
        else:
            # 获取用户的所有角色（通过UserRole关系）
            from rbac.models import UserRole
            user_roles = UserRole.objects.filter(user=user).values_list('role', flat=True)
            
            # 获取用户角色关联的菜单
            role_menu_ids = RoleMenu.objects.filter(role__in=user_roles).values_list('menu_id', flat=True)
            user_menus = Menu.objects.filter(
                id__in=role_menu_ids,
                status=True,
                visible=True
            ).order_by('sort_order')
        
        # 序列化菜单数据
        serializer = MenuSerializer(user_menus, many=True)
        
        return ApiResponse.success(data=serializer.data, message="获取用户菜单成功")
    except Exception as e:
        return ApiResponse.server_error(f"获取用户菜单失败: {str(e)}")


