"""
业务示例URL配置 - 展示如何组织业务模块的API路由

这个文件展示了：
1. 如何为业务模块设置独立的URL空间
2. 如何使用DRF Router管理ViewSet路由
3. 如何组织RESTful API结构
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, ProjectViewSet, DocumentViewSet, TaskViewSet

# 创建业务模块的路由器
router = DefaultRouter()

# 注册ViewSet
router.register(r'articles', ArticleViewSet, basename='demo-article')
router.register(r'projects', ProjectViewSet, basename='demo-project')
router.register(r'documents', DocumentViewSet, basename='demo-document')
router.register(r'tasks', TaskViewSet, basename='demo-task')

# URL配置
urlpatterns = [
    # 业务API路由
    path('api/', include(router.urls)),
]

"""
生成的API路由示例：

文章管理：
- GET /business_demo/api/articles/ - 获取文章列表
- POST /business_demo/api/articles/ - 创建文章
- GET /business_demo/api/articles/{id}/ - 获取文章详情
- PUT /business_demo/api/articles/{id}/ - 更新文章
- DELETE /business_demo/api/articles/{id}/ - 删除文章
- POST /business_demo/api/articles/{id}/publish/ - 发布文章
- POST /business_demo/api/articles/{id}/view/ - 查看文章
- GET /business_demo/api/articles/my_articles/ - 我的文章
- GET /business_demo/api/articles/public_articles/ - 公开文章

项目管理：
- GET /business_demo/api/projects/ - 获取项目列表
- POST /business_demo/api/projects/ - 创建项目
- GET /business_demo/api/projects/{id}/ - 获取项目详情
- PUT /business_demo/api/projects/{id}/ - 更新项目
- DELETE /business_demo/api/projects/{id}/ - 删除项目
- POST /business_demo/api/projects/{id}/update_progress/ - 更新进度
- GET /business_demo/api/projects/department_projects/ - 部门项目
- GET /business_demo/api/projects/statistics/ - 项目统计

文档管理：
- GET /business_demo/api/documents/ - 获取文档列表
- POST /business_demo/api/documents/ - 创建文档
- GET /business_demo/api/documents/{id}/ - 获取文档详情
- PUT /business_demo/api/documents/{id}/ - 更新文档
- DELETE /business_demo/api/documents/{id}/ - 删除文档
- POST /business_demo/api/documents/{id}/download/ - 下载文档
- GET /business_demo/api/documents/by_type/?type=pdf - 按类型获取文档

任务管理：
- GET /business_demo/api/tasks/ - 获取任务列表
- POST /business_demo/api/tasks/ - 创建任务
- GET /business_demo/api/tasks/{id}/ - 获取任务详情
- PUT /business_demo/api/tasks/{id}/ - 更新任务
- DELETE /business_demo/api/tasks/{id}/ - 删除任务
- POST /business_demo/api/tasks/{id}/assign/ - 分配任务
- POST /business_demo/api/tasks/{id}/complete/ - 完成任务
- GET /business_demo/api/tasks/my_tasks/ - 我的任务
"""
