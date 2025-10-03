# 🚀 Django Vue Admin API 接口文档

## 📋 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Content-Type**: `application/json`
- **Authentication**: Session-based (Cookie)

## 🔐 认证方式

系统使用Session认证，前端需要：
1. 调用登录接口获取Session
2. 后续请求自动携带Cookie
3. 处理CSRF Token（如果启用）

---

## 🎯 核心API接口

### 1. 🔑 认证管理

#### 1.1 用户登录
```http
POST /rbac/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "登录成功",
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "系统",
      "last_name": "管理员",
      "department": {
        "id": 1,
        "name": "总公司",
        "code": "HQ"
      },
      "position": "系统管理员",
      "is_active": true,
      "is_staff": true
    },
    "permissions": {
      "scope": 1,
      "scope_desc": "全部数据",
      "source": "超级用户"
    }
  }
}
```

#### 1.2 用户退出
```http
POST /rbac/auth/logout/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "退出成功",
  "success": true,
  "data": null
}
```

#### 1.3 获取用户信息
```http
GET /rbac/auth/profile/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取用户信息成功",
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "系统",
    "last_name": "管理员",
    "phone": "",
    "avatar": "",
    "department": {
      "id": 1,
      "name": "总公司",
      "code": "HQ"
    },
    "position": "系统管理员",
    "roles": [
      {
        "id": 1,
        "role_id": "1",
        "name": "超级管理员",
        "data_scope": 1
      }
    ],
    "permissions": {
      "scope": 1,
      "scope_desc": "全部数据",
      "source": "超级用户"
    }
  }
}
```

### 2. 👥 用户管理

#### 2.1 获取用户列表
```http
GET /rbac/api/users/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取用户列表成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "系统",
      "last_name": "管理员",
      "phone": "",
      "avatar": "",
      "position": "系统管理员",
      "department": {
        "id": 1,
        "name": "总公司",
        "code": "HQ"
      },
      "roles": [
        {
          "id": 1,
          "role_id": "1",
          "name": "超级管理员",
          "data_scope": 1
        }
      ],
      "data_scope": 1,
      "is_active": true,
      "is_staff": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 2.2 创建用户
```http
POST /rbac/api/users/
Content-Type: application/json

{
  "username": "new_user",
  "email": "user@example.com",
  "first_name": "新",
  "last_name": "用户",
  "password": "password123",
  "phone": "13800138000",
  "department": 2,
  "position": "开发工程师"
}
```

#### 2.3 更新用户
```http
PUT /rbac/api/users/{id}/
Content-Type: application/json

{
  "first_name": "更新的",
  "last_name": "姓名",
  "phone": "13900139000",
  "position": "高级开发工程师"
}
```

#### 2.4 设置用户自定义数据权限
```http
POST /rbac/api/users/{id}/set_custom_scope/
Content-Type: application/json

{
  "data_scope": 2
}
```

**data_scope 说明：**
- `1`: 全部数据
- `2`: 本部门及以下数据
- `3`: 本部门数据
- `4`: 本人数据
- `null`: 清除自定义权限

#### 2.5 获取用户权限信息
```http
GET /rbac/api/users/{id}/permission_info/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取用户权限信息成功",
  "success": true,
  "data": {
    "user_id": 1,
    "username": "admin",
    "department": {
      "id": 1,
      "name": "总公司",
      "code": "HQ"
    },
    "custom_data_scope": null,
    "roles": [
      {
        "id": 1,
        "role_id": "1",
        "name": "超级管理员",
        "data_scope": 1,
        "data_scope_desc": "全部数据"
      }
    ],
    "effective_permission": {
      "scope": 1,
      "scope_desc": "全部数据",
      "source": "超级用户",
      "department_ids": [],
      "department_count": 0
    }
  }
}
```

### 3. 🎭 角色管理

#### 3.1 获取角色列表
```http
GET /rbac/api/roles/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取角色列表成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "role_id": "1",
      "name": "超级管理员",
      "code": "admin",
      "description": "系统最高权限",
      "data_scope": 1,
      "data_scope_display": "全部数据",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "menus": [
        {
          "id": 1,
          "title": "系统管理",
          "path": "/system",
          "menu_type": 1
        }
      ],
      "menu_count": 10
    }
  ]
}
```

#### 3.2 创建角色
```http
POST /rbac/api/roles/
Content-Type: application/json

{
  "role_id": "5",
  "name": "项目经理",
  "code": "project_manager",
  "description": "项目管理权限",
  "data_scope": 2
}
```

#### 3.3 为角色分配菜单
```http
POST /rbac/api/roles/{id}/assign_menus/
Content-Type: application/json

