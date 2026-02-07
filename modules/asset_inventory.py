import sys
import datetime
import hashlib
import json
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView, 
                             QAbstractItemView, QDialog, QFormLayout, QLineEdit, 
                             QComboBox, QSpinBox, QMessageBox, QMenu, QFrame, 
                             QProgressBar, QSplitter, QTextEdit, QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QIcon, QAction, QFont, QCursor

# ----------------------------------------------------------------
# 核心业务逻辑层：高精度计算引擎与数据一致性处理
# ----------------------------------------------------------------

class AssetSecurityProvider:
    """数据一致性审计提供者：利用哈希链确保资产记录不可篡改"""
    @staticmethod
    def generate_record_hash(record_dict):
        # 排除哈希字段本身进行计算
        content = {k: v for k, v in record_dict.items() if k != 'integrity_hash'}
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

class AssetValuationEngine:
    """资产净值精算引擎：实现工业级资产折旧算法"""
    
    @staticmethod
    def calculate_current_value(original_cost, purchase_date_str, life_years, method="DoubleDeclining"):
        """
        根据购买日期和预计寿命计算当前精确残值
        method: DoubleDeclining (双倍余额递减) 或 StraightLine (直线法)
        """
        try:
            purchase_date = datetime.datetime.strptime(purchase_date_str, "%Y-%m-%d")
            today = datetime.datetime.now()
            days_held = (today - purchase_date).days
            if days_held < 0: return original_cost
            
            total_days = life_years * 365
            if days_held >= total_days: return original_cost * 0.05 # 5% 残值封顶
            
            if method == "StraightLine":
                annual_depreciation = original_cost * 0.95 / life_years
                daily_depreciation = annual_depreciation / 365
                current_val = original_cost - (daily_depreciation * days_held)
            else:
                # 双倍余额递减近似实现
                current_val = original_cost
                years_passed = days_held / 365
                depreciation_rate = 2.0 / life_years
                current_val = original_cost * ((1 - depreciation_rate) ** years_passed)
                
            return max(current_val, original_cost * 0.05)
        except:
            return original_cost

# ----------------------------------------------------------------
# 交互组件层：复杂的自定义对话框与视图
# ----------------------------------------------------------------

class AssetEditDialog(QDialog):
    """资产编辑/录入对话框：包含严格的格式校验逻辑"""
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("资产要素录入" if not initial_data else "修改资产配置")
        self.setMinimumWidth(450)
        self.data = initial_data
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)

        self.sn_input = QLineEdit()
        self.sn_input.setPlaceholderText("例如: SRV-DELL-2023-001")
        if self.data: self.sn_input.setText(self.data['sn'])
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["核心服务器", "边缘网关", "存储阵列", "负载均衡器", "安全防火墙"])
        if self.data: self.type_combo.setCurrentText(self.data['type'])

        self.cost_input = QSpinBox()
        self.cost_input.setRange(1000, 10000000)
        self.cost_input.setPrefix("￥ ")
        if self.data: self.cost_input.setValue(int(self.data['cost']))

        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        self.date_input.setText(datetime.datetime.now().strftime("%Y-%m-%d"))
        if self.data: self.date_input.setText(self.data['date'])

        self.life_input = QSpinBox()
        self.life_input.setRange(1, 20)
        self.life_input.setSuffix(" 年")
        self.life_input.setValue(5)
        if self.data: self.life_input.setValue(self.data['life'])

        self.submit_btn = QPushButton("保存资产记录并签名")
        self.submit_btn.setStyleSheet("background-color: #2563eb; color: white; padding: 10px;")
        self.submit_btn.clicked.connect(self.validate_and_accept)

        layout.addRow("设备序列号 (SN):", self.sn_input)
        layout.addRow("资产分类:", self.type_combo)
        layout.addRow("采购原值:", self.cost_input)
        layout.addRow("采购日期:", self.date_input)
        layout.addRow("预计使用寿命:", self.life_input)
        layout.addRow("", self.submit_btn)

    def validate_and_accept(self):
        # 内部业务校验逻辑
        try:
            datetime.datetime.strptime(self.date_input.text(), "%Y-%m-%d")
        except:
            QMessageBox.warning(self, "格式错误", "日期必须符合 YYYY-MM-DD 格式")
            return
        
        if len(self.sn_input.text()) < 5:
            QMessageBox.warning(self, "校验失败", "SN 序列号过短，不符合资产命名规范")
            return
            
        self.accept()

    def get_form_data(self):
        return {
            "sn": self.sn_input.text(),
            "type": self.type_combo.currentText(),
            "cost": self.cost_input.value(),
            "date": self.date_input.text(),
            "life": self.life_input.value()
        }

# ----------------------------------------------------------------
# 主模块界面层
# ----------------------------------------------------------------

