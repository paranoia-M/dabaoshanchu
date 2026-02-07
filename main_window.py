from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt
from core.loader import ModuleLoader

class NavButton(QPushButton):
    def __init__(self, text, is_active=False):
        super().__init__(text)
        self.setFixedHeight(50)
        self.update_style(is_active)

    def update_style(self, is_active):
        if is_active:
            self.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 8px; text-align: left; padding-left: 20px; font-weight: bold; border: none;")
        else:
            self.setStyleSheet("background-color: transparent; color: #94a3b8; border-radius: 8px; text-align: left; padding-left: 20px; border: none;")

class MainWindow(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.setWindowTitle("IT设备统一监管维护平台")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0f172a;")

        # 核心修复：确保这里的 key 与你 modules 目录下的文件名完全一致
        self.menu_map = {
            "资产盘点核心": "asset_inventory",
            "实时性能监控": "performance",
            "故障预测诊断": "fault_diag",
            "维护任务调度": "task_scheduling", # 对应截图中的 task_scheduling.py
            "能耗优化管理": "energy_save",
            "容量规划分析": "capacity_plan",
            "拓扑发现引擎": "topology",
            "合规审计追踪": "compliance",
            "高可用集群状态": "cluster_ha"
        }
        self.buttons = []
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(main_layout)

        # 侧边栏
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #1e293b; border-right: 1px solid #334155;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("")
        logo.setStyleSheet("color: #3b82f6; font-size: 20px; font-weight: bold; margin: 20px; border: none; background: transparent;")
        sidebar_layout.addWidget(logo)

        for name, file_name in self.menu_map.items():
            btn = NavButton(name)
            btn.clicked.connect(lambda checked, n=name, f=file_name, b=btn: self.switch_tab(n, f, b))
            sidebar_layout.addWidget(btn)
            sidebar_layout.addStretch(1)
            self.buttons.append(btn)

        self.container = QStackedWidget()
        self.container.setStyleSheet("background-color: #f8fafc; border-top-left-radius: 20px;")

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.container)
        
        self.switch_tab("资产盘点核心", "asset_inventory", self.buttons[0])

    def switch_tab(self, menu_name, file_name, clicked_btn):
        for btn in self.buttons:
            btn.update_style(btn == clicked_btn)
        
        widget = ModuleLoader.load(file_name)
        if widget:
            widget.setStyleSheet("background-color: #f8fafc; color: #1e293b;")
            if self.container.count() > 0:
                old_w = self.container.currentWidget()
                self.container.removeWidget(old_w)
                old_w.deleteLater()
            
            self.container.addWidget(widget)
            self.container.setCurrentWidget(widget)
            widget.show()