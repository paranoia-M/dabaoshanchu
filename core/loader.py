import os
import sys
import importlib
import traceback

class ModuleLoader:
    @staticmethod
    def get_resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    @staticmethod
    def load(module_name):
        base_dir = ModuleLoader.get_resource_path("")
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
            
        full_module_path = f"modules.{module_name}"
        try:
            if full_module_path in sys.modules:
                del sys.modules[full_module_path]
            
            module = importlib.import_module(full_module_path)
            # 确保模块里有 get_widget 函数
            if hasattr(module, 'get_widget'):
                return module.get_widget()
            print(f"模块 {module_name} 缺失 get_widget 导出函数")
            return None
        except Exception:
            print(f"加载模块 {module_name} 失败:")
            traceback.print_exc()
            return None