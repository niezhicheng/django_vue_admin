# 🚀 Django Vue Admin - 企业级权限管理系统

## 📋 项目简介

Django Vue Admin 是一个完整的企业级权限管理系统，提供了**RBAC权限控制**和**数据权限管理**功能。系统采用Django后端 + 前端无关的API设计，可以与Vue、React、Angular等任何前端框架集成。

### ✨ 核心特性

- 🔐 **完整的RBAC权限系统** - 用户、角色、权限、菜单管理
- 🏢 **数据权限控制** - 基于部门和角色的数据权限
- 📋 **动态菜单管理** - 支持目录、菜单、按钮三级权限控制
- 🌐 **前端无关API** - 标准REST API，支持任何前端框架
- 📊 **统一响应格式** - gin-vue-admin风格的JSON响应
- 🛡️ **安全可靠** - Session认证、权限中间件、数据过滤
- 📚 **完整文档** - OpenAPI接口文档和使用指南

### 🎯 数据权限级别

1. **全部数据** - 管理员可见所有数据
2. **本部门及以下数据** - 部门经理可见本部门和子部门数据  
3. **本部门数据** - 部门主管可见本部门数据
4. **本人数据** - 普通员工只能看自己的数据

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Django 4.2+
- SQLite (默认) 或其他数据库

### 2. 安装和运行

```bash
# 1. 克隆或下载项目
cd django_vue_admin

# 2. 安装依赖
pip install -r requirements.txt

# 3. 数据库迁移
python manage.py migrate

# 4. 初始化数据
python manage.py init_simple_rbac --reset

# 5. 启动服务器
python manage.py runserver

# 6. 访问演示页面
open frontend_example.html
```

### 3. 一键演示

```bash
# 运行演示启动脚本（自动启动服务器并打开演示页面）
python start_demo.py
```

### 4. 测试账号

| 用户名 | 密码 | 角色 | 数据权限 |
|--------|------|------|----------|
| `admin` | `admin123` | 超级管理员 | 全部数据 |
| `tech_manager` | `manager123` | 技术经理 | 本部门及以下数据 |
| `frontend_lead` | `lead123` | 前端组长 | 本部门数据 |
| `backend_dev` | `dev123` | 后端开发 | 本人数据 |

---

## 📖 API文档

### 🔑 认证接口

```http
# 登录
POST /rbac/auth/login/
{
  "username": "admin",
  "password": "admin123"
}

# 获取用户信息
GET /rbac/auth/profile/

# 退出登录
POST /rbac/auth/logout/
```

### 👥 用户管理

```http
# 获取用户列表（根据权限自动过滤）
GET /rbac/api/users/

# 创建用户
POST /rbac/api/users/
{
  "username": "new_user",
  "email": "user@example.com",
  "first_name": "新",
  "last_name": "用户",
  "department": 2,
  "position": "开发工程师"
}

# 设置用户数据权限
POST /rbac/api/users/{id}/set_custom_scope/
{
  "data_scope": 2
}
```

### 🏢 部门管理

```http
# 获取部门列表
GET /rbac/api/departments/

# 获取部门树
GET /rbac/api/departments/tree/

# 获取子部门
GET /rbac/api/departments/{id}/children/
```

### 📝 业务示例API

```http
# 获取文章列表（自动数据权限过滤）
GET /business_demo/api/articles/

# 创建文章
POST /business_demo/api/articles/
{
  "title": "文章标题",
  "content": "文章内容",
  "category": "技术",
  "data_level": 2
}

# 获取项目统计
GET /business_demo/api/projects/statistics/
```

### 📊 统一响应格式

```json
{
  "code": 0,
  "message": "操作成功",
  "success": true,
  "data": {...}
}
```

**完整API文档**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 🏗️ 项目结构

```
django_vue_admin/
├── rbac/                      # 核心权限系统
│   ├── models.py             # 权限模型和数据权限基类
│   ├── views.py              # RBAC管理API
│   ├── base_views.py         # 数据权限基础ViewSet
│   ├── simple_rbac.py        # 权限计算核心
│   └── management/commands/  # 管理命令
│
├── business_demo/            # 业务示例
│   ├── models.py             # 示例业务模型
│   ├── views.py              # 示例业务API
│   └── admin.py              # 示例业务管理
│
├── API_DOCUMENTATION.md      # 完整API接口文档
├── frontend_example.html     # 前端对接演示页面
├── start_demo.py            # 一键演示脚本
└── requirements.txt         # Python依赖
```

---

## 🔧 前端集成

### 1. Axios配置示例

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // 携带cookie
})

