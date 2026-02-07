import sys
import time
import random
import math
import collections
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QComboBox, 
                             QSlider, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPolygonF, QLinearGradient

# ----------------------------------------------------------------
# 核心逻辑层：性能采样引擎与异常检测算法
# ----------------------------------------------------------------

class PerformanceMetrics:
    """性能指标元数据定义"""
    def __init__(self, name, unit, color):
        self.name = name
        self.unit = unit
        self.color = color
        self.history = collections.deque(maxlen=200) # 滑动窗口大小
        self.ema = 0.0 # 指数移动平均
        self.std_dev = 0.0 # 标准差

class SampleWorker(QThread):
    """后台采样线程：模拟高频数据获取"""
    data_ready = pyqtSignal(dict)

    def __init__(self, frequency=0.5):
        super().__init__()
        self.frequency = frequency
        self.running = True
        self.base_load = 30.0

    def run(self):
        phase = 0.0
        while self.running:
            # 核心算法：基于正弦波+布朗运动模拟真实的服务器负载波动
            phase += 0.1
            noise = random.uniform(-2, 2)
            sine_wave = math.sin(phase) * 10
            
            # 模拟不同维度的 IT 指标
            metrics = {
                "CPU Usage": min(100, max(0, self.base_load + sine_wave + noise)),
                "Memory Load": min(100, max(0, 60 + math.cos(phase * 0.5) * 5 + noise * 0.5)),
                "Disk I/O": min(5000, max(0, 800 + random.randint(-200, 1500))),
                "Network Throughput": min(1000, max(0, 150 + random.uniform(0, 300)))
            }
            self.data_ready.emit(metrics)
            time.sleep(self.frequency)

    def stop(self):
        self.running = False

# ----------------------------------------------------------------
# 视觉表现层：自研高性能实时绘图引擎
# ----------------------------------------------------------------

