import os
import sys
import importlib

class ModuleLoader:
    @staticmethod
    def get_resource_path(relative_path):
        """处理 PyInstaller 打包后的路径转换"""
        if hasattr(sys, '_MEIPASS'):
            # 打包后的路径
            return os.path.join(sys._MEIPASS, relative_path)
        # 开发环境路径
        return os.path.join(os.path.abspath("."), relative_path)

    @staticmethod
    def load(module_name):
        # 核心修复：确保 sys.path 包含打包后的目录
        base_path = ModuleLoader.get_resource_path("")
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
            
        full_path = f"modules.{module_name}"
        try:
            # 强制刷新导入
            if full_path in sys.modules:
                del sys.modules[full_path]
            
            module = importlib.import_module(full_path)
            return module.get_widget()
        except Exception as e:
            print(f"动态加载模块 {module_name} 失败: {e}")
            import traceback
            traceback.print_exc() # 在控制台打印具体的报错信息
            return None