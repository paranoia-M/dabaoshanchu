from enum import Enum

class DeviceState(Enum):
    IDLE = "空闲"
    RUNNING = "运行中"
    FAULT = "故障"
    MAINTENANCE = "维护中"
    DECOMMISSIONED = "已退役"

class StateTransitionMachine:
    def __init__(self, initial_state):
        self.state = initial_state
        self.allowed = {
            DeviceState.IDLE: [DeviceState.RUNNING, DeviceState.MAINTENANCE],
            DeviceState.RUNNING: [DeviceState.FAULT, DeviceState.MAINTENANCE],
            DeviceState.FAULT: [DeviceState.MAINTENANCE],
            DeviceState.MAINTENANCE: [DeviceState.IDLE, DeviceState.RUNNING]
        }

    def transition(self, new_state):
        if new_state in self.allowed.get(self.state, []):
            self.state = new_state
            return True
        return False