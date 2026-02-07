import sys
import datetime
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QProgressBar, QDialog, 
                             QFormLayout, QLineEdit, QComboBox, QDateTimeEdit, 
                             QMessageBox, QScrollArea, QListWidget, QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

# ----------------------------------------------------------------
# 1. 核心业务算法逻辑
# ----------------------------------------------------------------

class SkillLevel:
    JUNIOR = 1
    SENIOR = 2
    EXPERT = 3

class MaintenanceTask:
    def __init__(self, task_id, title, skill_req, priority, duration_h):
        self.task_id = task_id
        self.title = title
        self.skill_req = skill_req
        self.priority = priority 
        self.duration_h = duration_h
        self.status = "待排程"
        self.assigned_engineer = None
        self.start_time = None

class Engineer:
    def __init__(self, name, skill_level, department):
        self.name = name
        self.skill_level = skill_level
        self.department = department
        self.current_load = 0 
        self.schedule = [] 

class SchedulingEngine:
    """资源优化调度算法引擎"""
    @staticmethod
    def calculate_match_score(task, engineer):
        if engineer.skill_level < task.skill_req:
            return -1
        load_score = (100 - engineer.current_load) * 0.4
        skill_gap = engineer.skill_level - task.skill_req
        skill_score = (10 - skill_gap) * 0.3
        priority_score = task.priority * 2.0
        return load_score + skill_score + priority_score

# ----------------------------------------------------------------
# 2. 自定义视觉甘特图组件
# ----------------------------------------------------------------

class GanttChartView(QFrame):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.setMinimumHeight(260)
        self.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        self.hour_width = 70 
        
    def set_data(self, tasks):
        self.tasks = [t for t in tasks if t.start_time]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        margin_left = 130
        margin_top = 40
        
        # 绘制背景网格
        painter.setPen(QPen(QColor("#f1f5f9"), 1))
        for i in range(12):
            x = margin_left + i * self.hour_width
            painter.drawLine(x, margin_top, x, h - 20)
            painter.drawText(x - 15, margin_top - 10, f"{8+i}:00")

        # 绘制任务条
        for i, task in enumerate(self.tasks):
            y = margin_top + 20 + i * 45
            start_hour = task.start_time.hour + task.start_time.minute / 60.0
            x = margin_left + (start_hour - 8) * self.hour_width
            rect_w = task.duration_h * self.hour_width
            
            color = QColor("#3b82f6") if task.priority < 7 else QColor("#ef4444")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), y, int(rect_w), 28, 5, 5)
            
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(QRect(int(x), y, int(rect_w), 28), Qt.AlignmentFlag.AlignCenter, task.title)
            
            painter.setPen(QPen(QColor("#475569")))
            painter.drawText(15, y + 18, f"{task.assigned_engineer}")

# ----------------------------------------------------------------
# 3. 主界面模块
# ----------------------------------------------------------------

