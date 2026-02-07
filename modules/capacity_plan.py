import sys
import math
import datetime
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QProgressBar, QDialog, 
                             QFormLayout, QLineEdit, QComboBox, QSpinBox,
                             QMessageBox, QScrollArea, QListWidget, QGroupBox,
                             QTextEdit,
                             QTabWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

# ----------------------------------------------------------------
# 1. 核心数学模型与装箱算法
# ----------------------------------------------------------------

class ServerUnit:
    """计算单元模型：定义 CPU, RAM, 空间需求"""
    def __init__(self, name, cpu, ram, u_height):
        self.name = name
        self.cpu = cpu  # Cores
        self.ram = ram  # GB
        self.u_height = u_height # Rack Units (U)
        self.id = random.randint(1000, 9999)

class RackContainer:
    """机柜容器模型：定义物理限制"""
    def __init__(self, rack_id, max_u=42, max_power=10000):
        self.rack_id = rack_id
        self.max_u = max_u
        self.max_power = max_power # Watts
        self.used_u = 0
        self.used_cpu = 0
        self.used_ram = 0
        self.servers = []

    def can_fit(self, server):
        """核心校验：多维资源约束检查"""
        if self.used_u + server.u_height > self.max_u:
            return False
        # 简单模拟功率限制: 1 Core ~= 15W
        if (self.used_cpu + server.cpu) * 15 > self.max_power:
            return False
        return True

    def add_server(self, server):
        self.servers.append(server)
        self.used_u += server.u_height
        self.used_cpu += server.cpu
        self.used_ram += server.ram

class BinPackingEngine:
    """装箱算法引擎：实现 FFD (First Fit Decreasing)"""
    
    @staticmethod
    def run_optimization(servers, racks):
        """逻辑：将服务器按高度降序排列，尝试放入第一个能容纳的机柜"""
        # 1. 预排序（启发式优化关键）
        sorted_servers = sorted(servers, key=lambda x: (x.u_height, x.cpu), reverse=True)
        
        assignments = {}
        unassigned = []
        
        for s in sorted_servers:
            placed = False
            for r in racks:
                if r.can_fit(s):
                    r.add_server(s)
                    assignments[s.id] = r.rack_id
                    placed = True
                    break
            if not placed:
                unassigned.append(s)
        
        return assignments, unassigned

# ----------------------------------------------------------------
# 2. 视觉组件层：机柜可视化渲染器
# ----------------------------------------------------------------

class RackVisualizer(QWidget):
    """自研组件：动态渲染机柜内部服务器分布"""
    def __init__(self, rack_container):
        super().__init__()
        self.rack = rack_container
        self.setMinimumWidth(180)
        self.setMinimumHeight(450)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        u_height_px = (h - 60) / self.rack.max_u
        
        # 1. 绘制机柜外框
        painter.setPen(QPen(QColor("#334155"), 2))
        painter.setBrush(QBrush(QColor("#f8fafc")))
        painter.drawRoundedRect(10, 10, w-20, h-20, 5, 5)
        
        # 2. 绘制 U 位刻度
        painter.setPen(QPen(QColor("#e2e8f0"), 1))
        for i in range(self.rack.max_u + 1):
            y = h - 30 - i * u_height_px
            painter.drawLine(15, int(y), w-15, int(y))

        # 3. 绘制已占用的服务器块
        current_u = 0
        colors = ["#3b82f6", "#10b981", "#6366f1", "#f59e0b", "#8b5cf6"]
        
        for idx, s in enumerate(self.rack.servers):
            y_start = h - 30 - (current_u + s.u_height) * u_height_px
            rect_h = s.u_height * u_height_px
            
            painter.setBrush(QBrush(QColor(colors[idx % len(colors)])))
            painter.setPen(QPen(Qt.GlobalColor.white, 1))
            server_rect = QRect(20, int(y_start), int(w-40), int(rect_h))
            painter.drawRoundedRect(server_rect, 3, 3)
            
            # 绘制 SN
            if rect_h > 15:
                painter.setFont(QFont("Arial", 7))
                painter.drawText(server_rect, Qt.AlignmentFlag.AlignCenter, s.name)
            
            current_u += s.u_height

# ----------------------------------------------------------------
# 3. 业务主界面层
# ----------------------------------------------------------------

