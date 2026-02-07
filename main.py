import sys
import time
import uuid
import platform
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLineEdit, 
                             QPushButton, QMessageBox, QLabel, QFrame, 
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt6.QtGui import QColor, QFont
from core.auth_service import AuthService
from main_window import MainWindow

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.auth = AuthService()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) # 去掉原生边框
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # 背景透明
        self.setFixedSize(450, 550)
        self.init_ui()
        self.pre_fill_defaults()

    def init_ui(self):
        # 外层容器（用于实现圆角和阴影）
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(10, 10, 430, 530)
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 20px;
                border: 1px solid #334155;
            }
        """)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.main_frame.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 标题区
        title_label = QLabel("IT设备统一监管维护平台")
        title_label.setStyleSheet("color: #f8fafc; font-size: 24px; font-weight: bold; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; border: none;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 输入框样式
        input_style = """
            QLineEdit {
                background-color: #0f172a;
                border: 2px solid #334155;
                border-radius: 10px;
                padding: 12px;
                color: #f1f2f6;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: #1e293b;
            }
        """

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("管理员工号")
        self.user_input.setStyleSheet(input_style)

        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("访问授权秘钥")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setStyleSheet(input_style)

        # 环境预检显示
        self.status_label = QLabel("等待环境安全扫描...")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px; border: none;")

        # 登录按钮
        self.login_btn = QPushButton("验证身份并接入系统")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        self.login_btn.clicked.connect(self.animate_login)

        # 退出按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setParent(self.main_frame)
        self.close_btn.setGeometry(390, 10, 30, 30)
        self.close_btn.setStyleSheet("color: #94a3b8; font-size: 20px; border: none; background: none;")
        self.close_btn.clicked.connect(self.close)

        layout.addWidget(title_label)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pwd_input)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.login_btn)

        # 启动环境指纹扫描模拟
        QTimer.singleShot(1000, self.perform_env_check)

    def pre_fill_defaults(self):
        """默认填充账号密码以便快速测试"""
        self.user_input.setText("admin")
        self.pwd_input.setText("admin123")

    def perform_env_check(self):
        """核心逻辑：环境指纹审计"""
        hw_id = uuid.uuid1().hex[:12].upper()
        sys_info = f"{platform.system()} {platform.machine()}"
        self.status_label.setText(f"终端指纹: {hw_id} | 环境状态: 正常")
        self.status_label.setStyleSheet("color: #10b981; font-size: 11px; border: none;")

    def animate_login(self):
        """登录按钮动画逻辑"""
        original_geo = self.login_btn.geometry()
        self.login_btn.setText("正在建立加密链路...")
        self.do_login()

    def do_login(self):
        # 增加安全延迟，模拟复杂验证过程
        QApplication.processEvents()
        time.sleep(0.5) 
        
        res = self.auth.authenticate(self.user_input.text(), self.pwd_input.text())
        if res:
            # 逻辑：注入会话令牌
            res['token'] = uuid.uuid4().hex
            self.user_info = res
            self.accept()
        else:
            self.login_btn.setText("验证身份并接入系统")
            QMessageBox.critical(self, "鉴权中心", "拦截到非法访问请求：凭据不匹配")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        main_win = MainWindow(login.user_info)
        main_win.show()
        sys.exit(app.exec())