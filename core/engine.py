import time
from enum import Enum
from threading import Lock

class DeviceState(Enum):
    IDLE = "空闲"
    RUNNING = "运行中"
    FAULT = "故障"
    MAINTENANCE = "维护中"
    DECOMMISSIONED = "已退役"

class BusinessRuleEngine:
    """业务规则引擎：处理资产折旧、风险评估等逻辑"""
    def __init__(self):
        self.rules = []

    def add_rule(self, func):
        self.rules.append(func)

    def evaluate(self, data):
        results = []
        for rule in self.rules:
            results.append(rule(data))
        return results

class StateTransitionMachine:
    """状态流转逻辑：严格控制IT设备生命周期"""
    def __init__(self, initial_state):
        self.state = initial_state
        self._lock = Lock()
        # 定义合法转换
        self.allowed_transitions = {
            DeviceState.IDLE: [DeviceState.RUNNING, DeviceState.MAINTENANCE],
            DeviceState.RUNNING: [DeviceState.FAULT, DeviceState.MAINTENANCE],
            DeviceState.FAULT: [DeviceState.MAINTENANCE],
            DeviceState.MAINTENANCE: [DeviceState.IDLE, DeviceState.RUNNING]
        }

    def transition_to(self, new_state):
        with self._lock:
            if new_state in self.allowed_transitions.get(self.state, []):
                old_state = self.state
                self.state = new_state
                return True, f"Transitioned from {old_state} to {new_state}"
            return False, f"Illegal transition from {self.state} to {new_state}"