{
  "menu_ids": [1, 2, 3, 5]
}
```

**响应示例：**
```json
{
  "code": 0,
  "message": "角色菜单分配成功，共分配 4 个菜单",
  "success": true,
  "data": {
    "role_id": 1,
    "menu_count": 4
  }
}
```

#### 3.4 获取角色菜单
```http
GET /rbac/api/roles/{id}/get_menus/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取角色菜单成功",
  "success": true,
  "data": {
    "role_id": 1,
    "role_name": "超级管理员",
    "menus": [
      {
        "id": 1,
        "name": "system",
        "title": "系统管理",
        "icon": "Setting",
        "path": "/system",
        "component": "Layout",
        "menu_type": 1,
        "menu_type_display": "目录",
        "permission_code": "system",
        "parent_id": null,
        "sort_order": 1,
        "status": true
      }
    ],
    "menu_count": 10
  }
}
```

#### 3.5 为角色分配权限
```http
POST /rbac/api/roles/{id}/assign_permissions/
Content-Type: application/json

{
  "permissions": [
    {
      "url_pattern": "/rbac/api/projects",
      "method": "GET"
    },
    {
      "url_pattern": "/rbac/api/projects/*",
      "method": "POST"
    }
  ]
}
```

#### 3.6 获取角色权限
```http
GET /rbac/api/roles/{id}/get_permissions/
```

### 4. 📋 菜单管理

#### 4.1 获取菜单列表
```http
GET /rbac/api/menus/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取菜单列表成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "system",
      "title": "系统管理",
      "icon": "Setting",
      "path": "/system",
      "component": "Layout",
      "redirect": "/system/user",
      "menu_type": 1,
      "menu_type_display": "目录",
      "permission_code": "system",
      "parent_id": null,
      "parent_title": null,
      "sort_order": 1,
      "is_hidden": false,
      "is_keep_alive": true,
      "is_affix": false,
      "is_frame": false,
      "frame_src": null,
      "visible": true,
      "status": true,
      "created_at": "2024-01-01T00:00:00Z",
      "breadcrumb": ["系统管理"]
    }
  ]
}
```

#### 4.2 获取菜单树
```http
GET /rbac/api/menus/tree/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取菜单树成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "system",
      "title": "系统管理",
      "icon": "Setting",
      "path": "/system",
      "component": "Layout",
      "redirect": "/system/user",
      "menu_type": 1,
      "permission_code": "system",
      "sort_order": 1,
      "is_hidden": false,
      "is_keep_alive": true,
      "is_affix": false,
      "is_frame": false,
      "frame_src": null,
      "visible": true,
      "status": true,
      "children": [
        {
          "id": 2,
          "name": "user",
          "title": "用户管理",
          "icon": "User",
          "path": "/system/user",
          "component": "system/user/index",
          "menu_type": 2,
          "permission_code": "system:user:list",
          "sort_order": 1,
          "children": []
        }
      ]
    }
  ]
}
```

#### 4.3 获取路由菜单（前端专用）
```http
GET /rbac/api/menus/routes/
```

**说明：** 这个接口返回当前用户有权限访问的菜单，格式适合前端路由使用。

**响应示例：**
```json
{
  "code": 0,
  "message": "获取路由菜单成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "system",
      "path": "/system",
      "component": "Layout",
      "redirect": "/system/user",
      "meta": {
        "title": "系统管理",
        "icon": "Setting",
        "hidden": false,
        "keepAlive": true,
        "affix": false,
        "frameSrc": null,
        "permission": "system"
      },
      "children": [
        {
          "id": 2,
          "name": "user",
          "path": "/system/user",
          "component": "system/user/index",
          "meta": {
            "title": "用户管理",
            "icon": "User",
            "hidden": false,
            "keepAlive": true,
            "affix": false,
            "frameSrc": null,
            "permission": "system:user:list"
          }
        }
      ]
    }
  ]
}
```

#### 4.4 创建菜单
```http
POST /rbac/api/menus/
Content-Type: application/json

{
  "name": "custom_menu",
  "title": "自定义菜单",
  "icon": "Custom",
  "path": "/custom",
  "component": "custom/index",
  "menu_type": 2,
  "permission_code": "custom:menu",
  "parent": 1,
  "sort_order": 10,
  "visible": true,
  "status": true
}
```

#### 4.5 更新菜单
```http
PUT /rbac/api/menus/{id}/
Content-Type: application/json

