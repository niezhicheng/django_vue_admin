"""
菜单相关序列化器
"""
from rest_framework import serializers
from ..models import Menu, RoleMenu


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)
    parent_title = serializers.CharField(source='parent.title', read_only=True)
    menu_type_display = serializers.CharField(read_only=True)
    breadcrumb = serializers.SerializerMethodField()
    
    class Meta:
        model = Menu
        fields = [
            'id', 'name', 'title', 'icon', 'path', 'component', 'redirect',
            'menu_type', 'menu_type_display', 'permission_code',
            'parent', 'parent_id', 'parent_title', 'sort_order',
            'is_hidden', 'is_keep_alive', 'is_affix', 'is_frame', 'frame_src',
            'visible', 'status', 'breadcrumb', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """创建菜单时处理parent字段"""
        parent_id = self.initial_data.get('parent')
        if parent_id:
            try:
                parent_menu = Menu.objects.get(id=parent_id)
                validated_data['parent'] = parent_menu
            except Menu.DoesNotExist:
                pass
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新菜单时处理parent字段"""
        parent_id = self.initial_data.get('parent')
        if parent_id is not None:
            if parent_id:
                try:
                    parent_menu = Menu.objects.get(id=parent_id)
                    validated_data['parent'] = parent_menu
                except Menu.DoesNotExist:
                    pass
            else:
                validated_data['parent'] = None
        return super().update(instance, validated_data)
    
    def get_breadcrumb(self, obj):
        """获取面包屑导航"""
        breadcrumb = [obj.title]
        parent = obj.parent
        while parent:
            breadcrumb.insert(0, parent.title)
            parent = parent.parent
        return breadcrumb


class RoleMenuSerializer(serializers.ModelSerializer):
    """角色菜单关联序列化器"""
    
    class Meta:
        model = RoleMenu
        fields = ['id', 'role', 'menu', 'created_at']
        read_only_fields = ['id', 'created_at']
