import sys
import math
import random
import datetime
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTreeWidget, QTreeWidgetItem, 
                             QProgressBar, QTextEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSplitter, QGroupBox, QSlider, QDialog,
                             QFormLayout, QLineEdit, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon, QLinearGradient

# ----------------------------------------------------------------
# 1. 核心算法层：概率诊断引擎与故障树建模
# ----------------------------------------------------------------

class InferenceEngine:
    """概率诊断引擎：模拟贝叶斯推断计算根因概率"""
    
    def __init__(self):
        # 定义症状与根因的关联强度 (Symptom -> {RootCause: Probability})
        self.knowledge_base = {
            "延迟突增": {"核心链路拥塞": 0.7, "数据库锁竞争": 0.4, "网卡硬件老化": 0.2},
            "进程死锁": {"内存溢出": 0.6, "存储IO挂起": 0.5, "配置脚本错误": 0.3},
            "供电异常": {"电源模块模块故障": 0.9, "环境温控失效": 0.4},
            "丢包率超标": {"核心链路拥塞": 0.5, "光纤跳线受损": 0.8}
        }

    def diagnose(self, observed_symptoms):
        """执行推理：计算给定症状下各原因的得分"""
        scores = {}
        for symptom in observed_symptoms:
            if symptom in self.knowledge_base:
                causes = self.knowledge_base[symptom]
                for cause, prob in causes.items():
                    scores[cause] = scores.get(cause, 0) + prob
        
        # 归一化处理
        total = sum(scores.values()) if scores else 1
        sorted_results = sorted(
            [(k, v/total) for k, v in scores.items()], 
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_results

# ----------------------------------------------------------------
# 2. 状态机层：维护工单全生命周期管理
# ----------------------------------------------------------------

class TicketStatus:
    DETECTED = "已检测"
    ANALYZING = "诊断中"
    PENDING_APPROVAL = "待审批"
    FIXING = "修复中"
    VERIFYING = "校验中"
    CLOSED = "已关闭"

class WorkflowEngine:
    """工单流转逻辑：严格控制状态转换规则"""
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

# ----------------------------------------------------------------
# 3. 视觉组件层：概率热力图渲染器
# ----------------------------------------------------------------

class ProbabilityHeatMap(QFrame):
    """自定义绘图：展示根因概率分布热力图"""
    def __init__(self):
        super().__init__()
        self.results = [] # [(Cause, Prob)]
        self.setMinimumHeight(180)
        self.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")

    def set_data(self, results):
        self.results = results
        self.update()

    def paintEvent(self, event):
        if not self.results: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        margin = 30
        rect_h = 25
        gap = 15
        max_w = self.width() - 2*margin - 120 # 预留文字空间

        for i, (cause, prob) in enumerate(self.results):
            y = margin + i * (rect_h + gap)
            
            # 绘制背景条
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#f1f5f9")))
            painter.drawRoundedRect(margin, y, max_w, rect_h, 4, 4)
            
            # 绘制概率条 (根据概率改变颜色)
            color = QColor("#3b82f6") if prob > 0.4 else QColor("#94a3b8")
            if prob > 0.7: color = QColor("#ef4444")
            
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(margin, y, int(max_w * prob), rect_h, 4, 4)
            
            # 绘制标签
            painter.setPen(QPen(QColor("#1e293b")))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(margin + max_w + 10, y + 18, f"{cause} ({prob:.1%})")

# ----------------------------------------------------------------
# 4. 主业务界面层
# ----------------------------------------------------------------

class FaultPredictionModule(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = InferenceEngine()
        self.workflow = WorkflowEngine()
        self.tickets = []
        self.init_ui()
        self.load_sample_fault_tree()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 头部导航
        header = QLabel("智能故障预测与根因辅助系统")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b;")
        layout.addWidget(header)

        # 核心分割布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- 左侧：故障树与风险评估 ---
        left_panel = QFrame()
        left_panel.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.addWidget(QLabel("IT基础设施故障传播树"))
        
        self.fault_tree = QTreeWidget()
        self.fault_tree.setHeaderLabels(["组件单元", "当前风险度"])
        self.fault_tree.setColumnCount(2)
        self.fault_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.fault_tree.itemClicked.connect(self.on_tree_item_clicked)
        lp_layout.addWidget(self.fault_tree)

        # --- 右侧：诊断引擎与工作流 ---
        right_panel = QWidget()
        rp_layout = QVBoxLayout(right_panel)
        rp_layout.setContentsMargins(0, 0, 0, 0)

        # 1. 诊断输出区
        diag_group = QGroupBox("实时诊断分析报告")
        dg_layout = QVBoxLayout(diag_group)
        self.heat_map = ProbabilityHeatMap()
        dg_layout.addWidget(self.heat_map)
        
        self.diag_console = QTextEdit()
        self.diag_console.setReadOnly(True)
        self.diag_console.setStyleSheet("background: #0f172a; color: #38bdf8; font-family: 'Consolas';")
        self.diag_console.setFixedHeight(120)
        dg_layout.addWidget(self.diag_console)
        
        # 2. 维护工单控制台
        ticket_group = QGroupBox("活动维护任务流转")
        tg_layout = QVBoxLayout(ticket_group)
        self.ticket_table = QTableWidget(0, 4)
        self.ticket_table.setHorizontalHeaderLabels(["任务ID", "级别", "当前阶段", "操作"])
        self.ticket_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tg_layout.addWidget(self.ticket_table)
        
        action_bar = QHBoxLayout()
        self.btn_analyze = QPushButton("启动根因分析")
        self.btn_analyze.setStyleSheet("background: #3b82f6; color: white; padding: 8px;")
        self.btn_analyze.clicked.connect(self.run_probabilistic_diagnosis)
        
        self.btn_approve = QPushButton("审批通过进入修复")
        self.btn_approve.setStyleSheet("background: #10b981; color: white; padding: 8px;")
        self.btn_approve.clicked.connect(self.advance_ticket_workflow)
        
        action_bar.addWidget(self.btn_analyze)
        action_bar.addWidget(self.btn_approve)
        tg_layout.addLayout(action_bar)

        rp_layout.addWidget(diag_group)
        rp_layout.addWidget(ticket_group)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)

    # ----------------------------------------------------------------
    # 5. 核心业务逻辑实现
    # ----------------------------------------------------------------

    def load_sample_fault_tree(self):
        """逻辑：递归构建故障树单元"""
        root = QTreeWidgetItem(self.fault_tree, ["核心业务簇 (Cluster-01)", "中风险"])
        
        network = QTreeWidgetItem(root, ["骨干网络链路", "低风险"])
        QTreeWidgetItem(network, ["光纤交换机 A", "正常"])
        QTreeWidgetItem(network, ["光纤交换机 B", "告警 (丢包率12%)"])
        
        storage = QTreeWidgetItem(root, ["存储资源池", "高风险"])
        QTreeWidgetItem(storage, ["控制器 LUN-01", "正常"])
        QTreeWidgetItem(storage, ["SAS 物理盘槽位-09", "预警 (S.M.A.R.T 错误)"])
        
        self.fault_tree.expandAll()

    def on_tree_item_clicked(self, item, col):
        """交互：选择不同节点触发不同的症状注入"""
        node_name = item.text(0)
        self.diag_console.append(f"> 选中单元: {node_name}，正在采集实时遥测特征...")
        
        # 模拟症状自动识别逻辑
        if "交换机" in node_name:
            self.current_symptoms = ["延迟突增", "丢包率超标"]
        elif "盘" in node_name or "存储" in node_name:
            self.current_symptoms = ["进程死锁", "供电异常"]
        else:
            self.current_symptoms = ["延迟突增"]
        
        self.diag_console.append(f"> 识别到异常特征向量: {self.current_symptoms}")

    def run_probabilistic_diagnosis(self):
        """核心算法：执行推理并更新热力图"""
        if not hasattr(self, 'current_symptoms'):
            QMessageBox.information(self, "提示", "请先在左侧故障树中选择一个受影响的实体单元")
            return

        self.diag_console.append("> 正在初始化贝叶斯推断引擎...")
        results = self.engine.diagnose(self.current_symptoms)
        
        # 模拟延迟感
        QTimer.singleShot(800, lambda: self._finalize_diagnosis(results))

    def _finalize_diagnosis(self, results):
        self.heat_map.set_data(results)
        self.diag_console.append(f"> 根因定位完成。最可能原因: {results[0][0]}，置信度: {results[0][1]:.2%}")
        
        # 自动生成工单
        ticket_id = f"TICK-{random.randint(1000, 9999)}"
        new_ticket = {"id": ticket_id, "priority": "CRITICAL", "status": TicketStatus.DETECTED}
        self.tickets.append(new_ticket)
        self.refresh_ticket_table()

    def refresh_ticket_table(self):
        self.ticket_table.setRowCount(0)
        for t in self.tickets:
            row = self.ticket_table.rowCount()
            self.ticket_table.insertRow(row)
            self.ticket_table.setItem(row, 0, QTableWidgetItem(t['id']))
            self.ticket_table.setItem(row, 1, QTableWidgetItem(t['priority']))
            
            status_item = QTableWidgetItem(t['status'])
            if t['status'] == TicketStatus.PENDING_APPROVAL:
                status_item.setBackground(QColor("#fef3c7"))
            self.ticket_table.setItem(row, 2, status_item)
            
            btn = QPushButton("推进流转")
            btn.clicked.connect(lambda chk, r=row: self.advance_ticket_workflow(r))
            self.ticket_table.setCellWidget(row, 3, btn)

    def advance_ticket_workflow(self, row=None):
        """核心逻辑：状态机驱动的工作流流转"""
        if row is None: # 顶部全局按钮逻辑
            row = self.ticket_table.currentRow()
            if row == -1: return

        ticket = self.tickets[row]
        current = ticket['status']
        
        # 定义下一个状态逻辑
        status_map = [
            TicketStatus.DETECTED, TicketStatus.ANALYZING, 
            TicketStatus.PENDING_APPROVAL, TicketStatus.FIXING, 
            TicketStatus.VERIFYING, TicketStatus.CLOSED
        ]
        
        try:
            curr_idx = status_map.index(current)
            if curr_idx < len(status_map) - 1:
                next_status = status_map[curr_idx + 1]
                
                # 调用状态机校验器
                if self.workflow.can_transition(current, next_status):
                    ticket['status'] = next_status
                    self.diag_console.append(f"[*] 工单 {ticket['id']} 状态变更: {current} -> {next_status}")
                    self.refresh_ticket_table()
                else:
                    QMessageBox.warning(self, "逻辑拦截", "当前状态不可越级流转")
        except ValueError:
            pass

def get_widget():
    return FaultPredictionModule()