class TaskSchedulingModule(QWidget):
    def __init__(self):
        super().__init__()
        self.engineers = [
            Engineer("张工", SkillLevel.EXPERT, "计算资源组"),
            Engineer("李工", SkillLevel.SENIOR, "网络运维组"),
            Engineer("王工", SkillLevel.JUNIOR, "基础环境组"),
            Engineer("赵工", SkillLevel.SENIOR, "存储架构组")
        ]
        self.tasks = []
        self.init_mock_tasks()
        self.init_ui()

    def init_mock_tasks(self):
        titles = ["核心交换机升级", "冷机系统例行维保", "存储LUN扩容", "防火墙巡检"]
        for i, title in enumerate(titles):
            self.tasks.append(MaintenanceTask(f"T-{100+i}", title, random.randint(1,3), random.randint(3,9), 2))

    def init_ui(self):
        # 关键修复：不要在初始化布局时传入 self，然后在最后又调用 setLayout
        # 统一使用 self.main_layout = QVBoxLayout(self)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 1. 资源卡片区
        res_header = QLabel("IT维护工程师资源池 (实时负载调度)")
        res_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        self.main_layout.addWidget(res_header)

        self.res_layout = QHBoxLayout()
        self.update_engineer_cards()
        self.main_layout.addLayout(self.res_layout)

        # 2. 甘特图区
        gantt_group = QGroupBox("维护计划排程甘特图 (8:00 - 20:00)")
        gantt_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 10px; padding-top: 15px; }")
        gantt_main_layout = QVBoxLayout(gantt_group)
        self.gantt_view = GanttChartView()
        gantt_main_layout.addWidget(self.gantt_view)
        self.main_layout.addWidget(gantt_group)

        # 3. 任务与控制分割区
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧任务列表
        task_panel = QFrame()
        task_panel.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        tp_layout = QVBoxLayout(task_panel)
        tp_layout.addWidget(QLabel("待处理维护任务池"))
        
        self.task_table = QTableWidget(0, 4)
        self.task_table.setHorizontalHeaderLabels(["任务ID", "维护内容", "难度", "操作"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tp_layout.addWidget(self.task_table)
        
        # 右侧操作日志
        op_panel = QFrame()
        op_panel.setFixedWidth(320)
        op_panel.setStyleSheet("background: #1e293b; border-radius: 12px; color: white;")
        op_layout = QVBoxLayout(op_panel)
        
        self.auto_btn = QPushButton("执行智能调度算法")
        self.auto_btn.setFixedHeight(45)
        self.auto_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auto_btn.setStyleSheet("background: #3b82f6; color: white; font-weight: bold; border-radius: 8px;")
        self.auto_btn.clicked.connect(self.run_auto_scheduling)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #0f172a; border: none; font-family: 'Courier New'; color: #10b981; font-size: 11px;")
        
        op_layout.addWidget(QLabel("调度引擎内核日志"))
        op_layout.addWidget(self.log_area)
        op_layout.addWidget(self.auto_btn)

        bottom_splitter.addWidget(task_panel)
        bottom_splitter.addWidget(op_panel)
        bottom_splitter.setStretchFactor(0, 3)
        self.main_layout.addWidget(bottom_splitter)

        self.refresh_task_table()

    def update_engineer_cards(self):
        # 清空旧卡片
        while self.res_layout.count():
            item = self.res_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for eng in self.engineers:
            card = QFrame()
            card.setFixedWidth(230)
            card.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #e2e8f0; padding: 10px;")
            cl = QVBoxLayout(card)
            
            name_lbl = QLabel(f"{eng.name} ({['','初级','高级','专家'][eng.skill_level]})")
            name_lbl.setStyleSheet("font-weight: bold; color: #1e293b; border: none;")
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(eng.current_load)
            bar.setFixedHeight(8)
            bar.setTextVisible(False)
            bar.setStyleSheet("QProgressBar::chunk { background: #10b981; border-radius: 4px; }")
            
            cl.addWidget(name_lbl)
            cl.addWidget(QLabel(f"科室: {eng.department}", styleSheet="color: #64748b; font-size: 11px; border:none;"))
            cl.addWidget(QLabel(f"当前负载: {eng.current_load}%", styleSheet="border:none;"))
            cl.addWidget(bar)
            self.res_layout.addWidget(card)

    def refresh_task_table(self):
        self.task_table.setRowCount(0)
        for t in self.tasks:
            if t.status == "待排程":
                row = self.task_table.rowCount()
                self.task_table.insertRow(row)
                self.task_table.setItem(row, 0, QTableWidgetItem(t.task_id))
                self.task_table.setItem(row, 1, QTableWidgetItem(t.title))
                self.task_table.setItem(row, 2, QTableWidgetItem("★" * t.skill_req))
                
                btn = QPushButton("分配")
                btn.setStyleSheet("background: #f1f5f9; color: #475569;")
                self.task_table.setCellWidget(row, 3, btn)

    def run_auto_scheduling(self):
        self.log_area.append("> 启动多约束启发式调度算法...")
        unassigned = [t for t in self.tasks if t.status == "待排程"]
        unassigned.sort(key=lambda x: x.priority, reverse=True)
        
        count = 0
        for task in unassigned:
            best_engineer = None
            max_score = -1
            
            for eng in self.engineers:
                score = SchedulingEngine.calculate_match_score(task, eng)
                if score > max_score:
                    potential_start = datetime.datetime.now().replace(hour=9, minute=0, second=0)
                    # 简化逻辑：暂不检查硬碰撞，只做算法分配
                    max_score = score
                    best_engineer = eng
                    start_time = potential_start

            if best_engineer:
                task.status = "已排程"
                task.assigned_engineer = best_engineer.name
                task.start_time = start_time
                best_engineer.current_load = min(100, best_engineer.current_load + 20)
                self.log_area.append(f"[SUCCESS] {task.task_id} 分配至 {best_engineer.name}")
                count += 1

        self.log_area.append(f"> 算法执行完毕，成功分配 {count} 个任务。")
        self.update_engineer_cards()
        self.refresh_task_table()
        self.gantt_view.set_data(self.tasks)

def get_widget():
    return TaskSchedulingModule()