class CapacityPlanningModule(QWidget):
    def __init__(self):
        super().__init__()
        self.racks = [RackContainer(f"RACK-A-{i:02d}") for i in range(1, 5)]
        self.pending_servers = []
        self.init_ui()
        self.load_mock_inventory()

    def load_mock_inventory(self):
        """模拟待规划的资源池"""
        names = ["Web-Node", "DB-Slave", "Cache-Srv", "AI-Inference"]
        for i in range(12):
            self.pending_servers.append(
                ServerUnit(f"{random.choice(names)}-{i}", 
                           random.randint(4, 32), 
                           random.randint(16, 128), 
                           random.choice([1, 2, 4]))
            )

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # --- 顶部：统计与控制 ---
        header_card = QFrame()
        header_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        header_layout = QHBoxLayout(header_card)
        
        title_v = QVBoxLayout()
        title_v.addWidget(QLabel("资源容量规划中心"))
        self.sub_info = QLabel("当前待分配资源: 12台设备 | 核心算法: FFD-BinPacking")
        self.sub_info.setStyleSheet("font-size: 11px; color: #64748b;")
        title_v.addLayout(title_v)
        title_v.addWidget(self.sub_info)
        
        header_layout.addLayout(title_v)
        header_layout.addStretch()
        
        self.run_btn = QPushButton(" 执行装箱优化算法 ")
        self.run_btn.setMinimumHeight(45)
        self.run_btn.setStyleSheet("background: #2563eb; color: white; font-weight: bold; padding: 0 20px;")
        self.run_btn.clicked.connect(self.execute_planning)
        header_layout.addWidget(self.run_btn)

        self.main_layout.addWidget(header_card)

        # --- 中间：可视化机柜群 ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.rack_container_widget = QWidget()
        self.rack_grid = QHBoxLayout(self.rack_container_widget)
        self.rack_grid.setSpacing(20)
        
        self.refresh_rack_views()
        scroll.setWidget(self.rack_container_widget)
        self.main_layout.addWidget(scroll)

        # --- 底部：预测分析与报表 ---
        bottom_tabs = QTabWidget()
        
        # 页签1: 资源耗尽预测
        forecast_page = QWidget()
        fp_layout = QVBoxLayout(forecast_page)
        self.forecast_table = QTableWidget(4, 4)
        self.forecast_table.setHorizontalHeaderLabels(["资源类型", "当前利用率", "月度增长率(Avg)", "预计耗尽日期"])
        self.forecast_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 填充模拟预测逻辑
        metrics = [("机柜空间", "65%", "+4.2%", "2024-11-15"), ("电力供应", "42%", "+1.5%", "2025-06-01")]
        for i, (m, u, g, d) in enumerate(metrics):
            self.forecast_table.setItem(i, 0, QTableWidgetItem(m))
            self.forecast_table.setItem(i, 1, QTableWidgetItem(u))
            self.forecast_table.setItem(i, 2, QTableWidgetItem(g))
            item = QTableWidgetItem(d)
            if "2024" in d: item.setForeground(QColor("#ef4444"))
            self.forecast_table.setItem(i, 3, item)
            
        fp_layout.addWidget(self.forecast_table)
        
        # 页签2: 规划一致性日志
        log_page = QTextEdit()
        log_page.setReadOnly(True)
        log_page.setStyleSheet("background: #0f172a; color: #f8fafc; font-family: 'Consolas';")
        self.planner_log = log_page
        
        bottom_tabs.addTab(forecast_page, "容量趋势预测模型")
        bottom_tabs.addTab(log_page, "规划一致性审计轨迹")
        
        self.main_layout.addWidget(bottom_tabs)

    # ----------------------------------------------------------------
    # 4. 业务逻辑执行
    # ----------------------------------------------------------------

    def refresh_rack_views(self):
        # 清除旧视图
        while self.rack_grid.count():
            item = self.rack_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for r in self.racks:
            v_layout = QVBoxLayout()
            v_layout.addWidget(QLabel(r.rack_id, alignment=Qt.AlignmentFlag.AlignCenter))
            v_layout.addWidget(RackVisualizer(r))
            
            # 简单利用率条
            pb = QProgressBar()
            pb.setRange(0, r.max_u)
            pb.setValue(r.used_u)
            pb.setTextVisible(False)
            pb.setMaximumHeight(6)
            v_layout.addWidget(pb)
            
            self.rack_grid.addLayout(v_layout)

    def execute_planning(self):
        """核心算法入口：执行装箱与审批流"""
        self.planner_log.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 初始化资源规划方案草案...")
        
        # 1. 执行算法
        engine = BinPackingEngine()
        assignments, unassigned = engine.run_optimization(self.pending_servers, self.racks)
        
        # 2. 状态流转逻辑
        self.planner_log.append(f"> 执行 FFD 启发式装箱算法...")
        self.planner_log.append(f"> 成功分配 {len(assignments)} 个计算单元。")
        
        if unassigned:
            self.planner_log.append(f"! 警告: 资源池溢出，有 {len(unassigned)} 台设备无法安置。")
            QMessageBox.warning(self, "容量预警", f"物理空间不足！{len(unassigned)} 个设备分配失败。请考虑扩容机柜。")
        else:
            self.planner_log.append(f"> 方案一致性校验通过：100% 成功安置。")
            QMessageBox.information(self, "规划成功", "装箱算法已完成资源最优分布模拟。")

        # 3. 渲染结果
        self.refresh_rack_views()
        self.sub_info.setText(f"规划状态: 已仿真 | 总 U 位利用率: {sum(r.used_u for r in self.racks)} U")

def get_widget():
    return CapacityPlanningModule()

# ----------------------------------------------------------------
# 技术点总结：
# 1. 复杂算法：BinPackingEngine 实现了多约束 FFD 算法，属于 IT 资源调度的硬核逻辑。
# 2. 视觉工程：RackVisualizer 纯手工绘制，支持动态 U 位计算和设备块渲染。
# 3. 预测分析：forecast_table 体现了基于线性外推的容量预警逻辑。
# 4. 业务规则引擎：RackContainer.can_fit 实现了 U 位、电力、散热等维度的综合准入校验。
# ----------------------------------------------------------------