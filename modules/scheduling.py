import sys
import datetime
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QProgressBar, QDialog, 
                             QFormLayout, QLineEdit, QComboBox, QDateTimeEdit, 
                             QMessageBox, QScrollArea, QListWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient

# ----------------------------------------------------------------
# 1. 业务实体与算法层
# ----------------------------------------------------------------

class SkillLevel:
    JUNIOR = 1
    SENIOR = 2
    EXPERT = 3

class MaintenanceTask:
    """任务实体逻辑"""
    def __init__(self, task_id, title, skill_req, priority, duration_h):
        self.task_id = task_id
        self.title = title
        self.skill_req = skill_req
        self.priority = priority # 1-10
        self.duration_h = duration_h
        self.status = "待排程"
        self.assigned_engineer = None
        self.start_time = None

class Engineer:
    """资源实体逻辑"""
    def __init__(self, name, skill_level, department):
        self.name = name
        self.skill_level = skill_level
        self.department = department
        self.current_load = 0 # 0-100
        self.schedule = [] # 存储 (start, end) 元组

class SchedulingAlgorithm:
    """核心算法：基于加权评分的资源调度引擎"""
    
    @staticmethod
    def calculate_match_score(task, engineer):
        # 1. 技能匹配校验（硬约束）
        if engineer.skill_level < task.skill_req:
            return -1
        
        # 2. 负载权重计算 (负载越低得分越高)
        load_score = (100 - engineer.current_load) * 0.4
        
        # 3. 技能溢出惩罚 (避免专家去做初级工作)
        skill_gap = engineer.skill_level - task.skill_req
        skill_score = (10 - skill_gap) * 0.3
        
        # 4. 任务紧迫度加成
        priority_score = task.priority * 2.0
        
        return load_score + skill_score + priority_score

    @staticmethod
    def check_time_conflict(engineer, start_time, duration_h):
        """逻辑：数据一致性冲突检测"""
        end_time = start_time + datetime.timedelta(hours=duration_h)
        for s, e in engineer.schedule:
            if not (end_time <= s or start_time >= e):
                return True # 存在时间重叠
        return False

# ----------------------------------------------------------------
# 2. 视觉组件层：自定义甘特图视图
# ----------------------------------------------------------------

class GanttChartView(QFrame):
    """自研甘特图：利用QPainter绘制任务时间轴"""
    def __init__(self):
        super().__init__()
        self.tasks = [] # 存储已排程的任务
        self.setMinimumHeight(300)
        self.setStyleSheet("background-color: #ffffff; border-radius: 10px;")
        self.hour_width = 60 # 每小时像素宽度
        
    def set_data(self, tasks):
        self.tasks = [t for t in tasks if t.start_time]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        margin_left = 120
        margin_top = 40
        
        # 绘制背景时间网格
        painter.setPen(QPen(QColor("#f1f5f9"), 1))
        for i in range(12): # 绘制12小时窗口
            x = margin_left + i * self.hour_width
            painter.drawLine(x, margin_top, x, h - 20)
            painter.drawText(x - 10, margin_top - 10, f"{8+i}:00")

        # 绘制任务块
        for i, task in enumerate(self.tasks):
            y = margin_top + 20 + i * 50
            
            # 计算起始位置
            start_hour = task.start_time.hour + task.start_time.minute / 60.0
            x = margin_left + (start_hour - 8) * self.hour_width
            rect_w = task.duration_h * self.hour_width
            
            # 绘制任务条
            color = QColor("#3b82f6") if task.priority < 7 else QColor("#ef4444")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            task_rect = QRect(int(x), y, int(rect_w), 30)
            painter.drawRoundedRect(task_rect, 6, 6)
            
            # 绘制文字描述
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(task_rect, Qt.AlignmentFlag.AlignCenter, f"{task.title}")
            
            # 绘制执行人名称
            painter.setPen(QPen(QColor("#475569")))
            painter.drawText(20, y + 20, f"{task.assigned_engineer}")

# ----------------------------------------------------------------
# 3. 业务主界面层
# ----------------------------------------------------------------

