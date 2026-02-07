import importlib
import sys
import os

class ModuleLoader:
    @staticmethod
    def load(module_name):
        full_path = f"modules.{module_name}"
        try:
            if full_path in sys.modules:
                # 核心：如果模块已加载，强制执行reload
                module = importlib.reload(sys.modules[full_path])
            else:
                module = importlib.import_module(full_path)
            return module.get_widget()
        except Exception as e:
            print(f"动态加载模块 {module_name} 失败: {e}")
            return None
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)