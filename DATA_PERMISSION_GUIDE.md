# 🎯 数据权限系统设计指南

## 📋 系统架构

### 🏗️ 基础架构

```
rbac/
├── models.py                    # 核心权限模型
│   ├── BaseDataPermissionModel  # 数据权限基础模型（抽象类）
│   ├── DataPermissionManager    # 数据权限管理器
│   ├── Department              # 部门模型
│   ├── User                    # 用户模型（扩展）
│   └── Role                    # 角色模型（扩展）
├── base_views.py               # 基础ViewSet和Admin
│   ├── BaseDataPermissionViewSet
│   ├── BaseDataPermissionAdmin
│   └── BaseDataPermissionSerializer
└── simple_rbac.py             # 权限计算核心

business_demo/                  # 业务示例App
├── models.py                   # 示例业务模型
├── views.py                    # 示例业务视图
├── admin.py                    # 示例业务管理
└── urls.py                     # 示例业务路由
```

## 🎯 核心设计理念

### 1. **基础数据权限模型（BaseDataPermissionModel）**

所有需要数据权限控制的业务表都应该继承这个抽象模型：

```python
class BaseDataPermissionModel(models.Model):
    # 权限相关字段
    created_by = models.ForeignKey('User', ...)      # 创建人
    updated_by = models.ForeignKey('User', ...)      # 更新人
    owner_department = models.ForeignKey('Department', ...)  # 所属部门
    
    # 时间字段
    created_at = models.DateTimeField(...)
    updated_at = models.DateTimeField(...)
    
    # 数据权限控制字段
    is_public = models.BooleanField(...)             # 是否公开数据
    data_level = models.IntegerField(...)            # 数据级别（公开/部门/私有/机密）
    
    class Meta:
        abstract = True  # 抽象模型
```

### 2. **混合权限策略**

```
权限优先级：用户自定义权限 > 角色权限 > 默认权限
```

**数据权限级别：**
- `1` - 全部数据：可以查看所有数据
- `2` - 本部门及以下数据：可以查看本部门和子部门数据
- `3` - 本部门数据：只能查看本部门数据
- `4` - 本人数据：只能查看自己创建的数据

### 3. **数据级别分类**

```python
DATA_LEVEL_CHOICES = [
    (1, '公开数据'),    # 所有人可见
    (2, '部门数据'),    # 部门内可见
    (3, '私有数据'),    # 创建者可见
    (4, '机密数据'),    # 需要特殊权限
]
```

## 🚀 使用指南

### 1. **创建业务模型**

```python
# business_demo/models.py
from rbac.models import BaseDataPermissionModel, DataPermissionModelManager

class Article(BaseDataPermissionModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, default='draft')
    
    # 使用数据权限管理器
    objects = DataPermissionModelManager()
    
    class Meta:
        db_table = 'demo_article'
        verbose_name = '文章'
```

**自动获得的功能：**
- ✅ 创建人、更新人自动设置
- ✅ 所属部门自动设置
- ✅ 数据权限自动过滤
- ✅ 审计字段管理

### 2. **创建业务视图**

```python
# business_demo/views.py
from rbac.base_views import BaseDataPermissionViewSet

class ArticleViewSet(BaseDataPermissionViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    # 自动获得的功能：
    # - 根据用户权限过滤数据
    # - 创建时自动设置创建人
    # - 统一的API响应格式
    # - 权限范围信息
```

### 3. **创建管理后台**

```python
# business_demo/admin.py
from rbac.base_views import BaseDataPermissionAdmin

@admin.register(Article)
class ArticleAdmin(BaseDataPermissionAdmin, admin.ModelAdmin):
    list_display = ['title', 'status', 'owner_department', 'created_by']
    
    # 自动获得的功能：
    # - 根据用户权限过滤数据
    # - 自动设置创建人/更新人
    # - 数据权限字段组
    # - 审计字段组
```

## 📊 权限计算逻辑

### 数据过滤流程

