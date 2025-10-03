"""
业务示例视图 - 展示如何使用数据权限基础ViewSet

这个文件展示了如何在实际业务中使用数据权限基础ViewSet：
1. 继承 BaseDataPermissionViewSet
2. 自动获得数据权限过滤
3. 统一的API响应格式
4. 自动设置创建人、更新人等审计字段
"""
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from rbac.base_views import BaseDataPermissionViewSet, BaseDataPermissionSerializer
from rbac.response import ApiResponse
from .models import Article, Project, Document, Task


# ===== 序列化器 =====

class ArticleSerializer(BaseDataPermissionSerializer, serializers.ModelSerializer):
    """文章序列化器"""
    
    class Meta:
        model = Article
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at', 'view_count']


class ProjectSerializer(BaseDataPermissionSerializer, serializers.ModelSerializer):
    """项目序列化器"""
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']


class DocumentSerializer(BaseDataPermissionSerializer, serializers.ModelSerializer):
    """文档序列化器"""
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at', 'download_count']


class TaskSerializer(BaseDataPermissionSerializer, serializers.ModelSerializer):
    """任务序列化器"""
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']


# ===== ViewSet =====

class ArticleViewSet(BaseDataPermissionViewSet):
    """
    文章管理ViewSet - 展示内容管理的数据权限使用
    
    权限逻辑：
    - 自动根据用户数据权限过滤可见文章
    - 创建时自动设置创建人和所属部门
    - 提供发布、查看统计等业务功能
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布文章"""
        try:
            article = self.get_object()
            article.status = 'published'
            # 发布的文章通常设为公开
            article.is_public = True
            article.save()
            
            return ApiResponse.success(message="文章发布成功")
        except Exception as e:
            return ApiResponse.server_error(f"发布失败: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """查看文章（增加浏览次数）"""
        try:
            article = self.get_object()
            article.view_count += 1
            article.save()
            
            serializer = self.get_serializer(article)
            return ApiResponse.success(
                data=serializer.data,
                message="文章详情"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取失败: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def my_articles(self, request):
        """获取我的文章"""
        try:
            # 只获取当前用户创建的文章
            articles = Article.objects.filter(created_by=request.user)
            serializer = self.get_serializer(articles, many=True)
            
            return ApiResponse.success(
                data=serializer.data,
                message="获取我的文章成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取失败: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def public_articles(self, request):
        """获取公开文章"""
        try:
            # 获取公开文章
            articles = Article.objects.public_data().filter(status='published')
            serializer = self.get_serializer(articles, many=True)
            
            return ApiResponse.success(
                data=serializer.data,
                message="获取公开文章成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取失败: {str(e)}")


class ProjectViewSet(BaseDataPermissionViewSet):
    """
    项目管理ViewSet - 展示项目管理的数据权限使用
    
    权限逻辑：
    - 根据用户部门权限过滤可见项目
    - 项目状态变更权限控制
    - 进度更新等业务功能
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """更新项目进度"""
        try:
            project = self.get_object()
            progress = request.data.get('progress', 0)
            
            if not 0 <= progress <= 100:
                return ApiResponse.validation_error("进度必须在0-100之间")
            
            project.progress = progress
            if progress == 100:
                project.status = 'completed'
            elif progress > 0:
                project.status = 'in_progress'
            
            project.save()
            
            return ApiResponse.success(
                data={'progress': project.progress, 'status': project.status},
                message="项目进度更新成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"更新失败: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def department_projects(self, request):
        """获取部门项目"""
        try:
            if not request.user.department:
                return ApiResponse.validation_error("用户未分配部门")
            
            # 获取本部门的项目
            projects = Project.objects.department_data(request.user.department)
            serializer = self.get_serializer(projects, many=True)
            
            return ApiResponse.success(
                data=serializer.data,
                message="获取部门项目成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取失败: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """项目统计"""
        try:
            # 根据用户权限获取可见项目
            queryset = self.get_queryset()
            
            stats = {
                'total': queryset.count(),
                'planning': queryset.filter(status='planning').count(),
                'in_progress': queryset.filter(status='in_progress').count(),
                'completed': queryset.filter(status='completed').count(),
                'high_priority': queryset.filter(priority__gte=3).count(),
            }
            
            return ApiResponse.success(
                data=stats,
                message="获取项目统计成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取统计失败: {str(e)}")


class DocumentViewSet(BaseDataPermissionViewSet):
    """
    文档管理ViewSet - 展示文档管理的数据权限使用
    
    权限逻辑：
    - 根据文档数据级别和用户权限过滤
    - 下载权限控制
    - 版本管理等功能
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """下载文档"""
        try:
            document = self.get_object()
            # 增加下载次数
            document.download_count += 1
            document.save()
            
            return ApiResponse.success(
                data={
                    'download_url': document.file_path,
                    'file_name': document.title,
                    'file_size': document.file_size,
                    'file_type': document.file_type
                },
                message="获取下载链接成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"下载失败: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """按文件类型获取文档"""
        try:
            file_type = request.query_params.get('type')
            if not file_type:
                return ApiResponse.validation_error("请指定文件类型")
            
            documents = self.get_queryset().filter(file_type=file_type)
            serializer = self.get_serializer(documents, many=True)
            
            return ApiResponse.success(
                data=serializer.data,
                message=f"获取{file_type}类型文档成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取失败: {str(e)}")


class TaskViewSet(BaseDataPermissionViewSet):
    """
    任务管理ViewSet - 展示任务管理的数据权限使用
    
    权限逻辑：
    - 任务创建者和指派人员可见
    - 上级可以查看下属任务
    - 任务状态流转控制
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        """重写查询集，添加任务特殊的权限逻辑"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # 除了基础数据权限外，还可以查看指派给自己的任务
        from django.db.models import Q
        additional_filter = Q(assigned_to=user)
        
        # 合并权限过滤
        return queryset.filter(additional_filter) | queryset
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """分配任务"""
        try:
            task = self.get_object()
            assigned_to_id = request.data.get('assigned_to')
            
            if not assigned_to_id:
                return ApiResponse.validation_error("请指定任务指派人")
            
            from rbac.models import User
            assigned_user = User.objects.get(id=assigned_to_id)
            task.assigned_to = assigned_user
            task.status = 'todo'
            task.save()
            
            return ApiResponse.success(
                data={
                    'assigned_to': assigned_user.username,
                    'status': task.status
                },
                message="任务分配成功"
            )
        except User.DoesNotExist:
            return ApiResponse.not_found("指派用户不存在")
        except Exception as e:
            return ApiResponse.server_error(f"分配失败: {str(e)}")
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成任务"""
        try:
            task = self.get_object()
            actual_hours = request.data.get('actual_hours')
            
            task.status = 'completed'
            if actual_hours:
                task.actual_hours = actual_hours
            task.save()
            
            return ApiResponse.success(message="任务完成")
        except Exception as e:
            return ApiResponse.server_error(f"操作失败: {str(e)}")
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """获取我的任务（创建的+指派给我的）"""
        try:
            from django.db.models import Q
            
            # 我创建的任务 + 指派给我的任务
            tasks = Task.objects.filter(
                Q(created_by=request.user) | Q(assigned_to=request.user)
            ).distinct()
            
            serializer = self.get_serializer(tasks, many=True)
            
            return ApiResponse.success(
                data=serializer.data,
                message="获取我的任务成功"
            )
        except Exception as e:
            return ApiResponse.server_error(f"获取失败: {str(e)}")