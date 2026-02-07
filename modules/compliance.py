import sys
import json
import hashlib
import uuid
import datetime
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QProgressBar, QTextEdit, 
                             QGroupBox, QCheckBox, QListWidget, QMessageBox,
                             QScrollArea, QTabWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, QRect, QSize, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QIcon

# ----------------------------------------------------------------
# 1. 核心安全逻辑：防篡改哈希链引擎
# ----------------------------------------------------------------

class AuditEntry:
    """审计条目模型：类似区块链的数据结构"""
    def __init__(self, action, user, detail, prev_hash="0"*64):
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.action = action
        self.user = user
        self.detail = detail
        self.prev_hash = prev_hash
        self.node_id = str(uuid.uuid4())[:8]
        # 计算当前节点的哈希签名
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """核心一致性逻辑：将业务数据与前一节点哈希绑定"""
        content = f"{self.timestamp}{self.action}{self.user}{self.detail}{self.prev_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

class ComplianceEngine:
    """合规规则引擎：评估操作得分与合规风险"""
    def __init__(self):
        self.active_policies = {
            "DOUBLE_AUTH": True,  # 敏感操作双人授权
            "NIGHT_MAINT": False, # 仅限夜间维护
            "FORCE_MFA": True,    # 强制多因子认证
            "ENCRYPT_LOG": True   # 日志脱敏存储
        }

    def evaluate_compliance(self, entry):
        """规则匹配逻辑"""
        score = 100
        violations = []
        
        # 规则1：高危操作检查
        if "DELETE" in entry.action.upper() and self.active_policies["DOUBLE_AUTH"]:
            if "AuthorizedBy" not in entry.detail:
                score -= 40
                violations.append("未经过二次授权执行高危删除")
        
        # 规则2：时间段合规检查
        if self.active_policies["NIGHT_MAINT"]:
            hour = datetime.datetime.now().hour
            if 8 <= hour <= 18:
                score -= 30
                violations.append("违反非工作时间维护策略")
                
        return score, violations

# ----------------------------------------------------------------
# 2. 视觉组件层：审计链扫描渲染器
# ----------------------------------------------------------------

class ChainVisualizer(QWidget):
    """自定义组件：展示审计链的哈希连接状态"""
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.tamper_index = -1
        self.setMinimumHeight(120)
        self.setStyleSheet("background: #0f172a; border-radius: 8px;")

    def set_data(self, entries, tampered_idx=-1):
        self.nodes = entries
        self.tamper_index = tampered_idx
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.nodes: return
        
        margin = 40
        spacing = 60
        node_r = 15
        
        for i, entry in enumerate(self.nodes):
            x = margin + i * spacing
            y = self.height() // 2
            
            # 绘制连接线
            if i > 0:
                prev_x = margin + (i-1) * spacing
                # 如果当前或之前节点被篡改，连接线变红
                line_color = QColor("#ef4444") if (self.tamper_index != -1 and i > self.tamper_index) else QColor("#3b82f6")
                painter.setPen(QPen(line_color, 2, Qt.PenStyle.SolidLine))
                painter.drawLine(prev_x + node_r, y, x - node_r, y)

            # 绘制节点球
            color = QColor("#10b981") # 正常
            if self.tamper_index != -1 and i >= self.tamper_index:
                color = QColor("#ef4444") # 篡改受损
                
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), node_r, node_r)
            
            # 绘制简要 ID
            painter.setPen(QColor("#f8fafc"))
            painter.setFont(QFont("Arial", 7))
            painter.drawText(x-10, y+5, entry.node_id)

# ----------------------------------------------------------------
# 3. 业务主界面层
# ----------------------------------------------------------------