```python
def filter_queryset(queryset, user):
    # 1. 获取用户数据权限
    data_scope, department_ids = get_user_data_scope(user)
    
    # 2. 根据权限级别过滤
    if data_scope == 1:  # 全部数据
        return queryset
    
    elif data_scope == 2 or 3:  # 部门数据
        filters = Q()
        filters |= Q(is_public=True)  # 公开数据
        filters |= Q(owner_department_id__in=department_ids)  # 部门数据
        filters |= Q(created_by__department_id__in=department_ids)  # 创建者部门
        return queryset.filter(filters)
    
    elif data_scope == 4:  # 本人数据
        filters = Q()
        filters |= Q(is_public=True)  # 公开数据
        filters |= Q(created_by=user)  # 本人创建
        return queryset.filter(filters)
```

## 🎨 业务场景示例

### 1. **文章管理场景**

```python
# 记者：只能看到自己的文章
user.roles = ['记者']  # data_scope = 4

# 编辑：可以看到本部门的文章
user.roles = ['编辑']  # data_scope = 3

# 主编：可以看到本部门及子部门的文章
user.roles = ['主编']  # data_scope = 2

# 总编：可以看到所有文章
user.roles = ['总编']  # data_scope = 1
```

### 2. **项目管理场景**

```python
# 项目成员：只能看到自己参与的项目
project.assigned_to = user  # 特殊逻辑

# 项目经理：可以看到本部门的项目
user.department = '技术部'  # data_scope = 3

# 总监：可以看到下属部门的项目
user.department = '技术部'  # data_scope = 2（包含子部门）
```

### 3. **文档管理场景**

```python
# 个人文档：只有创建者可见
document.data_level = 3  # 私有数据

# 部门文档：部门内可见
document.data_level = 2  # 部门数据

# 公开文档：所有人可见
document.is_public = True
document.data_level = 1  # 公开数据
```

## 🔧 API 使用示例

### 权限管理API

```bash
# 获取用户权限信息
GET /rbac/api/users/{id}/permission_info/

# 设置用户自定义权限
POST /rbac/api/users/{id}/set_custom_scope/
{
  "data_scope": 2  # 1=全部,2=部门及以下,3=本部门,4=本人,null=清除自定义
}

# 查看用户数据权限范围
GET /rbac/api/users/{id}/data_scope/
```

### 业务API示例

```bash
# 文章管理
GET /business_demo/api/articles/                    # 根据权限自动过滤
POST /business_demo/api/articles/{id}/publish/      # 发布文章
GET /business_demo/api/articles/my_articles/        # 我的文章
GET /business_demo/api/articles/public_articles/    # 公开文章

# 项目管理
GET /business_demo/api/projects/statistics/         # 项目统计（权限过滤）
POST /business_demo/api/projects/{id}/update_progress/  # 更新进度
GET /business_demo/api/projects/department_projects/    # 部门项目

# 任务管理
GET /business_demo/api/tasks/my_tasks/              # 我的任务
POST /business_demo/api/tasks/{id}/assign/          # 分配任务
POST /business_demo/api/tasks/{id}/complete/        # 完成任务
```

## ✨ 核心优势

### 1. **开箱即用**
- 继承基础模型即可获得完整数据权限功能
- 零配置自动权限过滤
- 统一的审计字段管理

### 2. **灵活可扩展**
- 支持用户自定义权限覆盖
- 支持多种数据级别分类
- 支持复杂的业务逻辑扩展

### 3. **安全可靠**
- 多层权限验证
- 自动防止数据泄露
- 完整的审计日志

### 4. **易于理解**
- 清晰的权限层级
- 直观的数据分类
- 完整的示例代码

## 🎯 最佳实践

### 1. **模型设计**
- 所有业务表都继承 `BaseDataPermissionModel`
- 使用 `DataPermissionModelManager` 作为管理器
- 合理设置 `data_level` 默认值

### 2. **视图设计**
- 继承 `BaseDataPermissionViewSet`
- 根据业务需求重写 `get_queryset()`
- 提供业务特定的权限检查

### 3. **权限配置**
- 优先使用角色权限，特殊情况使用用户自定义权限
- 合理设计部门层级结构
- 定期审查和调整权限配置

这个数据权限系统提供了完整的、可扩展的、易于使用的解决方案，既满足了常见的业务需求，又保持了足够的灵活性来应对复杂场景。
