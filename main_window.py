from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QColor
from core.loader import ModuleLoader

class NavButton(QPushButton):
    """自定义导航按钮，提升交互感"""
    def __init__(self, text, is_active=False):
        super().__init__(text)
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style(is_active)

    def update_style(self, is_active):
        if is_active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 20px;
                    font-weight: bold;
                    border: none;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #94a3b8;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 20px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #1e293b;
                    color: #f8fafc;
                }
            """)

class MainWindow(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.setWindowTitle("IT设备统一监管维护平台")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0f172a;") # 深色底色

        self.menu_map = {
            "资产盘点核心": "asset_inventory",
            "实时性能监控": "performance",
            "故障预测诊断": "fault_diag",
            "维护任务调度": "scheduling",
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

        # --- 侧边栏 ---
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #1e293b; border-right: 1px solid #334155;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)

        # 1. 顶部Logo区
        logo_label = QLabel("")
        logo_label.setStyleSheet("color: #3b82f6; font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # 2. 菜单项（平均分布逻辑）
        # 在菜单上方加一个微小弹簧
        sidebar_layout.addSpacing(10)
        
        for i, (name, file_name) in enumerate(self.menu_map.items()):
            btn = NavButton(name, is_active=(i==0))
            btn.clicked.connect(lambda checked, n=name, f=file_name, b=btn: self.switch_tab(n, f, b))
            sidebar_layout.addWidget(btn)
            # 在每个按钮之间添加相等的间距，实现“平均分布”
            sidebar_layout.addStretch(1) 
            self.buttons.append(btn)

        # 3. 底部用户信息区
        user_box = QFrame()
        user_box.setStyleSheet("background-color: #0f172a; border-radius: 10px; padding: 10px;")
        user_layout = QVBoxLayout(user_box)
        
        u_name = QLabel(self.user_info['user'])
        u_name.setStyleSheet("color: white; font-weight: bold; border: none;")
        u_role = QLabel(self.user_info['role'])
        u_role.setStyleSheet("color: #64748b; font-size: 11px; border: none;")
        
        user_layout.addWidget(u_name)
        user_layout.addWidget(u_role)
        
        sidebar_layout.addWidget(user_box)

        # --- 右侧内容区 ---
        self.container = QStackedWidget()
        self.container.setStyleSheet("background-color: #f8fafc; border-top-left-radius: 20px;")

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.container)
        
        # 初始化加载第一个界面
        self.switch_tab("资产盘点核心", "asset_inventory", self.buttons[0])

    def switch_tab(self, menu_name, file_name, clicked_btn):
        # 更新按钮样式
        for btn in self.buttons:
            btn.update_style(is_active=(btn == clicked_btn))
        
        # 动态加载模块
        widget = ModuleLoader.load(file_name)
        if widget:
            # 应用统一的右侧内边距样式
            widget.setStyleSheet("background-color: transparent; padding: 20px;")
            if self.container.count() > 0:
                old_widget = self.container.currentWidget()
                self.container.removeWidget(old_widget)
            
            self.container.addWidget(widget)
            self.container.setCurrentWidget(widget)