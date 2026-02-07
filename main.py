import sys
import os
import traceback
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLineEdit, 
                             QPushButton, QMessageBox, QLabel, QFrame)
from PyQt6.QtCore import Qt
from core.auth_service import AuthService
from main_window import MainWindow

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.auth = AuthService()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) 
        self.setFixedSize(450, 550)
        # 显式设置背景色，防止Windows打包黑屏
        self.setStyleSheet("background-color: #0f172a;") 
        self.init_ui()

    def init_ui(self):
        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(0, 0, 450, 550)
        self.main_frame.setStyleSheet("""
            QFrame { background-color: #1e293b; border: 1px solid #334155; }
            QLabel { background: transparent; }
        """)
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title_label = QLabel("IT设备统一监管维护平台")
        title_label.setStyleSheet("color: #f8fafc; font-size: 24px; font-weight: bold; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.user_input = QLineEdit(placeholderText="管理员工号")
        self.user_input.setText("admin")
        self.user_input.setStyleSheet("background-color: #0f172a; border: 2px solid #334155; border-radius: 10px; padding: 12px; color: #f1f2f6;")

        self.pwd_input = QLineEdit(placeholderText="访问授权秘钥")
        self.pwd_input.setText("admin123")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setStyleSheet("background-color: #0f172a; border: 2px solid #334155; border-radius: 10px; padding: 12px; color: #f1f2f6;")

        self.login_btn = QPushButton("验证身份并接入系统")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("background-color: #2563eb; color: white; border-radius: 10px; padding: 15px; font-size: 16px; font-weight: bold;")
        self.login_btn.clicked.connect(self.do_login)

        layout.addWidget(title_label)
        layout.addSpacing(40)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pwd_input)
        layout.addStretch()
        layout.addWidget(self.login_btn)

    def do_login(self):
        res = self.auth.authenticate(self.user_input.text(), self.pwd_input.text())
        if res:
            self.user_info = res
            self.accept()
        else:
            QMessageBox.critical(self, "鉴权中心", "拦截到非法访问请求：凭据不匹配")

if __name__ == "__main__":
    # 增加异常捕获，确保终端能看到错误
    try:
        app = QApplication(sys.argv)
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted:
            window = MainWindow(login.user_info)
            window.show()
            sys.exit(app.exec())
    except Exception:
        traceback.print_exc()