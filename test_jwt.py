#!/usr/bin/env python3
"""
JWT认证测试脚本
"""
import requests
import json

BASE_URL = 'http://localhost:8000'

def test_jwt_login():
    """测试JWT登录"""
    print("=== 测试JWT登录 ===")
    
    # 测试数据
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        # 发送登录请求
        response = requests.post(
            f'{BASE_URL}/rbac/auth/token/',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"登录成功!")
            print(f"Access Token: {data.get('access', 'N/A')[:50]}...")
            print(f"Refresh Token: {data.get('refresh', 'N/A')[:50]}...")
            print(f"用户信息: {data.get('user', {})}")
            return data.get('access'), data.get('refresh')
        else:
            print(f"登录失败: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None, None

def test_jwt_api(access_token):
    """测试使用JWT token访问API"""
    print("\n=== 测试JWT API访问 ===")
    
    if not access_token:
        print("没有access token，跳过测试")
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 测试获取用户信息
        response = requests.get(
            f'{BASE_URL}/rbac/auth/profile/',
            headers=headers
        )
        
        print(f"获取用户信息 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"用户信息: {data}")
        else:
            print(f"获取用户信息失败: {response.text}")
        
        # 测试获取角色列表
        response = requests.get(
            f'{BASE_URL}/rbac/api/roles/',
            headers=headers
        )
        
        print(f"获取角色列表 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"角色列表: {data}")
        else:
            print(f"获取角色列表失败: {response.text}")
            
    except Exception as e:
        print(f"API请求异常: {e}")

def test_token_refresh(refresh_token):
    """测试token刷新"""
    print("\n=== 测试Token刷新 ===")
    
    if not refresh_token:
        print("没有refresh token，跳过测试")
        return
    
    try:
        response = requests.post(
            f'{BASE_URL}/rbac/auth/token/refresh/',
            json={'refresh': refresh_token},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Token刷新 - 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"新的Access Token: {data.get('access', 'N/A')[:50]}...")
            return data.get('access')
        else:
            print(f"Token刷新失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"Token刷新异常: {e}")
        return None

if __name__ == '__main__':
    print("开始JWT认证测试...")
    
    # 测试登录
    access_token, refresh_token = test_jwt_login()
    
    # 测试API访问
    test_jwt_api(access_token)
    
    # 测试token刷新
    new_access_token = test_token_refresh(refresh_token)
    
    # 使用新token测试API
    if new_access_token:
        print("\n=== 使用新Token测试API ===")
        test_jwt_api(new_access_token)
    
    print("\nJWT认证测试完成!")
