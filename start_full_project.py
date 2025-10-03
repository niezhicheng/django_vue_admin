#!/usr/bin/env python3
"""
Django Vue Admin 完整项目启动脚本
同时启动Django后端和Vue前端
"""
import os
import sys
import time
import subprocess
import webbrowser
from threading import Thread
import signal

def run_django_server():
    """在后台运行Django服务器"""
    try:
        print("🚀 启动Django服务器...")
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
        ], check=True)
    except KeyboardInterrupt:
        print("\n✅ Django服务器已停止")
    except Exception as e:
        print(f"❌ Django服务器启动失败: {e}")

def run_vue_dev_server():
    """在后台运行Vue开发服务器"""
    try:
        print("🎨 启动Vue开发服务器...")
        os.chdir('front-end')
        subprocess.run(['npm', 'run', 'dev'], check=True)
    except KeyboardInterrupt:
        print("\n✅ Vue开发服务器已停止")
    except Exception as e:
        print(f"❌ Vue开发服务器启动失败: {e}")
    finally:
        os.chdir('..')

def check_server_ready():
    """检查服务器是否准备就绪"""
    import requests
    for i in range(30):  # 最多等待30秒
        try:
            response = requests.get('http://localhost:8000/rbac/auth/profile/', timeout=2)
            if response.status_code in [200, 401, 403]:  # 任何有效响应都表示服务器已启动
                return True
        except:
            pass
        time.sleep(1)
        print(f"⏳ 等待Django服务器启动... ({i+1}/30)")
    return False

def check_vue_ready():
    """检查Vue服务器是否准备就绪"""
    import requests
    for i in range(30):  # 最多等待30秒
        try:
            response = requests.get('http://localhost:5173/', timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
        print(f"⏳ 等待Vue开发服务器启动... ({i+1}/30)")
    return False

def main():
    """主函数"""
    print("🎯 Django Vue Admin 完整项目启动器")
    print("=" * 60)
    
    # 检查是否在正确的目录
    if not os.path.exists('manage.py'):
        print("❌ 错误: 请在Django项目根目录运行此脚本")
        return
    
    # 检查前端目录
    if not os.path.exists('front-end'):
        print("❌ 错误: 找不到front-end目录")
        return
    
    # 检查依赖
    try:
        import requests
    except ImportError:
        print("⏳ 安装requests依赖...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'])
        import requests
    
    print("📋 开始启动完整项目...")
    
    # 1. 在后台启动Django服务器
    django_thread = Thread(target=run_django_server, daemon=True)
    django_thread.start()
    
    # 2. 等待Django服务器准备就绪
    if not check_server_ready():
        print("❌ Django服务器启动超时，请手动检查")
        return
    
    print("✅ Django服务器已就绪!")
    
    # 3. 在后台启动Vue开发服务器
    vue_thread = Thread(target=run_vue_dev_server, daemon=True)
    vue_thread.start()
    
    # 4. 等待Vue服务器准备就绪
    if not check_vue_ready():
        print("❌ Vue开发服务器启动超时，请手动检查")
        return
    
    print("✅ Vue开发服务器已就绪!")
    
    # 5. 打开浏览器
    print("🌐 打开项目页面...")
    webbrowser.open('http://localhost:5173/')
    
    # 6. 显示信息
    print("\n🎉 完整项目已启动!")
    print("-" * 60)
    print("📖 API文档: API_DOCUMENTATION.md")
    print("🌐 Django后端: http://localhost:8000")
    print("🎨 Vue前端: http://localhost:5173")
    print("🔑 测试账号:")
    print("   • admin / admin123 (超级管理员)")
    print("   • tech_manager / manager123 (技术经理)")
    print("   • backend_dev / dev123 (后端开发)")
    print("-" * 60)
    print("💡 提示:")
    print("   1. 前端页面已在浏览器中打开")
    print("   2. 可以开始测试完整的RBAC功能")
    print("   3. 按 Ctrl+C 停止所有服务器")
    print("=" * 60)
    
    try:
        # 保持脚本运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 项目已停止，感谢使用!")

if __name__ == "__main__":
    main()
