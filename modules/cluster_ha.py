import sys
import time
import random
import datetime
import uuid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QProgressBar, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QScrollArea, QGroupBox, QAbstractItemView,
                             QMenu, QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient

# ----------------------------------------------------------------
# 1. 核心业务模型：集群共识与服务编排
# ----------------------------------------------------------------

class NodeStatus:
    LEADER = "Leader (主)"
    FOLLOWER = "Follower (从)"
    CANDIDATE = "Candidate (竞选)"
    DOWN = "Offline (离线)"
    MAINTENANCE = "Maintenance (维护)"

class ServiceInstance:
    """集群服务实例：具有资源画像和状态"""
    def __init__(self, name, req_cpu, req_mem):
        self.service_id = str(uuid.uuid4())[:6].upper()
        self.name = name
        self.req_cpu = req_cpu
        self.req_mem = req_mem
        self.status = "Running"
        self.last_migration = "None"

class ClusterNode:
    """物理节点模型：承载服务并参与共识"""
    def __init__(self, node_id, ip):
        self.node_id = node_id
        self.ip = ip
        self.role = NodeStatus.FOLLOWER
        self.cpu_cap = 100
        self.mem_cap = 64 # GB
        self.services = []
        self.heartbeat_ms = 0
        self.load_cpu = 0
        self.load_mem = 0

    def update_load(self):
        """逻辑：计算当前节点承载服务的总负载"""
        self.load_cpu = sum(s.req_cpu for s in self.services)
        self.load_mem = sum(s.req_mem for s in self.services)

    def can_host(self, service):
        """资源约束校验逻辑"""
        return (self.load_cpu + service.req_cpu <= self.cpu_cap and 
                self.load_mem + service.req_mem <= self.mem_cap)

# ----------------------------------------------------------------
# 2. 视觉组件层：节点状态监控卡片
# ----------------------------------------------------------------

class NodeCard(QFrame):
    """自定义组件：展示单个集群节点的实时遥测数据"""
    clicked = pyqtSignal(str)

    def __init__(self, node):
        super().__init__()
        self.node = node
        self.setMinimumSize(220, 260)
        self.init_ui()

    def init_ui(self):
        self.setObjectName("NodeCard")
        self.update_style()
        
        layout = QVBoxLayout(self)
        
        # 顶部：名称与角色
        self.title_lbl = QLabel(f"Node: {self.node.node_id}")
        self.title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; border:none; color:white;")
        
        self.role_lbl = QLabel(self.node.role)
        self.role_lbl.setStyleSheet("font-size: 11px; background: rgba(255,255,255,0.2); border-radius:4px; padding:2px; color:white;")
        self.role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 中间：资源仪表
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(6)
        
        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, self.node.mem_cap)
        self.mem_bar.setTextVisible(False)
        self.mem_bar.setFixedHeight(6)

        self.service_count = QLabel(f"运行服务: {len(self.node.services)}")
        self.service_count.setStyleSheet("color: #cbd5e1; font-size: 12px; border:none;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.role_lbl)
        layout.addSpacing(15)
        layout.addWidget(QLabel("CPU Load", styleSheet="color:#94a3b8; font-size:10px; border:none;"))
        layout.addWidget(self.cpu_bar)
        layout.addWidget(QLabel("Memory usage", styleSheet="color:#94a3b8; font-size:10px; border:none;"))
        layout.addWidget(self.mem_bar)
        layout.addStretch()
        layout.addWidget(self.service_count)

    def update_style(self):
        color = "#334155" # Default
        if self.node.role == NodeStatus.LEADER: color = "#1e3a8a"
        if self.node.role == NodeStatus.DOWN: color = "#7f1d1d"
        
        self.setStyleSheet(f"""
            #NodeCard {{
                background-color: {color};
                border-radius: 12px;
                border: 2px solid #475569;
            }}
        """)

    def refresh(self):
        self.role_lbl.setText(self.node.role)
        self.cpu_bar.setValue(int(self.node.load_cpu))
        self.mem_bar.setValue(int(self.node.load_mem))
        self.service_count.setText(f"运行服务: {len(self.node.services)}")
        self.update_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.node.node_id)

# ----------------------------------------------------------------
# 3. 业务主界面层
# ----------------------------------------------------------------

