"""
部门相关视图
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Department
from ..serializers import DepartmentSerializer
from ..utils import ApiResponse
from ..models import DataPermissionManager
from ..permissions import CasbinPermission


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理视图集"""
    model = Department
    serializer_class = DepartmentSerializer
    permission_classes = [CasbinPermission]
    
    def get_queryset(self):
        """获取部门查询集"""
        queryset = Department.objects.select_related('parent')
        
        # 应用数据权限过滤
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # 对于Department模型，使用自定义过滤逻辑
            user = self.request.user
            if user.is_superuser:
                return queryset
            else:
                # 根据用户的数据权限范围过滤
                # 优先使用角色的数据权限，如果没有角色则使用用户的数据权限
                data_scope = getattr(user, 'data_scope', 4)
                
                # 获取用户角色的最高数据权限
                from ..models import UserRole
                user_roles = UserRole.objects.filter(user=user).select_related('role')
                if user_roles.exists():
                    # 取角色中最高的数据权限（数字越小权限越高）
                    role_data_scopes = [ur.role.data_scope for ur in user_roles]
                    data_scope = min(role_data_scopes)
                if data_scope == 1:  # 全部数据
                    return queryset
                elif data_scope == 2:  # 本部门及以下数据
                    user_dept = getattr(user, 'department', None)
                    if not user_dept:
                        return queryset.none()
                    dept_ids = [user_dept.id] + [child.id for child in user_dept.get_all_children()]
                    return queryset.filter(id__in=dept_ids)
                elif data_scope == 3:  # 本部门数据
                    user_dept = getattr(user, 'department', None)
                    if not user_dept:
                        return queryset.none()
                    return queryset.filter(id=user_dept.id)
                else:  # 本人数据 - 部门没有创建人概念，返回空
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
