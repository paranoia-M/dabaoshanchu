import sys
import math
import random
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTreeWidget, QTreeWidgetItem, 
                             QProgressBar, QTextEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSplitter, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

class TicketStatus:
    DETECTED = "已检测"
    ANALYZING = "诊断中"
    PENDING_APPROVAL = "待审批"
    FIXING = "修复中"
    VERIFYING = "校验中"
    CLOSED = "已关闭"

class WorkflowEngine:
    def __init__(self):
        self.valid_transitions = {
            TicketStatus.DETECTED: [TicketStatus.ANALYZING],
            TicketStatus.ANALYZING: [TicketStatus.PENDING_APPROVAL],
            TicketStatus.PENDING_APPROVAL: [TicketStatus.FIXING, TicketStatus.CLOSED],
            TicketStatus.FIXING: [TicketStatus.VERIFYING],
            TicketStatus.VERIFYING: [TicketStatus.CLOSED, TicketStatus.ANALYZING]
        }
    def can_transition(self, current, target):
        return target in self.valid_transitions.get(current, [])

class ProbabilityHeatMap(QFrame):
    def __init__(self):
        super().__init__()
        self.results = []
        self.setMinimumHeight(180)
        self.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")

    def set_data(self, results):
        self.results = results
        self.update()

    def paintEvent(self, event):
        if not self.results: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin, rect_h, gap = 30, 25, 15
        max_w = self.width() - 2*margin - 120
        for i, (cause, prob) in enumerate(self.results):
            y = margin + i * (rect_h + gap)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#f1f5f9")))
            painter.drawRoundedRect(margin, y, max_w, rect_h, 4, 4)
            color = QColor("#3b82f6") if prob > 0.4 else QColor("#94a3b8")
            if prob > 0.7: color = QColor("#ef4444")
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(margin, y, int(max_w * prob), rect_h, 4, 4)
            painter.setPen(QPen(QColor("#1e293b")))
            painter.drawText(margin + max_w + 10, y + 18, f"{cause} ({prob:.1%})")

class FaultDiagModule(QWidget):
    def __init__(self):
        super().__init__()
        self.workflow = WorkflowEngine()
        self.tickets = []
        self.knowledge_base = {
            "延迟突增": {"核心链路拥塞": 0.7, "数据库锁竞争": 0.4},
            "进程死锁": {"内存溢出": 0.6, "存储IO挂起": 0.5},
            "供电异常": {"电源模块故障": 0.9},
            "丢包率超标": {"链路拥塞": 0.5, "光纤受损": 0.8}
        }
        self.init_ui()
        self.load_sample_fault_tree()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        lp_layout = QVBoxLayout(self.left_panel)
        lp_layout.addWidget(QLabel("IT基础设施故障传播树"))
        self.fault_tree = QTreeWidget()
        self.fault_tree.setHeaderLabels(["组件单元", "当前风险"])
        self.fault_tree.itemClicked.connect(self.on_tree_item_clicked)
        lp_layout.addWidget(self.fault_tree)

        # 右侧面板
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)

        self.heat_map = ProbabilityHeatMap()
        rp_layout.addWidget(self.heat_map)
        
        self.diag_console = QTextEdit()
        self.diag_console.setReadOnly(True)
        self.diag_console.setStyleSheet("background: #0f172a; color: #38bdf8; font-family: 'Arial';")
        self.diag_console.setFixedHeight(120)
        rp_layout.addWidget(self.diag_console)
        
        ticket_group = QGroupBox("活动维护任务流转")
        tg_layout = QVBoxLayout(ticket_group)
        self.ticket_table = QTableWidget(0, 4)
        self.ticket_table.setHorizontalHeaderLabels(["任务ID", "级别", "当前阶段", "操作"])
        self.ticket_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tg_layout.addWidget(self.ticket_table)
        
        btn_layout = QHBoxLayout()
        self.btn_analyze = QPushButton("启动根因分析")
        self.btn_analyze.clicked.connect(self.run_probabilistic_diagnosis)
        self.btn_analyze.setStyleSheet("background: #3b82f6; color: white; padding: 8px;")
        btn_layout.addWidget(self.btn_analyze)
        tg_layout.addLayout(btn_layout)

        rp_layout.addWidget(ticket_group)
        splitter.addWidget(self.left_panel)
        splitter.addWidget(right_panel)
        self.main_layout.addWidget(splitter)

    def load_sample_fault_tree(self):
        root = QTreeWidgetItem(self.fault_tree, ["核心业务簇", "中风险"])
        QTreeWidgetItem(root, ["核心交换机", "告警 (丢包)"])
        QTreeWidgetItem(root, ["存储阵列", "正常"])
        self.fault_tree.expandAll()

    def on_tree_item_clicked(self, item, col):
        self.current_symptom = "丢包率超标" if "交换机" in item.text(0) else "延迟突增"
        self.diag_console.append(f"> 识别到组件 {item.text(0)} 异常特征: {self.current_symptom}")

    def run_probabilistic_diagnosis(self):
        symptom = getattr(self, 'current_symptom', "延迟突增")
        causes = self.knowledge_base.get(symptom, {"未知": 1.0})
        results = sorted(causes.items(), key=lambda x: x[1], reverse=True)
        self.heat_map.set_data(results)
        
        # 创建新工单
        t_id = f"T-{random.randint(100,999)}"
        self.tickets.append({"id": t_id, "priority": "紧急", "status": TicketStatus.DETECTED})
        self.refresh_ticket_table()

    def refresh_ticket_table(self):
        self.ticket_table.setRowCount(0)
        for i, t in enumerate(self.tickets):
            row = self.ticket_table.rowCount()
            self.ticket_table.insertRow(row)
            self.ticket_table.setItem(row, 0, QTableWidgetItem(t['id']))
            self.ticket_table.setItem(row, 1, QTableWidgetItem(t['priority']))
            self.ticket_table.setItem(row, 2, QTableWidgetItem(t['status']))
            
            btn = QPushButton("推进")
            # 通过 lambda 传递当前的固定索引
            btn.clicked.connect(lambda checked, r=row: self.advance_ticket_workflow(r))
            self.ticket_table.setCellWidget(row, 3, btn)

    def advance_ticket_workflow(self, row=None):
        if row is None: row = self.ticket_table.currentRow()
        # 严格的边界检查
        if row < 0 or row >= len(self.tickets): return

        ticket = self.tickets[row]
        status_map = [TicketStatus.DETECTED, TicketStatus.ANALYZING, TicketStatus.PENDING_APPROVAL, TicketStatus.FIXING, TicketStatus.VERIFYING, TicketStatus.CLOSED]
        
        try:
            curr_idx = status_map.index(ticket['status'])
            if curr_idx < len(status_map) - 1:
                next_s = status_map[curr_idx + 1]
                if self.workflow.can_transition(ticket['status'], next_s):
                    ticket['status'] = next_s
                    self.diag_console.append(f"[*] {ticket['id']} -> {next_s}")
                    self.refresh_ticket_table()
        except Exception as e:
            print(f"Error: {e}")

def get_widget():
    return FaultDiagModule()