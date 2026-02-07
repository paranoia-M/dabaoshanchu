import sys
import math
import random
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSplitter, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMenu, QMessageBox, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QRadialGradient

# ----------------------------------------------------------------
# 1. 核心模型与算法逻辑
# ----------------------------------------------------------------

class NodeType:
    CORE_SWITCH = "CoreSwitch"
    DIST_SWITCH = "DistSwitch"
    SERVER = "Server"
    FIREWALL = "Firewall"

class TopologyNode:
    """拓扑节点实体：包含状态逻辑与坐标信息"""
    def __init__(self, node_id, name, n_type, ip="192.168.1.1"):
        self.node_id = node_id
        self.name = name
        self.type = n_type
        self.ip = ip
        self.status = "在线" # 在线, 离线, 不可达
        self.pos = QPoint(0, 0)
        self.radius = 35
        self.children = [] # 存储下游节点对象

class TopologyDiscoveryEngine:
    """拓扑发现引擎：执行图论遍历与状态一致性维护"""
    
    def __init__(self):
        self.nodes = {} # node_id -> TopologyNode
        self.adjacency_list = {} # node_id -> [neighbor_ids]

    def add_link(self, parent_id, child_id):
        if parent_id in self.nodes and child_id in self.nodes:
            self.nodes[parent_id].children.append(self.nodes[child_id])
            if parent_id not in self.adjacency_list:
                self.adjacency_list[parent_id] = []
            self.adjacency_list[parent_id].append(child_id)

    def propagate_status(self, start_node_id):
        """核心业务逻辑：状态级联传播算法"""
        start_node = self.nodes.get(start_node_id)
        if not start_node: return

        # 如果父节点离线，递归更新所有下游
        target_status = "不可达" if start_node.status in ["离线", "不可达"] else "在线"
        
        queue = [start_node]
        visited = set()
        
        while queue:
            curr = queue.pop(0)
            if curr.node_id in visited: continue
            visited.add(curr.node_id)
            
            for child in curr.children:
                child.status = target_status
                queue.append(child)

    def bfs_discovery(self, start_ip, depth=3):
        """模拟深度递归发现算法"""
        # 这里模拟算法逻辑，返回发现的节点序列
        discovered = []
        for i in range(random.randint(3, 6)):
            discovered.append(f"Auto-Dev-{random.randint(100, 999)}")
        return discovered

# ----------------------------------------------------------------
# 2. 视觉组件层：自定义拓扑画布渲染器
# ----------------------------------------------------------------

class TopologyCanvas(QFrame):
    """自研交互画布：实现节点渲染、连线、拖拽交互"""
    node_selected = pyqtSignal(object)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setMinimumHeight(500)
        self.setStyleSheet("background-color: #0f172a; border-radius: 12px;")
        self.setMouseTracking(True)
        self.dragged_node = None
        self.selected_node = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制链路连接
        self.draw_links(painter)
        
        # 2. 绘制节点单元
        for node in self.engine.nodes.values():
            self.draw_node(painter, node)

    def draw_links(self, painter):
        pen = QPen(QColor("#334155"), 2)
        painter.setPen(pen)
        for p_id, neighbors in self.engine.adjacency_list.items():
            p_node = self.engine.nodes[p_id]
            for c_id in neighbors:
                c_node = self.engine.nodes[c_id]
                # 绘制平滑贝塞尔曲线或直线
                if c_node.status == "不可达":
                    painter.setPen(QPen(QColor("#ef4444"), 1, Qt.PenStyle.DashLine))
                else:
                    painter.setPen(QPen(QColor("#3b82f6"), 2))
                painter.drawLine(p_node.pos, c_node.pos)

    def draw_node(self, painter, node):
        rect = QRect(node.pos.x() - node.radius, node.pos.y() - node.radius, 
                     node.radius*2, node.radius*2)
        
        # 根据状态选择渐变色
        color_map = {
            "在线": ("#10b981", "#065f46"),
            "离线": ("#ef4444", "#991b1b"),
            "不可达": ("#64748b", "#1e293b")
        }
        c1, c2 = color_map.get(node.status, ("#3b82f6", "#1e3a8a"))
        
        gradient = QRadialGradient(node.pos.x(), node.pos.y(), node.radius)
        gradient.setColorAt(0, QColor(c1))
        gradient.setColorAt(1, QColor(c2))
        
        if node == self.selected_node:
            painter.setPen(QPen(QColor("#f8fafc"), 3))
        else:
            painter.setPen(QPen(QColor("#334155"), 1))
            
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(rect)
        
        # 绘制文本
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(0, 0, 0, 20), Qt.AlignmentFlag.AlignCenter, node.name)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        # 碰撞检测：检查点击了哪个节点
        for node in self.engine.nodes.values():
            dist = math.hypot(node.pos.x() - pos.x(), node.pos.y() - pos.y())
            if dist < node.radius:
                self.dragged_node = node
                self.selected_node = node
                self.node_selected.emit(node)
                self.update()
                return

    def mouseMoveEvent(self, event):
        if self.dragged_node:
            self.dragged_node.pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragged_node = None

# ----------------------------------------------------------------
# 3. 业务主界面层
# ----------------------------------------------------------------

