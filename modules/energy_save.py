import sys
import random
import math
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QSlider, 
                             QProgressBar, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QScrollArea, QGroupBox,
                             QDial, QStackedWidget, QMessageBox, QComboBox,
                             QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QFont, QLinearGradient, QRadialGradient, QColor

# ----------------------------------------------------------------
# 1. 核心业务逻辑层：能效与热力分析引擎
# ----------------------------------------------------------------

class EnergyMode:
    AUTO_AI = "动态能效模式 (AI)"
    COOLING_FIRST = "制冷优先模式"
    MAX_PERF = "最大性能模式"
    SILENT = "极地静默模式"

class PowerEfficiencyEngine:
    @staticmethod
    def calculate_pue(it_load, cooling_load, aux_load):
        if it_load <= 0: return 2.0
        total_power = it_load + cooling_load + aux_load
        return round(total_power / it_load, 2)

    @staticmethod
    def estimate_carbon_reduction(saved_kwh):
        return saved_kwh * 0.475

class ThermalPhysicsSimulator:
    def __init__(self, rows=4, cols=8):
        self.rows, self.cols = rows, cols
        self.racks = [[[random.uniform(2.5, 4.8), random.uniform(23.0, 26.0)] 
                      for _ in range(cols)] for _ in range(rows)]

    def compute_step(self, ambient_temp, cooling_efficiency):
        for r in range(self.rows):
            for c in range(self.cols):
                power, temp = self.racks[r][c]
                heat_gen = power * 1.25 
                heat_dissipation = (cooling_efficiency * 0.4) + (25.0 - ambient_temp) * 0.1
                delta_t = heat_gen - heat_dissipation
                new_temp = max(18.5, min(49.5, temp + delta_t * 0.05))
                self.racks[r][c][1] = new_temp
        return self.racks

# ----------------------------------------------------------------
# 2. 视觉呈现层：高精度绘图组件
# ----------------------------------------------------------------

