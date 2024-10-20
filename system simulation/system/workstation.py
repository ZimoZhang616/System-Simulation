import job
from machine import *

# 工作站类，表示一个生产线上的工作站
class WorkStation:
    def __init__(self, station_id):
        """
        初始化工作站
        :param station_id: 工作站的ID
        :param num_machines: 该工作站的机器数量
        """
        self.station_id = station_id
        self.input_queue = []  # 该工作站的等待队列
        self.output_queue = []  # 该工作站的等待队列
        
    def set_machines(self, machines):
        self.num_machines = len(machines)
        self.machines = machines

    def is_machine_available(self):
        """
        判断是否有空闲的机器
        :return: 布尔值，表示是否有空闲的机器
        """
        return any(not machine.status == machine_Status.Running for machine in self.machines)
    
    def add_job_to_input_queue(self, job):
        """
        将作业添加到等待队列
        :param job: 需要处理的作业
        """
        self.input_queue.append(job)
    
    
    def update_workstation(self):
        # workstation主要做的事情，就是分配任务给machine
        # 1. 找到空闲的机器
        # 2. 用一定的策略去给每一个机器一个job
        # 3. job给到这个机器去

        idle_machine_list = []
        for idx, machine in enumerate(self.machines):
            if machine.status == machine_Status.Idle:
                idle_machine_list.append(idx)

        for i in idle_machine_list:
            #choosed_job = System_Policy.policy_machine()
            if len(self.input_queue) != 0:
                choosed_job = self.input_queue.pop(0)
                self.machines[i].set_job(choosed_job) # 先进先出
        
        print(f'update_workstation: {self.station_id}, workstation_input_queue: {self.input_queue}, workstation_output_queue: {self.output_queue}')


