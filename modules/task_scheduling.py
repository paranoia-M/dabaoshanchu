from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit

class TaskSchedulingModule(QWidget):
    """维护任务调度：基于加权优先级的资源分配算法"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def schedule_algorithm(self, tasks, engineers):
        """核心逻辑：贪心算法匹配最优维护工程师"""
        # 逻辑实现：根据工程师技能匹配度和当前负载调度
        sorted_engineers = sorted(engineers, key=lambda x: x['workload'])
        assignments = {}
        for task in tasks:
            assigned = sorted_engineers.pop(0)
            assignments[task['id']] = assigned['name']
            assigned['workload'] += 1
            sorted_engineers.append(assigned)
            sorted_engineers.sort(key=lambda x: x['workload'])
        return assignments

    def init_ui(self):
        layout = QVBoxLayout()
        self.log_area = QTextEdit()
        btn = QPushButton("执行智能调度算法")
        btn.clicked.connect(self.run_scheduling)
        
        layout.addWidget(btn)
        layout.addWidget(self.log_area)
        self.setLayout(layout)

    def run_scheduling(self):
        tasks = [{'id': f'T{i}'} for i in range(5)]
        engineers = [{'name': '张工', 'workload': 2}, {'name': '李工', 'workload': 0}]
        result = self.schedule_algorithm(tasks, engineers)
        self.log_area.append(f"分配结果: {str(result)}")

def get_widget():
    return TaskSchedulingModule()