// 响应拦截器处理统一格式
api.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 0) {
      throw new Error(res.message)
    }
    return res
  }
)
```

### 2. Vue组合式API示例

```vue
<script setup>
import { ref, onMounted } from 'vue'

const articles = ref([])

const fetchArticles = async () => {
  const response = await api.get('/business_demo/api/articles/')
  articles.value = response.data
}

onMounted(fetchArticles)
</script>
```

### 3. 权限控制示例

```javascript
// 根据用户数据权限控制界面
const userScope = userStore.user.permissions.scope

const canEditAllData = computed(() => userScope === 1)
const canEditDeptData = computed(() => userScope <= 2)
const canEditOwnData = computed(() => userScope <= 4)
```

---

## 🎨 业务模型开发

### 1. 继承基础数据权限模型

```python
from rbac.models import BaseDataPermissionModel, DataPermissionModelManager

class Article(BaseDataPermissionModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # 使用数据权限管理器
    objects = DataPermissionModelManager()
```

### 2. 创建数据权限ViewSet

```python
from rbac.base_views import BaseDataPermissionViewSet

class ArticleViewSet(BaseDataPermissionViewSet):
    queryset = Article.objects.all()  # 自动权限过滤
    serializer_class = ArticleSerializer
```

### 3. 自动权限控制

系统会自动根据用户权限过滤数据：
- 创建时自动设置`created_by`和`owner_department`
- 查询时自动过滤可见数据范围
- 更新时自动设置`updated_by`

---

## 🎯 数据权限设计

### 混合权限模式

系统采用**角色权限 + 用户自定义**的混合模式：

1. **角色权限**：用户通过角色获得基础数据权限
2. **用户自定义**：可以为特定用户设置特殊权限
3. **优先级**：`用户自定义 > 角色权限 > 默认权限`

### 部门层级权限

- **总公司** → **技术部** → **前端组/后端组**
- **全部数据**：可见所有部门数据
- **本部门及以下**：可见本部门+子部门数据
- **本部门数据**：只能看本部门数据
- **本人数据**：只能看自己创建的数据

---

## 🔍 演示功能

访问 `frontend_example.html` 可以体验：

1. **用户登录/退出** - 不同角色的权限演示
2. **用户列表** - 根据数据权限自动过滤
3. **部门树** - 层级部门结构展示
4. **文章管理** - 数据权限控制的CRUD操作
5. **项目统计** - 业务数据的统计展示
6. **创建文章** - 数据级别和权限设置

---

## 🛠️ 开发指南

### 添加新的业务模块

1. **创建模型**：继承`BaseDataPermissionModel`
2. **创建ViewSet**：继承`BaseDataPermissionViewSet`
3. **注册路由**：添加到`urls.py`
4. **配置Admin**：继承`BaseBusinessModelAdmin`

### 自定义权限逻辑

```python
# 在视图中自定义权限过滤
def get_queryset(self):
    queryset = super().get_queryset()
    # 添加额外的业务权限逻辑
    if self.action == 'special_action':
        queryset = queryset.filter(special_condition=True)
    return queryset
```

### 扩展数据权限

```python
# 自定义数据权限管理器
class CustomDataPermissionManager(DataPermissionModelManager):
    def for_user(self, user):
        queryset = super().for_user(user)
        # 添加自定义过滤逻辑
        return queryset.filter(custom_field=user.custom_value)
```

---

## 🎁 特色功能

### 1. 🎯 开箱即用
- 继承基础模型即可获得完整数据权限功能
- 无需重复编写权限控制代码

### 2. 🔧 灵活扩展
- 支持用户自定义权限覆盖
- 支持多种数据级别分类
- 支持自定义权限逻辑

### 3. 🛡️ 安全可靠
- 多层权限验证
- 自动数据过滤
- 防止权限泄露

### 4. 📚 完整生态
- 完整的API文档
- 前端集成示例
- 业务开发指南

---

## 📞 技术支持

- **API文档**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **数据权限指南**: [DATA_PERMISSION_GUIDE.md](DATA_PERMISSION_GUIDE.md)
- **演示页面**: [frontend_example.html](frontend_example.html)

## 🏆 适用场景

- 🏢 **企业内部管理系统** - 完整的权限控制和数据安全
- 📊 **数据管理平台** - 基于部门的数据权限管理
- 🎯 **多租户SaaS系统** - 灵活的权限和数据隔离
- 🔐 **权限管理中台** - 为其他系统提供权限服务

---

**🎉 Django Vue Admin - 让权限管理变得简单而强大！**
# django_vue_admin