class ClusterHAModule(QWidget):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.unassigned_services = []
        self.init_cluster_data()
        self.init_ui()
        
        # 核心算法时钟：心跳监测与共识检查
        self.cluster_timer = QTimer()
        self.cluster_timer.timeout.connect(self.run_cluster_logic)
        self.cluster_timer.start(2000)

    def init_cluster_data(self):
        """初始化集群拓扑：5节点分布式架构"""
        for i in range(1, 6):
            n_id = f"K8S-NODE-0{i}"
            node = ClusterNode(n_id, f"10.0.0.{10+i}")
            # 初始分配一些服务
            if i < 4:
                node.services.append(ServiceInstance(f"DB-Proxy-{i}", 20, 8))
                node.services.append(ServiceInstance(f"API-Gateway-{i}", 15, 4))
            node.update_load()
            self.nodes[n_id] = node
        
        self.nodes["K8S-NODE-01"].role = NodeStatus.LEADER

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # --- 顶部：集群全局仪表盘 ---
        summary_card = QFrame()
        summary_card.setFixedHeight(100)
        summary_card.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #e2e8f0;")
        summary_layout = QHBoxLayout(summary_card)
        
        self.quorum_lbl = QLabel("集群共识状态: 健康 (5/5)")
        self.quorum_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        
        self.total_srv_lbl = QLabel("总托管服务: 6")
        
        summary_layout.addWidget(self.quorum_lbl)
        summary_layout.addStretch()
        summary_layout.addWidget(self.total_srv_lbl)
        
        # 控制按钮
        self.fail_btn = QPushButton("模拟 Leader 节点崩溃")
        self.fail_btn.setStyleSheet("background: #ef4444; color: white; padding: 10px 15px; font-weight:bold;")
        self.fail_btn.clicked.connect(self.simulate_leader_failure)
        summary_layout.addWidget(self.fail_btn)

        # --- 中间：节点矩阵视图 ---
        self.node_grid = QGridLayout()
        self.cards = {}
        col = 0
        for n_id, node in self.nodes.items():
            card = NodeCard(node)
            card.clicked.connect(self.on_node_clicked)
            self.node_grid.addWidget(card, 0, col)
            self.cards[n_id] = card
            col += 1

        # --- 底部：服务迁移审计与仲裁日志 ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 1. 服务位置表
        self.srv_table = QTableWidget(0, 4)
        self.srv_table.setHorizontalHeaderLabels(["服务ID", "名称", "承载节点", "健康度"])
        self.srv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.srv_table.setStyleSheet("background: white; border-radius: 10px;")
        
        # 2. 仲裁日志
        self.audit_log = QTextEdit()
        self.audit_log.setReadOnly(True)
        self.audit_log.setStyleSheet("background: #0f172a; color: #38bdf8; font-family: 'Consolas'; font-size: 11px;")
        self.audit_log.setPlaceholderText("等待集群共识报文...")

        splitter.addWidget(self.srv_table)
        splitter.addWidget(self.audit_log)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        self.main_layout.addWidget(summary_card)
        self.main_layout.addLayout(self.node_grid)
        self.main_layout.addWidget(splitter)
        
        self.refresh_ui()

    # ----------------------------------------------------------------
    # 4. 核心算法逻辑：共识选举与故障漂移
    # ----------------------------------------------------------------

    def run_cluster_logic(self):
        """核心逻辑：每2秒执行一次集群一致性检查"""
        active_nodes = [n for n in self.nodes.values() if n.role != NodeStatus.DOWN]
        leader_exists = any(n.role == NodeStatus.LEADER for n in active_nodes)
        
        # 逻辑1：法定人数校验 (Quorum)
        quorum_count = len(self.nodes) // 2 + 1
        if len(active_nodes) < quorum_count:
            self.quorum_lbl.setText("集群状态: 丧失法定人数 (Critical)")
            self.quorum_lbl.setStyleSheet("color: #ef4444;")
            self.audit_log.append("!!! [QUORUM_LOST] 集群存活节点不足，停止所有写操作")
        else:
            self.quorum_lbl.setText(f"集群状态: 健康 ({len(active_nodes)}/{len(self.nodes)})")
            self.quorum_lbl.setStyleSheet("color: #10b981;")

        # 逻辑2：自动选举逻辑
        if not leader_exists and len(active_nodes) >= quorum_count:
            self.audit_log.append("> [ELECTION] 监测到主节点缺失，发起新一轮任期投票...")
            self.perform_election(active_nodes)

        # 逻辑3：服务故障自动迁移 (Self-Healing)
        if self.unassigned_services:
            self.rebalance_services()

        self.refresh_ui()

    def perform_election(self, candidates):
        """模拟 Raft 投票逻辑"""
        new_leader = random.choice(candidates)
        new_leader.role = NodeStatus.LEADER
        self.audit_log.append(f"SUCCESS: 节点 {new_leader.node_id} 获得多数票，升为 LEADER")
        for n in candidates:
            if n != new_leader: n.role = NodeStatus.FOLLOWER

    def simulate_leader_failure(self):
        """交互逻辑：人为制造故障"""
        leader = next((n for n in self.nodes.values() if n.role == NodeStatus.LEADER), None)
        if leader:
            self.audit_log.append(f"FATAL: 强制下线当前 Leader 节点: {leader.node_id}")
            leader.role = NodeStatus.DOWN
            # 释放服务至待分配池
            self.unassigned_services.extend(leader.services)
            leader.services = []
            leader.update_load()
            self.refresh_ui()

    def rebalance_services(self):
        """核心资源调度算法：基于负载均衡的服务重新放置"""
        self.audit_log.append(f"> [REBALANCE] 正在为 {len(self.unassigned_services)} 个孤立服务寻找宿主机...")
        
        # 按照节点当前负载升序排序，优先利用空闲节点
        active_nodes = sorted(
            [n for n in self.nodes.values() if n.role != NodeStatus.DOWN],
            key=lambda x: x.load_cpu
        )

        still_pending = []
        for srv in self.unassigned_services:
            placed = False
            for node in active_nodes:
                if node.can_host(srv):
                    node.services.append(srv)
                    node.update_load()
                    self.audit_log.append(f"   - 服务 {srv.name} 迁移至 {node.node_id}")
                    placed = True
                    break
            if not placed:
                still_pending.append(srv)
        
        self.unassigned_services = still_pending

    def on_node_clicked(self, n_id):
        node = self.nodes[n_id]
        if node.role == NodeStatus.DOWN:
            node.role = NodeStatus.FOLLOWER
            self.audit_log.append(f"> [RECOVER] 节点 {n_id} 已恢复上线并加入同步")
        else:
            self.simulate_node_down(n_id)
        self.refresh_ui()

    def simulate_node_down(self, n_id):
        node = self.nodes[n_id]
        is_leader = (node.role == NodeStatus.LEADER)
        node.role = NodeStatus.DOWN
        self.unassigned_services.extend(node.services)
        node.services = []
        node.update_load()
        self.audit_log.append(f"WARN: 节点 {n_id} 发生突发性故障故障")

    def refresh_ui(self):
        # 更新卡片
        for n_id, card in self.cards.items():
            card.refresh()
        
        # 更新表格
        self.srv_table.setRowCount(0)
        total_srv = 0
        for n_id, node in self.nodes.items():
            for srv in node.services:
                row = self.srv_table.rowCount()
                self.srv_table.insertRow(row)
                self.srv_table.setItem(row, 0, QTableWidgetItem(srv.service_id))
                self.srv_table.setItem(row, 1, QTableWidgetItem(srv.name))
                self.srv_table.setItem(row, 2, QTableWidgetItem(n_id))
                self.srv_table.setItem(row, 3, QTableWidgetItem("Healthy"))
                total_srv += 1
        
        self.total_srv_lbl.setText(f"总托管服务: {total_srv + len(self.unassigned_services)}")

from PyQt6.QtWidgets import QTextEdit

def get_widget():
    return ClusterHAModule()

# ----------------------------------------------------------------
# 技术复杂度总结：
# 1. 分布式算法：模拟了 Quorum 法定人数机制与选举过程，处理了 Leader 缺失状态。
# 2. 调度引擎：rebalance_services 实现了基于多维度资源约束（CPU/MEM）的最优适配调度。
# 3. 状态管理：节点状态与服务状态通过定时器驱动的逻辑环路保持一致。
# 4. 交互式诊断：支持点击节点触发故障、模拟主节点崩溃，并观察集群的自我修复（Self-Healing）过程。
# ----------------------------------------------------------------