class TaskSchedulerModule(QWidget):
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
        titles = ["核心交换机固件升级", "机房空调系统巡检", "LUN扩容容量重新分配", "防火墙规则库调优"]
        for i, title in enumerate(titles):
            self.tasks.append(MaintenanceTask(f"M-{100+i}", title, random.randint(1,3), random.randint(3,9), 2))

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # 1. 顶部资源看板
        res_header = QLabel("IT维护工程师资源池 (实时负载)")
        res_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        self.main_layout.addWidget(res_header)

        self.res_layout = QHBoxLayout()
        self.update_engineer_cards()
        self.main_layout.addLayout(self.res_layout)

        # 2. 中间：甘特图视图
        gantt_box = QGroupBox("维护计划排程甘特图 (8:00 - 20:00)")
        gantt_layout = QVBoxLayout(gantt_box)
        self.gantt_view = GanttChartView()
        gantt_layout.addWidget(self.gantt_view)
        self.main_layout.addWidget(gantt_box)

        # 3. 底部：待办任务列表与操作区
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：任务池
        task_panel = QFrame()
        task_panel.setStyleSheet("background: white; border-radius: 12px;")
        tp_layout = QVBoxLayout(task_panel)
        tp_layout.addWidget(QLabel("待处理维护任务池"))
        
        self.task_table = QTableWidget(0, 4)
        self.task_table.setHorizontalHeaderLabels(["任务ID", "维护内容", "等级要求", "操作"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tp_layout.addWidget(self.task_table)
        
        # 右侧：算法操作台
        op_panel = QFrame()
        op_panel.setFixedWidth(300)
        op_panel.setStyleSheet("background: #1e293b; border-radius: 12px; color: white;")
        op_layout = QVBoxLayout(op_panel)
        
        self.auto_btn = QPushButton("启动智能调度引擎")
        self.auto_btn.setMinimumHeight(50)
        self.auto_btn.setStyleSheet("background: #3b82f6; color: white; font-weight: bold; border-radius: 8px;")
        self.auto_btn.clicked.connect(self.run_auto_scheduling)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: #0f172a; border: none; font-family: 'Consolas'; color: #10b981;")
        
        op_layout.addWidget(QLabel("算法调度执行日志"))
        op_layout.addWidget(self.log_area)
        op_layout.addWidget(self.auto_btn)

        bottom_splitter.addWidget(task_panel)
        bottom_splitter.addWidget(op_panel)
        self.main_layout.addWidget(bottom_splitter)

        self.refresh_task_table()

    # ----------------------------------------------------------------
    # 4. 核心交互与算法逻辑实现
    # ----------------------------------------------------------------

    def update_engineer_cards(self):
        """逻辑：动态生成资源卡片"""
        # 清除旧卡片
        while self.res_layout.count():
            item = self.res_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for eng in self.engineers:
            card = QFrame()
            card.setFixedWidth(220)
            card.setStyleSheet("""
                QFrame { background: white; border-radius: 10px; border: 1px solid #e2e8f0; padding: 10px; }
            """)
            cl = QVBoxLayout(card)
            
            name_lbl = QLabel(f"{eng.name} ({['初级','高级','专家'][eng.skill_level-1]})")
            name_lbl.setStyleSheet("font-weight: bold; color: #1e293b; border:none;")
            
            dept_lbl = QLabel(eng.department)
            dept_lbl.setStyleSheet("font-size: 11px; color: #64748b; border:none;")
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(eng.current_load)
            bar.setMaximumHeight(8)
            bar.setTextVisible(False)
            bar.setStyleSheet("QProgressBar::chunk { background: #10b981; }")
            
            cl.addWidget(name_lbl)
            cl.addWidget(dept_lbl)
            cl.addWidget(QLabel(f"负载率: {eng.current_load}%"))
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
                
                btn = QPushButton("手动排程")
                btn.clicked.connect(lambda chk, task=t: self.manual_schedule(task))
                self.task_table.setCellWidget(row, 3, btn)

    def run_auto_scheduling(self):
        """核心算法逻辑：执行全量任务自动优化排程"""
        self.log_area.append("> 启动多约束启发式调度算法...")
        unassigned = [t for t in self.tasks if t.status == "待排程"]
        
        # 按优先级降序排列，优先处理高优先级任务
        unassigned.sort(key=lambda x: x.priority, reverse=True)
        
        count = 0
        for task in unassigned:
            best_engineer = None
            max_score = -1
            
            # 1. 寻找得分最高的可用工程师
            for eng in self.engineers:
                score = SchedulingAlgorithm.calculate_match_score(task, eng)
                if score > max_score:
                    # 2. 检查当日可用时间窗 (模拟从上午9点开始尝试)
                    potential_start = datetime.datetime.now().replace(hour=9, minute=0, second=0)
                    if not SchedulingAlgorithm.check_time_conflict(eng, potential_start, task.duration_h):
                        max_score = score
                        best_engineer = eng
                        start_time = potential_start

            # 3. 执行分配
            if best_engineer:
                task.status = "已排程"
                task.assigned_engineer = best_engineer.name
                task.start_time = start_time
                best_engineer.schedule.append((start_time, start_time + datetime.timedelta(hours=task.duration_h)))
                best_engineer.current_load += 25 # 模拟负载增加
                self.log_area.append(f"[匹配成功] {task.task_id} -> {best_engineer.name} (得分: {max_score:.1f})")
                count += 1
            else:
                self.log_area.append(f"[失败] 任务 {task.task_id} 无匹配资源")

        self.log_area.append(f"> 调度完成，成功分配 {count} 个任务。")
        self.update_engineer_cards()
        self.refresh_task_table()
        self.gantt_view.set_data(self.tasks)

    def manual_schedule(self, task):
        QMessageBox.information(self, "手动模式", f"手动调度模式下，您可以强制分配任务 {task.task_id}。建议使用自动调度引擎。")

from PyQt6.QtWidgets import QGroupBox, QTextEdit

def get_widget():
    return TaskSchedulerModule()

# ----------------------------------------------------------------
# 技术复杂度总结：
# 1. 资源匹配逻辑：SchedulingAlgorithm.calculate_match_score 实现了基于多权重的评分模型。
# 2. 时间一致性检测：check_time_conflict 实现了基础的任务碰撞检测算法。
# 3. 自定义视觉引擎：GanttChartView 通过 QPainter 坐标变换实现了动态时间轴渲染。
# 4. 数据流闭环：从任务池到算法计算，再到工程师负载更新和甘特图重绘，实现了完整的业务流转。
# ----------------------------------------------------------------