class PueGauge(QWidget):
    def __init__(self, label="实时 PUE 指标"):
        super().__init__()
        self.value = 1.30
        self.label = label
        self.setMinimumSize(220, 220)

    def set_value(self, val):
        self.value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect().adjusted(20, 20, -20, -20)
        center = rect.center()

        # 修正 QPen 参数：参数顺序为 (颜色, 宽度, 线型)
        bg_pen = QPen(QColor("#f1f5f9"), 15, Qt.PenStyle.SolidLine)
        painter.setPen(bg_pen)
        painter.drawArc(rect, -30 * 16, 240 * 16)

        if self.value < 1.25: color = QColor("#10b981")
        elif self.value < 1.6: color = QColor("#3b82f6")
        else: color = QColor("#f43f5e")
        
        # 修正 QPen 参数：显式指定 SolidLine，将 RoundCap 放在第4位
        val_pen = QPen(color, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(val_pen)
        
        span = max(0, min(240, int(240 * (3.0 - self.value) / 2.0)))
        painter.drawArc(rect, (210 - (240 - span)) * 16, (240 - span) * 16)

        painter.setPen(QColor("#1e293b"))
        painter.setFont(QFont("Inter", 26, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.2f}")
        
        painter.setFont(QFont("Inter", 10))
        painter.drawText(center.x() - 40, center.y() + 45, self.label)

class RackHeatMap(QFrame):
    rack_clicked = pyqtSignal(int, int, float, float)

    def __init__(self, rows=4, cols=8):
        super().__init__()
        self.rows, self.cols = rows, cols
        self.data = None
        self.setMinimumHeight(350)

    def update_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        if not self.data: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        padding = 10
        cell_w = (w - padding * 2) / self.cols
        cell_h = (h - padding * 2) / self.rows

        for r in range(self.rows):
            for c in range(self.cols):
                power, temp = self.data[r][c]
                rect = QRectF(padding + c * cell_w, padding + r * cell_h, cell_w - 6, cell_h - 6)
                hue = max(0, min(240, int(240 * (50 - temp) / 30)))
                color = QColor.fromHsv(hue, 210, 230)
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
                painter.drawRoundedRect(rect, 6, 6)
                
                if temp > 42:
                    painter.setPen(QPen(Qt.GlobalColor.white, 2))
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "!")

    def mousePressEvent(self, event):
        if not self.data: return
        w, h = self.width(), self.height()
        cell_w = (w - 20) / self.cols
        cell_h = (h - 20) / self.rows
        c = int((event.position().x() - 10) / cell_w)
        r = int((event.position().y() - 10) / cell_h)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            p, t = self.data[r][c]
            self.rack_clicked.emit(r, c, p, t)

# ----------------------------------------------------------------
# 3. 业务主界面层
# ----------------------------------------------------------------

class EnergyManagementModule(QWidget):
    def __init__(self):
        super().__init__()
        self.simulator = ThermalPhysicsSimulator()
        self.engine = PowerEfficiencyEngine()
        self.it_load_base = 480.0
        self.cooling_power = 120.0
        self.init_ui()
        
        self.ticker = QTimer()
        self.ticker.timeout.connect(self.on_refresh_tick)
        self.ticker.start(1500)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(25)

        # KPI 面板
        kpi_container = QHBoxLayout()
        self.pue_gauge = PueGauge()
        
        dist_card = QFrame()
        dist_card.setStyleSheet("""
            QFrame { background: white; border-radius: 15px; border: 1px solid #e2e8f0; }
            QLabel { border: none; color: #475569; font-weight: bold; background: transparent; }
        """)
        dist_layout = QVBoxLayout(dist_card)
        dist_layout.setContentsMargins(25, 20, 25, 20)
        dist_layout.addWidget(QLabel("IT 核心负载分解 (kW)"))
        self.it_bar = QProgressBar()
        self.it_bar.setFixedHeight(12)
        self.it_bar.setStyleSheet("QProgressBar::chunk { background: #3b82f6; border-radius: 5px; }")
        dist_layout.addWidget(self.it_bar)
        dist_layout.addSpacing(15)
        dist_layout.addWidget(QLabel("制冷与环境损耗 (kW)"))
        self.cool_bar = QProgressBar()
        self.cool_bar.setFixedHeight(12)
        self.cool_bar.setStyleSheet("QProgressBar::chunk { background: #10b981; border-radius: 5px; }")
        dist_layout.addWidget(self.cool_bar)
        
        kpi_container.addWidget(self.pue_gauge, 1)
        kpi_container.addWidget(dist_card, 2)
        self.main_layout.addLayout(kpi_container)

        # 中间 Splitter
        self.mid_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.mid_splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        heat_group = QGroupBox("机房实时热分布图 (点击查看机架详情)")
        heat_group.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 25px; background: white; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 15px; color: #1e293b; }
        """)
        hg_layout = QVBoxLayout(heat_group)
        hg_layout.setContentsMargins(15, 35, 15, 15)
        self.heatmap = RackHeatMap()
        self.heatmap.rack_clicked.connect(self.on_rack_inspected)
        hg_layout.addWidget(self.heatmap)
        
        ctrl_group = QGroupBox("智能能效策略控制")
        ctrl_group.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 25px; background: white; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 15px; color: #1e293b; }
            QLabel { color: #64748b; font-size: 13px; font-weight: normal; border: none; background: transparent; }
        """)
        cg_layout = QVBoxLayout(ctrl_group)
        cg_layout.setContentsMargins(20, 50, 20, 20) # 增大边距，彻底解决文字遮挡
        cg_layout.setSpacing(15)
        
        cg_layout.addWidget(QLabel("当前运行模式方案:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([EnergyMode.AUTO_AI, EnergyMode.COOLING_FIRST, EnergyMode.MAX_PERF, EnergyMode.SILENT])
        self.mode_combo.setMinimumHeight(45)
        self.mode_combo.setStyleSheet("QComboBox { border: 1px solid #cbd5e1; border-radius: 8px; padding-left: 10px; }")
        cg_layout.addWidget(self.mode_combo)
        
        cg_layout.addWidget(QLabel("模拟外部环境温度 (°C):"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(10, 45)
        self.temp_slider.setValue(24)
        self.temp_slider.setFixedHeight(30)
        cg_layout.addWidget(self.temp_slider)
        
        cg_layout.addStretch()
        
        self.migrate_btn = QPushButton("执行热力感知的负载迁移")
        self.migrate_btn.setMinimumHeight(55)
        self.migrate_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; font-weight: bold; border-radius: 10px; font-size: 14px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.migrate_btn.clicked.connect(self.on_run_migration)
        cg_layout.addWidget(self.migrate_btn)

        self.mid_splitter.addWidget(heat_group)
        self.mid_splitter.addWidget(ctrl_group)
        self.mid_splitter.setStretchFactor(0, 3)
        self.mid_splitter.setStretchFactor(1, 1)
        self.main_layout.addWidget(self.mid_splitter)

        self.audit_table = QTableWidget(0, 3)
        self.audit_table.setHorizontalHeaderLabels(["事件时间", "调度决策记录", "节能贡献 (kWh)"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.audit_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.audit_table.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        self.audit_table.setMaximumHeight(200)
        self.main_layout.addWidget(self.audit_table)

    def on_refresh_tick(self):
        ext_temp = self.temp_slider.value()
        self.it_load_base += random.uniform(-5, 5)
        self.it_load_base = max(200, min(800, self.it_load_base))
        self.cooling_power = max(50, (ext_temp - 20) * 4.5 + self.it_load_base * 0.15 + random.uniform(-2, 2))
        
        pue = self.engine.calculate_pue(self.it_load_base, self.cooling_power, 25.0)
        self.pue_gauge.set_value(pue)
        self.it_bar.setValue(int(self.it_load_base / 8))
        self.cool_bar.setValue(int(self.cooling_power / 4))
        
        cool_eff = 40.0 if self.mode_combo.currentText() == EnergyMode.COOLING_FIRST else 25.0
        self.heatmap.update_data(self.simulator.compute_step(ext_temp, cool_eff))

    def on_rack_inspected(self, r, c, p, t):
        self.log_audit("机架巡检", f"坐标[{r},{c}] 功耗:{p:.2f}kW 温度:{t:.1f}°C")

    def on_run_migration(self):
        QTimer.singleShot(500, lambda: QMessageBox.information(self, "迁移引擎", "调度成功：已根据热力模型重新优化负载分布。"))
        self.log_audit("调度成功", f"能效优化完成，减排 {random.uniform(0.5, 2.0):.2f} kg")

    def log_audit(self, action, detail):
        row = self.audit_table.rowCount()
        self.audit_table.insertRow(0)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.audit_table.setItem(0, 0, QTableWidgetItem(ts))
        self.audit_table.setItem(0, 1, QTableWidgetItem(f"{action}: {detail}"))
        self.audit_table.setItem(0, 2, QTableWidgetItem(f"{random.uniform(0.1, 1.5):.2f}"))

def get_widget():
    return EnergyManagementModule()