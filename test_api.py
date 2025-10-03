#!/usr/bin/env python3
"""
API接口测试脚本
用于验证前后端对接的API接口是否正常工作
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
session = requests.Session()

def test_login():
    """测试登录接口"""
    print("🔐 测试用户登录...")
    
    response = session.post(
        f"{BASE_URL}/rbac/auth/login/",
        json={
            "username": "admin",
            "password": "admin123"
        },
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ 登录成功: {data['message']}")
            print(f"   用户: {data['data']['user']['username']}")
            print(f"   部门: {data['data']['user']['department']['name']}")
            print(f"   权限: {data['data']['permissions']['scope_desc']}")
            return True
        else:
            print(f"❌ 登录失败: {data.get('message')}")
    else:
        print(f"❌ 登录请求失败: {response.status_code}")
    return False

def test_profile():
    """测试获取用户信息"""
    print("\n👤 测试获取用户信息...")
    
    response = session.get(f"{BASE_URL}/rbac/auth/profile/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            user = data['data']
            print(f"✅ 获取用户信息成功")
            print(f"   用户ID: {user['id']}")
            print(f"   用户名: {user['username']}")
            print(f"   邮箱: {user['email']}")
            print(f"   部门: {user['department']['name'] if user['department'] else '无'}")
            print(f"   角色: {', '.join([r['name'] for r in user['roles']])}")
            return True
    
    print(f"❌ 获取用户信息失败")
    return False

def test_users_list():
    """测试获取用户列表"""
    print("\n📋 测试获取用户列表...")
    
    response = session.get(f"{BASE_URL}/rbac/api/users/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            users = data['data']
            print(f"✅ 获取用户列表成功，共 {len(users)} 个用户")
            for user in users[:3]:  # 只显示前3个
                print(f"   - {user['username']} ({user['first_name']} {user['last_name']})")
            return True
    
    print(f"❌ 获取用户列表失败")
    return False

def test_departments():
    """测试获取部门列表"""
    print("\n🏢 测试获取部门列表...")
    
    response = session.get(f"{BASE_URL}/rbac/api/departments/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            departments = data['data']
            print(f"✅ 获取部门列表成功，共 {len(departments)} 个部门")
            for dept in departments[:3]:
                print(f"   - {dept['name']} (编码: {dept['code']})")
            return True
    
    print(f"❌ 获取部门列表失败")
    return False

def test_department_tree():
    """测试获取部门树"""
    print("\n🌳 测试获取部门树...")
    
    response = session.get(f"{BASE_URL}/rbac/api/departments/tree/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            tree = data['data']
            print(f"✅ 获取部门树成功")
            for dept in tree:
                print(f"   - {dept['name']}")
                for child in dept.get('children', []):
                    print(f"     └─ {child['name']}")
                    for grandchild in child.get('children', []):
                        print(f"        └─ {grandchild['name']}")
            return True
    
    print(f"❌ 获取部门树失败")
    return False

def test_articles():
    """测试文章管理接口"""
    print("\n📝 测试文章管理...")
    
    # 获取文章列表
    response = session.get(f"{BASE_URL}/business_demo/api/articles/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            articles = data['data']
            print(f"✅ 获取文章列表成功，共 {len(articles)} 篇文章")
            for article in articles:
                print(f"   - {article['title']} (作者: {article['created_by_info']['name']})")
                print(f"     权限: {article['permission_scope']['data_level']}")
            return True
    
    print(f"❌ 获取文章列表失败")
    return False

def test_create_article():
    """测试创建文章"""
    print("\n📝 测试创建文章...")
    
    article_data = {
        "title": "API测试文章",
        "content": "这是通过API接口创建的测试文章",
        "category": "测试",
        "status": "draft",
        "tags": "API,测试",
        "is_public": True,
        "data_level": 1
    }
    
    response = session.post(
        f"{BASE_URL}/business_demo/api/articles/",
        json=article_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        data = response.json()
        if data.get("success"):
            article = data['data']
            print(f"✅ 创建文章成功: {article['title']}")
            print(f"   ID: {article['id']}")
            print(f"   数据级别: {article['permission_scope']['data_level']}")
            return article['id']
    
    print(f"❌ 创建文章失败")
    return None

def test_article_actions(article_id):
    """测试文章操作"""
    if not article_id:
        return
        
    print(f"\n🎬 测试文章操作 (ID: {article_id})...")
    
    # 测试查看文章
    response = session.post(f"{BASE_URL}/business_demo/api/articles/{article_id}/view/")
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ 查看文章成功，浏览次数: {data['data']['view_count']}")
    
    # 测试发布文章
    response = session.post(f"{BASE_URL}/business_demo/api/articles/{article_id}/publish/")
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ 发布文章成功: {data['message']}")

def test_my_articles():
    """测试获取我的文章"""
    print("\n📚 测试获取我的文章...")
    
    response = session.get(f"{BASE_URL}/business_demo/api/articles/my_articles/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            articles = data['data']
            print(f"✅ 获取我的文章成功，共 {len(articles)} 篇")
            return True
    
    print(f"❌ 获取我的文章失败")
    return False

def test_projects():
    """测试项目管理"""
    print("\n📋 测试项目管理...")
    
    response = session.get(f"{BASE_URL}/business_demo/api/projects/statistics/")
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            stats = data['data']
            print(f"✅ 获取项目统计成功")
            print(f"   总项目数: {stats['total']}")
            print(f"   进行中: {stats['in_progress']}")
            print(f"   已完成: {stats['completed']}")
            return True
    
    print(f"❌ 获取项目统计失败")
    return False

def main():
    """主测试函数"""
    print("🚀 开始API接口测试...\n")
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(2)
    
    # 测试认证
    if not test_login():
        print("❌ 登录失败，停止测试")
        return
    
    # 测试用户相关接口
    test_profile()
    test_users_list()
    
    # 测试部门相关接口
    test_departments()
    test_department_tree()
    
    # 测试业务接口
    test_articles()
    article_id = test_create_article()
    test_article_actions(article_id)
    test_my_articles()
    test_projects()
    
    print("\n✅ API接口测试完成！")
    print("\n📖 查看完整API文档: API_DOCUMENTATION.md")
    print("🌐 服务器地址: http://localhost:8000")
    print("🔑 测试账号: admin / admin123")

if __name__ == "__main__":
    main()
