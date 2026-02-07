import hashlib
import datetime

class AuthService:
    def __init__(self):
        # 预设权限池
        self.rbac_table = {
            "SuperUser": ["all_access", "kernel_modify", "audit_export"],
            "Operator": ["monitor_read", "task_create"]
        }
        self._users = {
            "admin": (self._hash("admin123"), "SuperUser"),
            "staff": (self._hash("staff123"), "Operator")
        }

    def _hash(self, pwd):
        # 增加加盐模拟
        return hashlib.sha256(f"IT_PLATFORM_{pwd}".encode()).hexdigest()

    def authenticate(self, user, pwd):
        # 逻辑1：双重一致性校验
        if user in self._users:
            stored_hash, role = self._users[user]
            if stored_hash == self._hash(pwd):
                # 逻辑2：动态分配资源权限掩码
                return {
                    "user": user,
                    "role": role,
                    "permissions": self.rbac_table.get(role, []),
                    "login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        return None