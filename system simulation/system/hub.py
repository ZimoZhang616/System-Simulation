import job
from machine import *
from workstation import *
import random


class Hub(WorkStation):
    def __init__(self, station_id, job_types, thoughtput_goal, job_arrival_rate):
        super().__init__(station_id)  # 调用父类的构造函数
        self.job_types = job_types
        self.thoughtput_goal = thoughtput_goal
        self.job_arrival_rate = job_arrival_rate
        self.job_initialize_list = [] # 初始化列表，在开始的时候生成随机数
        self.total_jobs = 0 
        

    def generate_job(self, total_simulation_time):
        """
        随机数种子生成self.job_initialize_list = [] 
        """
        """
        根据到达率生成随机任务，随机数种子生成 self.job_initialize_list
        """
        random.seed(4)
        interarrival_time = 1 / self.job_arrival_rate  # 平均到达时间 (小时)
        #total_simulation_time = 8 * 3600  # 8小时的总模拟时间，单位秒
        time = 0  # 初始化当前时间
        
        while time < total_simulation_time:
            # 随机选择任务类型，概率根据self.job_types的配置
            job_type = random.choices(
                population=list(self.job_types.keys()),  # 任务类型的列表
                weights=[self.job_types[job]['generate_probability'] for job in self.job_types]  # 从job_types中提取生成概率
                )[0]
            
            # 获取该任务类型的操作工序和平均服务时间
            operations = self.job_types[job_type]['operations']
            service_times = self.job_types[job_type]['mean_service_times']
            
            # 创建新任务并加入初始化列表
            new_job = job.Job(self.total_jobs, job_type, operations, service_times, time)
            self.job_initialize_list.append(new_job)
            
            # 更新下一个任务的到达时间
            next_arrival_time = random.expovariate(self.job_arrival_rate)
            next_arrival_time = round(next_arrival_time* 3600) # 转换成秒并圆整
            time += next_arrival_time   
            
            # 更新已生成的任务数
            self.total_jobs += 1
        

    def update_hub(self, time):
        # 根据已经生成的随机数，每过一秒，在output队列里面添加任务
        for tmp_job in self.job_initialize_list:
            if tmp_job.start_time == time:
                tmp_job.status = Job_Status.Waiting
                self.output_queue.append(tmp_job)
        print(f'update_hub, hub_output_queue: {self.output_queue}')




