from django.apps import AppConfig


class DjangoVueAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_vue_admin'
    
    def ready(self):
        """Django应用启动时执行"""
        # 延迟加载权限策略，确保数据库已初始化
        import threading
        import time
        
        def load_policies_delayed():
            time.sleep(2)  # 等待2秒确保数据库初始化完成
            try:
                from rbac.simple_rbac import simple_rbac_manager
                simple_rbac_manager.reload_policies()
                print("权限策略已加载")
            except Exception as e:
                print(f"权限策略加载失败: {e}")
        
        # 在后台线程中加载权限策略
        thread = threading.Thread(target=load_policies_delayed)
        thread.daemon = True
        thread.start()
