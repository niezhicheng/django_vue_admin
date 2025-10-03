"""
简化的RBAC URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import UserViewSet, RoleViewSet, DepartmentViewSet, MenuViewSet, CustomTokenObtainPairView, ApiGroupViewSet, ApiViewSet, get_role_api_permissions, assign_role_api_permissions, get_role_menu_permissions, assign_role_menu_permissions, jwt_profile_view, user_menus_view

# 创建路由器
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'menus', MenuViewSet, basename='menu')
router.register(r'api-groups', ApiGroupViewSet, basename='api-group')
router.register(r'apis', ApiViewSet, basename='api')
# router.register(r'api-logs', ApiLogViewSet, basename='api-log')  # 暂时注释掉

urlpatterns = [
    # API路由
    path('api/', include(router.urls)),
    
    # 角色API权限管理
    path('api/roles/<int:role_id>/get_api_permissions/', get_role_api_permissions, name='role-get-api-permissions'),
    path('api/roles/<int:role_id>/assign_api_permissions/', assign_role_api_permissions, name='role-assign-api-permissions'),
    
    # 角色菜单权限管理
    path('api/roles/<int:role_id>/get_menu_permissions/', get_role_menu_permissions, name='role-get-menu-permissions'),
    path('api/roles/<int:role_id>/assign_menu_permissions/', assign_role_menu_permissions, name='role-assign-menu-permissions'),
    
    # JWT认证相关
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/profile/', jwt_profile_view, name='jwt_profile'),
    path('auth/user-menus/', user_menus_view, name='user_menus'),
    
    # 认证相关（保持兼容性）
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),  # 重定向到JWT认证
    # path('auth/logout/', AuthView.logout_view, name='logout'),  # 暂时注释掉
    # path('auth/profile/', AuthView.profile_view, name='profile'),  # 暂时注释掉
    
    # 权限检查
    # path('auth/check-permission/', check_permission_view, name='check_permission'),  # 暂时注释掉
]