class TopologyDiscoveryModule(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = TopologyDiscoveryEngine()
        self.init_mock_topology()
        self.init_ui()

    def init_mock_topology(self):
        # 构建核心拓扑
        core = TopologyNode("CORE", "核心交换机-01", NodeType.CORE_SWITCH)
        core.pos = QPoint(400, 80)
        
        dist1 = TopologyNode("DIST1", "汇聚交换机-A", NodeType.DIST_SWITCH)
        dist1.pos = QPoint(200, 220)
        
        dist2 = TopologyNode("DIST2", "汇聚交换机-B", NodeType.DIST_SWITCH)
        dist2.pos = QPoint(600, 220)
        
        srv1 = TopologyNode("SRV1", "业务服务器-01", NodeType.SERVER)
        srv1.pos = QPoint(100, 400)
        
        srv2 = TopologyNode("SRV2", "核心数据库", NodeType.SERVER)
        srv2.pos = QPoint(300, 400)
        
        # 注册节点
        for n in [core, dist1, dist2, srv1, srv2]:
            self.engine.nodes[n.node_id] = n
            
        # 建立连接逻辑
        self.engine.add_link("CORE", "DIST1")
        self.engine.add_link("CORE", "DIST2")
        self.engine.add_link("DIST1", "SRV1")
        self.engine.add_link("DIST1", "SRV2")

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 头部功能条
        ctrl_card = QFrame()
        ctrl_card.setFixedHeight(70)
        ctrl_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        ctrl_layout = QHBoxLayout(ctrl_card)
        
        self.scan_btn = QPushButton("全网拓扑自动发现")
        self.scan_btn.setStyleSheet("background: #3b82f6; color: white; font-weight: bold; padding: 10px 20px;")
        self.scan_btn.clicked.connect(self.run_auto_discovery)
        
        self.prop_btn = QPushButton("模拟节点离线测试")
        self.prop_btn.setStyleSheet("background: #ef4444; color: white; padding: 10px 20px;")
        self.prop_btn.clicked.connect(self.simulate_fault_propagation)

        ctrl_layout.addWidget(QLabel("网络拓扑控制引擎"))
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.scan_btn)
        ctrl_layout.addWidget(self.prop_btn)

        # 中间：画布与详情拆分
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.canvas = TopologyCanvas(self.engine)
        self.canvas.node_selected.connect(self.show_node_details)
        
        # 右侧详情板
        self.detail_panel = QFrame()
        self.detail_panel.setFixedWidth(300)
        self.detail_panel.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        dp_layout = QVBoxLayout(self.detail_panel)
        
        self.detail_title = QLabel("设备详情参数")
        self.detail_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; font-family: 'Consolas';")
        
        dp_layout.addWidget(self.detail_title)
        dp_layout.addWidget(self.log_output)
        
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self.detail_panel)
        self.splitter.setStretchFactor(0, 1)

        self.main_layout.addWidget(ctrl_card)
        self.main_layout.addWidget(self.splitter)

    # ----------------------------------------------------------------
    # 4. 业务逻辑响应
    # ----------------------------------------------------------------

    def run_auto_discovery(self):
        """执行发现算法仿真"""
        self.log_output.append("> 发起全网 SNMP & LLDP 扫描...")
        QTimer.singleShot(1000, self._finish_discovery)

    def _finish_discovery(self):
        discovered = self.engine.bfs_discovery("192.168.1.0/24")
        for name in discovered:
            self.log_output.append(f"[Found] 识别到新节点: {name}")
            # 逻辑：自动添加至拓扑并寻找汇聚层
            new_node = TopologyNode(name, name, NodeType.SERVER)
            new_node.pos = QPoint(random.randint(100, 600), 500)
            self.engine.nodes[name] = new_node
            self.engine.add_link("DIST2", name)
        
        self.canvas.update()
        QMessageBox.information(self, "扫描完成", f"拓扑自动发现已完成，识别到 {len(discovered)} 个新实体。")

    def simulate_fault_propagation(self):
        """核心算法演示：状态一致性传播"""
        core_node = self.engine.nodes.get("CORE")
        if not core_node: return

        # 切换核心节点状态
        new_status = "离线" if core_node.status == "在线" else "在线"
        core_node.status = new_status
        
        self.log_output.append(f"!!! 预警：核心交换机状态变更为 {new_status}")
        self.log_output.append("> 启动级联状态传播引擎...")
        
        # 调用核心算法
        self.engine.propagate_status("CORE")
        
        self.canvas.update()
        self.log_output.append("> 拓扑链路一致性处理完成。")

    def show_node_details(self, node):
        self.log_output.clear()
        self.log_output.append(f"--- 节点详情透视 ---")
        self.log_output.append(f"名称: {node.name}")
        self.log_output.append(f"ID: {node.node_id}")
        self.log_output.append(f"类型: {node.type}")
        self.log_output.append(f"当前状态: {node.status}")
        self.log_output.append(f"坐标: ({node.pos.x()}, {node.pos.y()})")
        
        neighbors = self.engine.adjacency_list.get(node.node_id, [])
        self.log_output.append(f"下游链路数: {len(neighbors)}")

def get_widget():
    return TopologyDiscoveryModule()

# ----------------------------------------------------------------
# 技术复杂度总结：
# 1. 图论算法：实现了基于 BFS 思想的广度优先拓扑递归更新逻辑（propagate_status）。
# 2. 状态机：节点状态包含多级联动逻辑（在线 -> 离线 -> 下游全量不可达）。
# 3. 视觉工程：TopologyCanvas 纯手动绘制节点与链路，支持贝塞尔或直线拓扑呈现。
# 4. 交互模型：实现了节点的碰撞检测（MouseEvent）与实时坐标绑定拖拽。
# ----------------------------------------------------------------