{
  "title": "更新的菜单标题",
  "icon": "NewIcon",
  "sort_order": 5
}
```

#### 4.6 删除菜单
```http
DELETE /rbac/api/menus/{id}/
```

#### 4.7 获取子菜单
```http
GET /rbac/api/menus/{id}/children/
```

### 5. 🏢 部门管理

#### 5.1 获取部门列表
```http
GET /rbac/api/departments/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取部门列表成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "总公司",
      "code": "HQ",
      "parent_id": null,
      "parent_name": null,
      "level": 1,
      "sort_order": 1,
      "leader": "",
      "phone": "",
      "email": "",
      "status": true,
      "created_at": "2024-01-01T00:00:00Z",
      "path": "总公司"
    }
  ]
}
```

#### 5.2 获取部门树
```http
GET /rbac/api/departments/tree/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取部门树成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "总公司",
      "code": "HQ",
      "level": 1,
      "sort_order": 1,
      "leader": "",
      "status": true,
      "children": [
        {
          "id": 2,
          "name": "技术部",
          "code": "TECH",
          "level": 2,
          "sort_order": 1,
          "leader": "技术总监",
          "status": true,
          "children": [
            {
              "id": 3,
              "name": "前端组",
              "code": "FRONTEND",
              "level": 3,
              "sort_order": 1,
              "leader": "前端组长",
              "status": true,
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

#### 5.3 获取子部门
```http
GET /rbac/api/departments/{id}/children/
```

---

## 🏢 业务示例API

### 1. 📝 文章管理

#### 1.1 获取文章列表
```http
GET /business_demo/api/articles/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取数据成功",
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "管理员文章",
      "content": "这是管理员写的文章",
      "category": "管理",
      "status": "draft",
      "view_count": 0,
      "tags": "",
      "is_public": true,
      "data_level": 2,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "permission_scope": {
        "created_by": "admin",
        "owner_department": "总公司",
        "is_public": true,
        "data_level": "部门数据"
      },
      "created_by_info": {
        "id": 1,
        "username": "admin",
        "name": "系统 管理员"
      },
      "owner_department_info": {
        "id": 1,
        "name": "总公司",
        "code": "HQ"
      }
    }
  ]
}
```

#### 1.2 创建文章
```http
POST /business_demo/api/articles/
Content-Type: application/json

{
  "title": "新文章标题",
  "content": "文章内容",
  "category": "技术",
  "status": "draft",
  "tags": "Django,Vue",
  "is_public": false,
  "data_level": 2
}
```

#### 1.3 发布文章
```http
POST /business_demo/api/articles/{id}/publish/
```

#### 1.4 查看文章（增加浏览次数）
```http
POST /business_demo/api/articles/{id}/view/
```

#### 1.5 获取我的文章
```http
GET /business_demo/api/articles/my_articles/
```

#### 1.6 获取公开文章
```http
GET /business_demo/api/articles/public_articles/
```

### 2. 📋 项目管理

#### 2.1 获取项目列表
```http
GET /business_demo/api/projects/
```

#### 2.2 创建项目
```http
POST /business_demo/api/projects/
Content-Type: application/json

{
  "name": "新项目",
  "description": "项目描述",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "budget": "100000.00",
  "status": "planning",
  "priority": 2,
  "progress": 0,
  "is_public": false,
  "data_level": 2
}
```

#### 2.3 更新项目进度
```http
POST /business_demo/api/projects/{id}/update_progress/
Content-Type: application/json

{
  "progress": 50
}
```

#### 2.4 获取部门项目
```http
GET /business_demo/api/projects/department_projects/
```

#### 2.5 获取项目统计
```http
GET /business_demo/api/projects/statistics/
```

**响应示例：**
```json
{
  "code": 0,
  "message": "获取项目统计成功",
  "success": true,
  "data": {
    "total": 10,
    "planning": 3,
    "in_progress": 5,
    "completed": 2,
    "high_priority": 4
  }
}
```

### 3. 📄 文档管理

#### 3.1 获取文档列表
```http
GET /business_demo/api/documents/
```

#### 3.2 下载文档
```http
POST /business_demo/api/documents/{id}/download/
```

#### 3.3 按类型获取文档
```http
GET /business_demo/api/documents/by_type/?type=pdf
```

### 4. ✅ 任务管理

#### 4.1 获取任务列表
```http
GET /business_demo/api/tasks/
```

#### 4.2 创建任务
```http
POST /business_demo/api/tasks/
Content-Type: application/json

{
  "title": "新任务",
  "description": "任务描述",
  "assigned_to": 2,
  "due_date": "2024-01-15T18:00:00Z",
  "status": "todo",
  "priority": 2,
  "estimated_hours": "8.00"
}
```

#### 4.3 分配任务
```http
POST /business_demo/api/tasks/{id}/assign/
Content-Type: application/json

{
  "assigned_to": 3
}
```

#### 4.4 完成任务
```http
POST /business_demo/api/tasks/{id}/complete/
Content-Type: application/json

{
  "actual_hours": "6.50"
}
```

#### 4.5 获取我的任务
```http
GET /business_demo/api/tasks/my_tasks/
```

---

## 📊 统一响应格式

### 成功响应
```json
{
  "code": 0,
  "message": "操作成功",
  "success": true,
  "data": {...}
}
```

### 错误响应
```json
{
  "code": 1,
  "message": "错误信息",
  "success": false,
  "data": null
}
```

### 状态码说明
- `0`: 成功
- `1`: 一般错误
- `401`: 未登录或token过期
- `403`: 权限不足
- `404`: 资源不存在
- `405`: 请求方法不允许
- `422`: 参数验证失败
- `500`: 服务器内部错误

---

## 🔧 前端集成指南

### 1. Axios 配置示例

```javascript
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  withCredentials: true, // 携带cookie
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加token或其他headers
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    const res = response.data
    
    // 统一处理业务错误
    if (res.code !== 0) {
      // 处理错误
      if (res.code === 401) {
        // 跳转到登录页
        window.location.href = '/login'
      }
      return Promise.reject(new Error(res.message || 'Error'))
    }
    
    return res
  },
  error => {
    // 处理HTTP错误
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
```

### 2. Vue 3 组合式API示例

```vue
<template>
  <div>
    <h1>文章列表</h1>
    <div v-for="article in articles" :key="article.id">
      <h3>{{ article.title }}</h3>
      <p>作者: {{ article.created_by_info.name }}</p>
      <p>部门: {{ article.owner_department_info.name }}</p>
      <span :class="getDataLevelClass(article.data_level)">
        {{ article.permission_scope.data_level }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

const articles = ref([])

const fetchArticles = async () => {
  try {
    const response = await api.get('/business_demo/api/articles/')
    articles.value = response.data
  } catch (error) {
    console.error('获取文章失败:', error)
  }
}

const getDataLevelClass = (level) => {
  const classes = {
    1: 'public',
    2: 'department', 
    3: 'private',
    4: 'confidential'
  }
  return classes[level] || 'default'
}

onMounted(() => {
  fetchArticles()
})
</script>
```

### 3. 权限控制示例

```javascript
// 权限检查工具
export const usePermissions = () => {
  const userStore = useUserStore()
  
  const hasPermission = (permission) => {
    const user = userStore.user
    if (!user) return false
    
    // 超级用户拥有所有权限
    if (user.is_superuser) return true
    
    // 检查数据权限范围
    const dataScope = user.permissions.scope
    return dataScope <= permission.requiredScope
  }
  
  const canViewData = (dataScope) => {
    const user = userStore.user
    if (!user) return false
    
    return user.permissions.scope <= dataScope
  }
  
  return {
    hasPermission,
    canViewData
  }
}

// 在组件中使用
const { hasPermission, canViewData } = usePermissions()

const canEditArticle = computed(() => {
  return hasPermission({ requiredScope: 2 })
})
```

### 4. 数据权限说明

前端需要理解的数据权限级别：
- **scope = 1**: 可以看到所有数据
- **scope = 2**: 可以看到本部门及子部门数据
- **scope = 3**: 可以看到本部门数据
- **scope = 4**: 只能看到自己的数据

前端可以根据用户的`permissions.scope`来：
1. 控制界面元素的显示/隐藏
2. 决定是否显示某些操作按钮
3. 过滤数据列表的显示

---

## 🚀 快速开始

1. **启动后端服务**
```bash
cd django_vue_admin
python manage.py runserver
```

2. **使用测试账号登录**
- 管理员: `admin / admin123`
- 技术经理: `tech_manager / manager123`
- 前端组长: `frontend_lead / lead123`
- 后端开发: `backend_dev / dev123`

3. **测试API接口**
```bash
# 登录
curl -X POST http://localhost:8000/rbac/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 获取用户信息
curl -X GET http://localhost:8000/rbac/auth/profile/ \
  -b cookies.txt

# 获取文章列表
curl -X GET http://localhost:8000/business_demo/api/articles/ \
  -b cookies.txt
```

这个API文档提供了完整的接口说明，前端可以直接按照这个文档进行开发对接！🎉
