import enum

# 作业类，表示一个生产任务
# 定义枚举类型
class Job_Status(enum.Enum):
    NotExist = 1
    Working = 2
    Queueing = 3
    Waiting = 4
    Transporting = 5
    Perished = 6

class Job:
    def __init__(self, index, job_type, routing, processing_time, start_time):
        """
        初始化作业
        :param job_type: 作业的类型（1, 2, 3）
        :param routing: 该作业的工作站路线
        """
        self.job_type = job_type
        self.job_index = index
        self.routing = routing   # 路线列表，如 [3, 1, 2, 5]

        self.processing_time = processing_time # 每个地方需要耗费的时间，如 [10,15,20]
        self.current_station_index = 0  # 当前正在处理的工作站索引

        self.status_job = Job_Status.NotExist
        self.start_time = start_time
        self.duration = 0
    
    def update_job_info(self, status_job, present_time):
        self.status_job = status_job
        self.duration = present_time - self.start_time
        self.current_station_index += 1

        if self.current_station_index == len(self.routing):# 如果到了终点，就结束！
            self.status_job = Job_Status.Perished