class RealTimeGraph(QFrame):
    """自研绘图组件：利用QPainter实现平滑的波形滚动"""
    def __init__(self, title, color):
        super().__init__()
        self.title = title
        self.line_color = QColor(color)
        self.data = collections.deque([0.0] * 100, maxlen=100)
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: #0f172a; border-radius: 8px;")
        
    def update_data(self, val):
        self.data.append(val)
        self.update() # 触发 paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        padding = 40

        # 1. 绘制网格线
        grid_pen = QPen(QColor("#1e293b"), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        for i in range(5):
            y = padding + i * (h - 2 * padding) / 4
            painter.drawLine(padding, int(y), w - padding, int(y))

        # 2. 坐标变换逻辑：将原始数据映射到像素坐标
        points = QPolygonF()
        max_val = max(self.data) if max(self.data) > 100 else 100
        x_step = (w - 2 * padding) / (len(self.data) - 1)
        
        for i, val in enumerate(self.data):
            x = padding + i * x_step
            # 翻转Y轴：0在底部
            y = (h - padding) - (val / max_val * (h - 2 * padding))
            points.append(QPointF(x, y))

        # 3. 绘制填充渐变色区域
        fill_path = QPolygonF(points)
        fill_path.append(QPointF(w - padding, h - padding))
        fill_path.append(QPointF(padding, h - padding))
        
        gradient = QLinearGradient(0, padding, 0, h - padding)
        gradient.setColorAt(0, self.line_color)
        gradient.setStart(0, padding)
        gradient.setFinalStop(0, h-padding)
        gradient.setColorAt(1, QColor(self.line_color.red(), self.line_color.green(), self.line_color.blue(), 20))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(fill_path)

        # 4. 绘制核心曲线
        line_pen = QPen(self.line_color, 2, Qt.PenStyle.SolidLine)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(points)

        # 5. 绘制文本标签
        painter.setPen(QColor("#94a3b8"))
        painter.setFont(QFont("Consolas", 9))
        painter.drawText(QRectF(padding, 10, 200, 20), Qt.AlignmentFlag.AlignLeft, f"{self.title}: {self.data[-1]:.1f}")

# ----------------------------------------------------------------
# 业务交互层：主监控模块
# ----------------------------------------------------------------

class PerformanceMonitorModule(QWidget):
    def __init__(self):
        super().__init__()
        self.metrics = {
            "CPU Usage": PerformanceMetrics("CPU Usage", "%", "#3b82f6"),
            "Memory Load": PerformanceMetrics("Memory Load", "%", "#10b981"),
            "Disk I/O": PerformanceMetrics("Disk I/O", "MB/s", "#f59e0b"),
            "Network Throughput": PerformanceMetrics("Network", "Mbps", "#8b5cf6")
        }
        self.anomaly_logs = []
        self.init_ui()
        self.start_sampling()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # --- 顶部控制栏 ---
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(20, 15, 20, 15)

        title_sec = QVBoxLayout()
        title_main = QLabel("实时资源遥测中心")
        title_main.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b; border:none;")
        title_sub = QLabel("内核级采样频率: 2Hz | 异常检测算法: Z-Score")
        title_sub.setStyleSheet("font-size: 12px; color: #64748b; border:none;")
        title_sec.addWidget(title_main)
        title_sec.addWidget(title_sub)

        ctrl_layout.addLayout(title_sec)
        ctrl_layout.addStretch()

        self.freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.freq_slider.setRange(1, 10)
        self.freq_slider.setValue(5)
        self.freq_slider.setFixedWidth(150)
        
        self.stress_btn = QPushButton("开启压力模拟")
        self.stress_btn.setCheckable(True)
        self.stress_btn.setMinimumSize(120, 40)
        self.stress_btn.setStyleSheet("""
            QPushButton { background-color: #f1f5f9; color: #475569; border-radius: 8px; font-weight: bold; }
            QPushButton:checked { background-color: #ef4444; color: white; }
        """)
        self.stress_btn.clicked.connect(self.toggle_stress)

        ctrl_layout.addWidget(QLabel("采样延时:"))
        ctrl_layout.addWidget(self.freq_slider)
        ctrl_layout.addSpacing(20)
        ctrl_layout.addWidget(self.stress_btn)

        # --- 中间图表网格 ---
        chart_grid = QGridLayout()
        self.graphs = {}
        row, col = 0, 0
        for name, m in self.metrics.items():
            g = RealTimeGraph(name, m.color)
            chart_grid.addWidget(g, row, col)
            self.graphs[name] = g
            col += 1
            if col > 1:
                col = 0
                row += 1

        # --- 底部详细指标与异常追踪 ---
        bottom_layout = QHBoxLayout()
        
        # 1. 异常记录列表
        self.alert_table = QTableWidget(0, 3)
        self.alert_table.setHorizontalHeaderLabels(["时间戳", "指标名称", "异常描述"])
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alert_table.setStyleSheet("background-color: white; border-radius: 8px;")
        
        # 2. 资源调度模拟
        scheduler_card = QFrame()
        scheduler_card.setFixedWidth(350)
        scheduler_card.setStyleSheet("background-color: #1e293b; border-radius: 12px; color: #94a3b8;")
        sched_layout = QVBoxLayout(scheduler_card)
        sched_layout.addWidget(QLabel("资源调度分配算法仿真"))
        
        self.sched_log = QTextEdit()
        self.sched_log.setReadOnly(True)
        self.sched_log.setStyleSheet("background: transparent; border: none; font-family: 'Consolas'; font-size: 11px; color: #10b981;")
        sched_layout.addWidget(self.sched_log)

        bottom_layout.addWidget(self.alert_table, 2)
        bottom_layout.addWidget(scheduler_card, 1)

        self.main_layout.addWidget(ctrl_card)
        self.main_layout.addLayout(chart_grid)
        self.main_layout.addLayout(bottom_layout)

    # ----------------------------------------------------------------
    # 核心算法实现：异常检测与负载均衡仿真
    # ----------------------------------------------------------------

    def start_sampling(self):
        self.worker = SampleWorker()
        self.worker.data_ready.connect(self.process_new_data)
        self.worker.start()

    def process_new_data(self, data):
        """核心业务规则处理函数"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]
        
        for name, val in data.items():
            m = self.metrics[name]
            m.history.append(val)
            
            # 1. 更新UI图表
            if name in self.graphs:
                self.graphs[name].update_data(val)

            # 2. 核心算法：实时异常检测 (Z-Score)
            if len(m.history) > 30:
                mean = sum(m.history) / len(m.history)
                variance = sum((x - mean) ** 2 for x in m.history) / len(m.history)
                std = math.sqrt(variance)
                
                # 如果当前值偏离均值超过 2.5 倍标准差，判定为突发异常
                if std > 0 and abs(val - mean) > 2.5 * std:
                    self.log_anomaly(timestamp, name, val, mean)

        # 3. 模拟资源调度算法逻辑
        if random.random() > 0.8:
            self.simulate_resource_scheduling(data)

    def log_anomaly(self, ts, name, val, mean):
        row = self.alert_table.rowCount()
        self.alert_table.insertRow(0)
        self.alert_table.setItem(0, 0, QTableWidgetItem(ts))
        self.alert_table.setItem(0, 1, QTableWidgetItem(name))
        
        diff_pct = ((val - mean) / mean * 100) if mean != 0 else 0
        desc = f"突降 {abs(diff_pct):.1f}%" if val < mean else f"激增 {diff_pct:.1f}%"
        item = QTableWidgetItem(f"检测到抖动: {desc} (当前值: {val:.1f})")
        item.setForeground(QColor("#ef4444"))
        self.alert_table.setItem(0, 2, item)
        
        if self.alert_table.rowCount() > 50:
            self.alert_table.removeRow(50)

    def simulate_resource_scheduling(self, data):
        """资源调度算法：模拟加权负载均衡器对任务重分配的处理"""
        cpu = data["CPU Usage"]
        action = "维持现状"
        if cpu > 80:
            action = "触发冷迁移：迁移容器至 Node-B"
        elif cpu < 20:
            action = "触发能效模式：合并节点实例"
        
        self.sched_log.append(f"> [Task] {action}")
        # 自动滚动底部
        self.sched_log.verticalScrollBar().setValue(self.sched_log.verticalScrollBar().maximum())

    def toggle_stress(self):
        if self.stress_btn.isChecked():
            self.worker.base_load = 85.0
            self.sched_log.append("!!! 系统进入压力模拟模式 !!!")
        else:
            self.worker.base_load = 30.0
            self.sched_log.append("--- 压力模拟已停止 ---")

    def closeEvent(self, event):
        self.worker.stop()
        self.worker.wait()
        super().closeEvent(event)

# 为了兼容性导入缺失的库
import datetime
from PyQt6.QtWidgets import QTextEdit

def get_widget():
    return PerformanceMonitorModule()