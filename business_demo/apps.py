"""
业务示例App配置
"""
from django.apps import AppConfig


class BusinessDemoConfig(AppConfig):
    """
    业务示例App配置
    
    这个App展示了如何在实际业务中使用RBAC数据权限系统：
    
    1. 模型设计：
       - 继承 BaseDataPermissionModel
       - 使用 DataPermissionModelManager
       - 自动获得数据权限功能
    
    2. 视图设计：
       - 继承 BaseDataPermissionViewSet
       - 自动权限过滤和审计字段设置
       - 统一的API响应格式
    
    3. 管理后台：
       - 继承 BaseDataPermissionAdmin
       - 自动权限过滤和字段设置
       - 完善的管理界面
    
    4. 业务场景：
       - 文章管理：内容发布、权限控制
       - 项目管理：项目协作、进度跟踪
       - 文档管理：文件共享、下载统计
       - 任务管理：任务分配、状态跟踪
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'business_demo'
    verbose_name = '业务示例'