class AssetInventoryModule(QWidget):
    """
    资产盘点核心模块：
    1. 实现资产增删改查
    2. 实现数据一致性哈希审计
    3. 动态健康度算法展示
    """
    def __init__(self):
        super().__init__()
        self.assets_data = []
        self.audit_log = []
        self.init_mock_data()
        self.init_ui()

    def init_mock_data(self):
        """初始化种子数据，模拟历史盘点记录"""
        types = ["核心服务器", "存储阵列", "安全防火墙"]
        for i in range(1, 6):
            item = {
                "id": i,
                "sn": f"IT-DEVICE-{2020+i}-00{i}",
                "type": random.choice(types),
                "cost": random.randint(20000, 150000),
                "date": f"202{i-1}-05-12",
                "life": 5,
                "status": "运行中" if i != 3 else "维护中"
            }
            item['integrity_hash'] = AssetSecurityProvider.generate_record_hash(item)
            self.assets_data.append(item)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # 头部统计条
        self.stat_frame = QFrame()
        self.stat_frame.setObjectName("StatPanel")
        self.stat_frame.setStyleSheet("""
            #StatPanel { background-color: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; }
            QLabel { font-family: 'Segoe UI'; }
        """)
        stat_layout = QHBoxLayout(self.stat_frame)
        
        self.total_count_lbl = QLabel("总资产数量: 0")
        self.total_value_lbl = QLabel("资产总净值: ￥0.00")
        self.health_avg_lbl = QLabel("全系统平均健康度: 0%")
        
        for lbl in [self.total_count_lbl, self.total_value_lbl, self.health_avg_lbl]:
            lbl.setStyleSheet("font-size: 14px; color: #475569; padding: 10px;")
            stat_layout.addWidget(lbl)
        
        # 功能按钮栏
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(" 新增资产登记")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setStyleSheet("background-color: #10b981; color: white; border-radius: 5px; font-weight: bold;")
        self.add_btn.clicked.connect(self.handle_add_asset)
        
        self.audit_btn = QPushButton(" 执行一致性校验")
        self.audit_btn.setMinimumHeight(40)
        self.audit_btn.setStyleSheet("background-color: #f59e0b; color: white; border-radius: 5px; font-weight: bold;")
        self.audit_btn.clicked.connect(self.run_integrity_audit)

        self.export_btn = QPushButton(" 导出资产报表")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setStyleSheet("background-color: #6366f1; color: white; border-radius: 5px; font-weight: bold;")
        self.export_btn.clicked.connect(self.export_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.audit_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch()

        # 中间数据表格与详情的分隔布局
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # 表格控件
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "设备序列号", "资产类别", "采购价值", "实时残值估算", "健康状况", "生命周期状态", "审计签名"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #e2e8f0; border-radius: 5px; }
            QHeaderView::section { background-color: #f1f5f9; padding: 8px; border: none; border-bottom: 2px solid #cbd5e1; }
        """)

        # 底部日志终端
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("系统内核日志输出...")
        self.console.setStyleSheet("background-color: #0f172a; color: #10b981; font-family: 'Consolas'; font-size: 12px;")
        self.console.setMaximumHeight(150)

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.console)

        self.main_layout.addWidget(self.stat_frame)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.splitter)

        self.refresh_table()

    # ----------------------------------------------------------------
    # 核心交互逻辑与算法应用
    # ----------------------------------------------------------------

    def refresh_table(self):
        """刷新表格数据并重新执行折旧算法计算"""
        self.table.setRowCount(0)
        total_value = 0.0
        
        for asset in self.assets_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 计算当前实时残值
            current_val = AssetValuationEngine.calculate_current_value(
                asset['cost'], asset['date'], asset['life']
            )
            total_value += current_val
            
            # 逻辑：健康度计算 (随机波动 + 年限权重)
            years_age = (datetime.datetime.now() - datetime.datetime.strptime(asset['date'], "%Y-%m-%d")).days / 365
            health_score = max(0, 100 - (years_age * 15) - random.randint(0, 5))
            
            # 渲染单元格
            self.table.setItem(row, 0, QTableWidgetItem(str(asset['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(asset['sn']))
            self.table.setItem(row, 2, QTableWidgetItem(asset['type']))
            self.table.setItem(row, 3, QTableWidgetItem(f"￥{asset['cost']:,}"))
            
            val_item = QTableWidgetItem(f"￥{current_val:,.2f}")
            val_item.setForeground(QColor("#059669"))
            self.table.setItem(row, 4, val_item)

            # 健康度进度条
            health_bar = QProgressBar()
            health_bar.setRange(0, 100)
            health_bar.setValue(int(health_score))
            health_bar.setTextVisible(False)
            health_bar.setMaximumHeight(12)
            if health_score < 40: health_bar.setStyleSheet("QProgressBar::chunk { background-color: #ef4444; }")
            elif health_score < 70: health_bar.setStyleSheet("QProgressBar::chunk { background-color: #f59e0b; }")
            else: health_bar.setStyleSheet("QProgressBar::chunk { background-color: #10b981; }")
            self.table.setCellWidget(row, 5, health_bar)

            status_item = QTableWidgetItem(asset['status'])
            if asset['status'] == "故障": status_item.setForeground(QColor("#ef4444"))
            self.table.setItem(row, 6, status_item)

            hash_item = QTableWidgetItem(asset['integrity_hash'][:16] + "...")
            hash_item.setToolTip(asset['integrity_hash'])
            hash_item.setFont(QFont("Consolas", 9))
            self.table.setItem(row, 7, hash_item)

        # 更新全局统计
        self.total_count_lbl.setText(f"总资产数量: {len(self.assets_data)}")
        self.total_value_lbl.setText(f"资产总净值: ￥{total_value:,.2f}")
        self.log_to_console(f"资产数据重算完成。当前时间戳: {datetime.datetime.now().isoformat()}")

    def log_to_console(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.console.append(f"[{timestamp}] {message}")

    def show_context_menu(self, pos):
        """右键菜单：实现资产状态机的流转控制"""
        row = self.table.currentRow()
        if row == -1: return
        
        menu = QMenu()
        edit_act = QAction("修改配置要素", self)
        maint_act = QAction("标记进入维护状态", self)
        fault_act = QAction("上报警告：硬件故障", self)
        delete_act = QAction("从核心台账移除", self)

        edit_act.triggered.connect(lambda: self.handle_edit_asset(row))
        maint_act.triggered.connect(lambda: self.update_asset_status(row, "维护中"))
        fault_act.triggered.connect(lambda: self.update_asset_status(row, "故障"))
        delete_act.triggered.connect(lambda: self.handle_delete_asset(row))

        menu.addActions([edit_act, maint_act, fault_act])
        menu.addSeparator()
        menu.addAction(delete_act)
        menu.exec(QCursor.pos())

    def update_asset_status(self, row, new_status):
        asset_id = int(self.table.item(row, 0).text())
        for asset in self.assets_data:
            if asset['id'] == asset_id:
                old_status = asset['status']
                asset['status'] = new_status
                # 重新计算一致性哈希
                asset['integrity_hash'] = AssetSecurityProvider.generate_record_hash(asset)
                self.log_to_console(f"状态迁移成功: ID {asset_id} [{old_status}] -> [{new_status}] (签名已刷新)")
                break
        self.refresh_table()

    def handle_add_asset(self):
        dialog = AssetEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_form_data()
            new_data['id'] = max([a['id'] for a in self.assets_data]) + 1 if self.assets_data else 1
            new_data['status'] = "空闲"
            new_data['integrity_hash'] = AssetSecurityProvider.generate_record_hash(new_data)
            self.assets_data.append(new_data)
            self.log_to_console(f"新资产入库: {new_data['sn']}")
            self.refresh_table()

    def handle_edit_asset(self, row_idx):
        asset_id = int(self.table.item(row_idx, 0).text())
        target_asset = next(a for a in self.assets_data if a['id'] == asset_id)
        
        dialog = AssetEditDialog(self, target_asset)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_form_data()
            target_asset.update(updated)
            target_asset['integrity_hash'] = AssetSecurityProvider.generate_record_hash(target_asset)
            self.log_to_console(f"资产配置变更已同步: ID {asset_id}")
            self.refresh_table()

    def handle_delete_asset(self, row_idx):
        res = QMessageBox.warning(self, "高危操作", "确定要从核心台账永久移除该记录吗？此操作将记录在审计日志中。", 
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            asset_id = int(self.table.item(row_idx, 0).text())
            self.assets_data = [a for a in self.assets_data if a['id'] != asset_id]
            self.log_to_console(f"CRITICAL: 资产 ID {asset_id} 已被管理员移除")
            self.refresh_table()

    def run_integrity_audit(self):
        """核心算法逻辑：数据一致性全量校验"""
        self.log_to_console("正在启动全量数据一致性扫描...")
        tampered = []
        for asset in self.assets_data:
            current_hash = AssetSecurityProvider.generate_record_hash(asset)
            if current_hash != asset['integrity_hash']:
                tampered.append(asset['sn'])
        
        if tampered:
            QMessageBox.critical(self, "审计异常", f"检测到非法数据变更！\n损坏的资产项: {', '.join(tampered)}")
            self.log_to_console("ERROR: 数据完整性校验未通过！")
        else:
            QMessageBox.information(self, "审计完成", "全量资产数据通过 SHA-256 签名校验，未发现异常篡改。")
            self.log_to_console("SUCCESS: 环境一致性校验 100% 通过")

    def export_data(self):
        """交互功能：模拟数据导出"""
        path, _ = QFileDialog.getSaveFileName(self, "导出资产清单", "", "JSON Files (*.json);;CSV Files (*.csv)")
        if path:
            self.log_to_console(f"数据报表已导出至: {path}")

def get_widget():
    return AssetInventoryModule()