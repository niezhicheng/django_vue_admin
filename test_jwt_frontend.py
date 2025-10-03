#!/usr/bin/env python3
"""
测试JWT认证与前端对接
"""
import requests
import json

BASE_URL = 'http://localhost:8000'

def test_jwt_login():
    """测试JWT登录并返回前端期望的格式"""
    print("=== 测试JWT登录（前端格式） ===")
    
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/rbac/auth/token/',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"登录成功!")
            print(f"响应格式: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 检查前端期望的字段
            if 'data' in data and 'access_token' in data['data']:
                print("✅ 包含access_token字段")
            else:
                print("❌ 缺少access_token字段")
                
            if 'data' in data and 'refresh_token' in data['data']:
                print("✅ 包含refresh_token字段")
            else:
                print("❌ 缺少refresh_token字段")
                
            if 'data' in data and 'user' in data['data']:
                print("✅ 包含user字段")
            else:
                print("❌ 缺少user字段")
                
            return data.get('data', {}).get('access_token')
        else:
            print(f"登录失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def test_jwt_api_with_token(access_token):
    """测试使用JWT token访问API"""
    print("\n=== 测试JWT API访问 ===")
    
    if not access_token:
        print("没有access token，跳过测试")
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # 测试获取用户信息
    try:
        response = requests.get(
            f'{BASE_URL}/rbac/auth/profile/',
            headers=headers
        )
        
        print(f"获取用户信息 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 用户信息获取成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
    except Exception as e:
        print(f"❌ API请求异常: {e}")
    
    # 测试获取角色列表
    try:
        response = requests.get(
            f'{BASE_URL}/rbac/api/roles/',
            headers=headers
        )
        
        print(f"获取角色列表 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 角色列表获取成功")
        else:
            print(f"❌ 获取角色列表失败: {response.text}")
    except Exception as e:
        print(f"❌ API请求异常: {e}")

def test_cors():
    """测试CORS配置"""
    print("\n=== 测试CORS配置 ===")
    
    try:
        # 发送OPTIONS预检请求
        response = requests.options(
            f'{BASE_URL}/rbac/auth/token/',
            headers={
                'Origin': 'http://localhost:5175',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        
        print(f"OPTIONS预检请求 - 状态码: {response.status_code}")
        print(f"CORS头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ CORS配置正常")
        else:
            print("❌ CORS配置有问题")
            
    except Exception as e:
        print(f"❌ CORS测试异常: {e}")

if __name__ == '__main__':
    print("开始JWT认证与前端对接测试...")
    
    # 测试CORS
    test_cors()
    
    # 测试登录
    access_token = test_jwt_login()
    
    # 测试API访问
    test_jwt_api_with_token(access_token)
    
    print("\n=== 测试完成 ===")
    print("如果所有测试都通过，前端应该能够正常使用JWT认证登录和访问API。")
