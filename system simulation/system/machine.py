import enum
import System_Policy
from job import *
import workstation

class machine_Status(enum.Enum):
    Idle = 1
    Running = 2
    

class Machine:
    def __init__(self, index, workstation):
        """
        初始化 Machine 类
        :param index: 机器的索引
        :param workstation_index: 机器所属工作站的索引
        """
        self.index = index  # 机器索引
        #self.workstation_index = workstation_index  # 工作站索引
        self.workstation = workstation
        self.status = machine_Status.Idle  # 机器的状态，默认为空闲状态
        self.total_running_time = 0  # 机器总运行时间
        self.total_idle_time = 0  # 机器总空闲时间
    
        self.processing_countdown = 0
        self.proceesing_job = None

    def update_machine(self):# 更新
        finished_job = None
        if self.status == machine_Status.Idle: 
            self.total_idle_time += 1
            print(f'update_machine: {self.index}: machine_statue: {self.status}, processing_countdown: {self.processing_countdown}')
            return finished_job
        else:
            self.processing_countdown -= 1
            self.total_running_time += 1
            if self.processing_countdown == 0: # 如果完成了加工，job的信息改变，workstation输出队列去，自己状态变为idle
                self.proceesing_job.status_job = Job_Status.Waiting  # 当前job进入workstation的等待队列
                #self.workstation.output_queue.append(self.proceesing_job)
                finished_job = self.proceesing_job
                self.proceesing_job = None
                self.idle()
        print(f'update_machine: {self.index}, machine_statue: {self.status}, processing_countdown: {self.processing_countdown}')
        return finished_job
                

    def set_job(self, job):
        """
        设置该机器开始执行任务
        :param job_duration: 当前任务的持续时间
        """
        self.proceesing_job = job
        self.processing_countdown = job.processing_time[job.current_station_index]
        self.status = machine_Status.Running
        print(f"Machine {self.index} at workstation {self.workstation} is running for {job.job_index} hours.")
    
    def idle(self):
        """
        设置该机器为空闲状态
        :param idle_duration: 空闲的持续时间
        """
        self.status = machine_Status.Idle
        print(f"Machine {self.index} at workstation {self.workstation} is idle.")
    
    def get_status(self):
        """
        返回机器的当前状态
        :return: 机器的状态，idle 或 running
        """
        return self.status
    
    def get_total_times(self):
        """
        获取机器的累计运行和空闲时间
        :return: 返回运行时间和空闲时间
        """
        return self.total_running_time, self.total_idle_time
