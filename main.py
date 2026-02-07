import sys
import time
import uuid
import platform
import os
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLineEdit, 
                             QPushButton, QMessageBox, QLabel, QFrame, 
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from core.auth_service import AuthService
from main_window import MainWindow

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.auth = AuthService()
        # 修复：在Windows打包环境下，去掉透明背景属性，防止黑色块出现
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) 
        self.setFixedSize(450, 550)
        
        # 修复：显式设置对话框背景色
        self.setStyleSheet("background-color: #0f172a;") 
        self.init_ui()
        self.pre_fill_defaults()

    def init_ui(self):
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 450, 550)
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 0px;
                border: 1px solid #334155;
            }
        """)
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title_label = QLabel("IT设备统一监管维护平台")
        title_label.setStyleSheet("color: #f8fafc; font-size: 24px; font-weight: bold; border: none; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Unified Supervision & Maintenance")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; border: none; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        input_style = """
            QLineEdit {
                background-color: #0f172a;
                border: 2px solid #334155;
                border-radius: 10px;
                padding: 12px;
                color: #f1f2f6;
                font-size: 14px;
            }
        """

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("管理员工号")
        self.user_input.setStyleSheet(input_style)

        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("访问授权秘钥")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setStyleSheet(input_style)

        self.status_label = QLabel("等待环境安全扫描...")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px; border: none; background: transparent;")

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
            QPushButton:hover { background-color: #3b82f6; }
        """)
        self.login_btn.clicked.connect(self.do_login)

        layout.addWidget(title_label)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pwd_input)
        layout.addWidget(self.status_label)