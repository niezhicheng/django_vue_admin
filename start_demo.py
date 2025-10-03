#!/usr/bin/env python3
"""
Django Vue Admin 演示启动脚本
快速启动Django服务器并打开演示页面
"""
import os
import sys
import time
import subprocess
import webbrowser
from threading import Thread

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
        print(f"⏳ 等待服务器启动... ({i+1}/30)")
    return False

def main():
    """主函数"""
    print("🎯 Django Vue Admin 演示启动器")
    print("=" * 50)
    
    # 检查是否在正确的目录
    if not os.path.exists('manage.py'):
        print("❌ 错误: 请在Django项目根目录运行此脚本")
        return
    
    # 检查依赖
    try:
        import requests
    except ImportError:
        print("⏳ 安装requests依赖...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'])
        import requests
    
    print("📋 开始演示流程...")
    
    # 1. 在后台启动Django服务器
    server_thread = Thread(target=run_django_server, daemon=True)
    server_thread.start()
    
    # 2. 等待服务器准备就绪
    if not check_server_ready():
        print("❌ 服务器启动超时，请手动检查")
        return
    
    print("✅ Django服务器已就绪!")
    
    # 3. 打开演示页面
    demo_file = os.path.abspath('frontend_example.html')
    print(f"🌐 打开演示页面: {demo_file}")
    webbrowser.open(f'file://{demo_file}')
    
    # 4. 显示信息
    print("\n🎉 演示环境已准备完成!")
    print("-" * 50)
    print("📖 API文档: API_DOCUMENTATION.md")
    print("🌐 服务器地址: http://localhost:8000")
    print("🖥️  演示页面: 已在浏览器中打开")
    print("🔑 测试账号:")
    print("   • admin / admin123 (超级管理员)")
    print("   • tech_manager / manager123 (技术经理)")
    print("   • backend_dev / dev123 (后端开发)")
    print("-" * 50)
    print("💡 提示:")
    print("   1. 在演示页面中可以测试所有API功能")
    print("   2. 查看API_DOCUMENTATION.md获取完整接口文档")
    print("   3. 按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 保持脚本运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 演示结束，感谢使用!")

if __name__ == "__main__":
    main()