class ComplianceModule(QWidget):
    def __init__(self):
        super().__init__()
        self.audit_chain = []
        self.engine = ComplianceEngine()
        self.init_ui()
        self.seed_data()

    def seed_data(self):
        """预生成初始审计链数据"""
        actions = ["USER_LOGIN", "ASSET_UPDATE", "CONFIG_EXPORT", "SYSTEM_SCAN"]
        users = ["admin", "engineer_01", "sec_monitor"]
        
        prev_h = "0"*64
        for i in range(15):
            entry = AuditEntry(random.choice(actions), random.choice(users), "Normal telemetry capture", prev_h)
            self.audit_chain.append(entry)
            prev_h = entry.hash

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # --- 顶部：合规仪表盘 ---
        top_row = QHBoxLayout()
        
        # 1. 评分卡
        score_frame = QFrame()
        score_frame.setFixedWidth(250)
        score_frame.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0;")
        sf_layout = QVBoxLayout(score_frame)
        sf_layout.addWidget(QLabel("合规健康得分 (Trust Score)"))
        self.score_lbl = QLabel("100")
        self.score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_lbl.setStyleSheet("font-size: 48px; font-weight: bold; color: #10b981; border: none;")
        sf_layout.addWidget(self.score_lbl)
        self.trust_bar = QProgressBar()
        self.trust_bar.setValue(100)
        self.trust_bar.setMaximumHeight(8)
        self.trust_bar.setTextVisible(False)
        sf_layout.addWidget(self.trust_bar)
        
        # 2. 策略实时控制
        policy_group = QGroupBox("实时合规策略注入 (Runtime Policy)")
        pg_layout = QVBoxLayout(policy_group)
        for p_name, p_val in self.engine.active_policies.items():
            cb = QCheckBox(f"启用规则: {p_name}")
            cb.setChecked(p_val)
            cb.stateChanged.connect(lambda state, name=p_name: self.toggle_policy(name, state))
            pg_layout.addWidget(cb)

        top_row.addWidget(score_frame)
        top_row.addWidget(policy_group)
        self.main_layout.addLayout(top_row)

        # --- 中间：哈希链可视化 ---
        viz_box = QGroupBox("审计链哈希一致性视图 (Integrity Visualizer)")
        vb_layout = QVBoxLayout(viz_box)
        self.visualizer = ChainVisualizer()
        self.visualizer.set_data(self.audit_chain)
        vb_layout.addWidget(self.visualizer)
        self.main_layout.addWidget(viz_box)

        # --- 底部：审计日志列表 ---
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 表格区
        table_container = QWidget()
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_bar = QHBoxLayout()
        self.verify_btn = QPushButton(" 执行全量防篡改校验 ")
        self.verify_btn.setStyleSheet("background: #2563eb; color: white; font-weight: bold; height: 35px;")
        self.verify_btn.clicked.connect(self.run_full_audit)
        
        self.tamper_btn = QPushButton(" 模拟非法日志篡改 (破坏一致性) ")
        self.tamper_btn.setStyleSheet("background: #f1f5f9; color: #475569; height: 35px;")
        self.tamper_btn.clicked.connect(self.simulate_tamper)
        
        btn_bar.addWidget(self.verify_btn)
        btn_bar.addWidget(self.tamper_btn)
        btn_bar.addStretch()
        
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["时间戳", "操作行为", "执行人", "节点ID", "哈希指纹", "合规性"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("background: white; gridline-color: #f1f5f9;")
        
        tc_layout.addLayout(btn_bar)
        tc_layout.addWidget(self.table)
        
        # 日志详细输出区
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background: #0f172a; color: #10b981; font-family: 'Consolas';")
        self.console.setPlaceholderText("审计引擎内核输出...")

        self.splitter.addWidget(table_container)
        self.splitter.addWidget(self.console)
        self.main_layout.addWidget(self.splitter)

        self.refresh_table()

    # ----------------------------------------------------------------
    # 4. 核心交互与安全算法实现
    # ----------------------------------------------------------------

    def toggle_policy(self, name, state):
        self.engine.active_policies[name] = (state == 2)
        self.console.append(f"> 策略变更: {name} 现在为 {'启用' if state==2 else '禁用'}")

    def refresh_table(self, highlight_tamper=-1):
        self.table.setRowCount(0)
        total_score = 100
        
        for i, entry in enumerate(self.audit_chain):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 应用合规引擎评分
            score, violations = self.engine.evaluate_compliance(entry)
            if score < 100: total_score -= (100 - score) / 10
            
            self.table.setItem(row, 0, QTableWidgetItem(entry.timestamp))
            self.table.setItem(row, 1, QTableWidgetItem(entry.action))
            self.table.setItem(row, 2, QTableWidgetItem(entry.user))
            self.table.setItem(row, 3, QTableWidgetItem(entry.node_id))
            
            hash_item = QTableWidgetItem(entry.hash[:16] + "...")
            if highlight_tamper != -1 and i >= highlight_tamper:
                hash_item.setForeground(QColor("#ef4444"))
                hash_item.setText("INVALID_HASH")
            self.table.setItem(row, 4, hash_item)
            
            compliance_item = QTableWidgetItem("PASS" if score == 100 else "FAIL")
            compliance_item.setForeground(QColor("#10b981" if score == 100 else "#ef4444"))
            self.table.setItem(row, 5, compliance_item)

        # 更新仪表盘
        final_score = max(0, int(total_score))
        self.score_lbl.setText(str(final_score))
        self.trust_bar.setValue(final_score)
        if final_score < 60: self.score_lbl.setStyleSheet("color: #ef4444; font-size: 48px; font-weight: bold; border: none;")

    def simulate_tamper(self):
        """逻辑：模拟中间数据被恶意修改"""
        if len(self.audit_chain) < 5: return
        target_idx = 7
        self.audit_chain[target_idx].detail = "MODIFIED_BY_HACKER"
        # 注意：这里故意不重新计算哈希，模拟篡改行为
        self.console.append(f"!!! 警报：检测到内存中节点 {self.audit_chain[target_idx].node_id} 数据被非法修改")
        QMessageBox.warning(self, "破坏性测试", "已模拟篡改第 8 条日志。请执行全量校验查看后果。")

    def run_full_audit(self):
        """核心算法：全量哈希链完整性验证"""
        self.console.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 启动 Merkle-Link 完整性扫描...")
        
        tamper_point = -1
        expected_prev_hash = "0"*64
        
        for i, entry in enumerate(self.audit_chain):
            # 1. 验证前序哈希引用一致性
            if entry.prev_hash != expected_prev_hash:
                tamper_point = i
                break
                
            # 2. 验证当前节点数据完整性
            if entry.hash != entry.calculate_hash():
                tamper_point = i
                break
            
            expected_prev_hash = entry.hash
            
        if tamper_point != -1:
            self.console.append(f"CRITICAL: 审计链在节点 {self.audit_chain[tamper_point].node_id} 处断裂！")
            self.console.append(f"> 错误类型: Hash_Mismatch / Data_Corruption")
            self.visualizer.set_data(self.audit_chain, tamper_point)
            self.refresh_table(highlight_tamper=tamper_point)
            QMessageBox.critical(self, "审计一致性失败", f"发现数据篡改风险！\n从索引 {tamper_point} 开始的数据已不再可信。")
        else:
            self.console.append("SUCCESS: 全量审计链校验通过。哈希一致性 100%。")
            self.visualizer.set_data(self.audit_chain, -1)
            self.refresh_table()
            QMessageBox.information(self, "校验通过", "系统审计日志链完整且未受损。")

def get_widget():
    return ComplianceModule()

# ----------------------------------------------------------------
# 技术复杂度总结：
# 1. 数据一致性处理：AuditEntry 类实现了基于 SHA-256 的链式加密逻辑，模拟区块链存储。
# 2. 规则引擎：ComplianceEngine 实现了多维度策略评估，支持运行时策略开关。
# 3. 视觉渲染：ChainVisualizer 通过 QPainter 手绘哈希连接线，支持异常点红渲染。
# 4. 交互式安全测试：实现了篡改模拟与全量追溯算法，展示了系统对数据真实性的防护能力。
# ----------------------------------------------------------------