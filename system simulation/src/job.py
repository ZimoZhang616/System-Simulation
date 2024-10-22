from global_def import *


# 作业类，表示一个生产任务/工单状态
# Job状态只能被动更改
class JobState(enum.Enum):
    NotExist = 0  # 初始化（位于工厂入口）
    Moving = 1  # 运输中   <--- By Workstation
    Queueing = 2  # 工作站队列中等待    <--- By Workstation
    Working = 3  # 加工中   <--- By Machine
    Ready = 4  # 加工结束（滞留在机器中，未分配机器人）   <--- By Machine
    Waiting = 5  # 等待运输（已分配机器人）   <--- By Robot
    Perished = 6  # 完成


class Job:
    def __init__(self, parent, index, name, job_type):
        self.parent = parent
        self.index = index
        self.name = name
        self.type = job_type  # start from 0

        # Job routing
        self.routing_list = JOB_ROUTING[self.type]  # 路线列表，如 [3, 1, 2, 5]
        self.routing_workstation_list = []

        # Calculate the job service time (Sample from the gamma distribution)
        self.service_time_list = [np.random.gamma(shape=JOB_TIME_GAMMA,
                                                  scale=JOB_MEAN_TIME[self.type][i_routine] / JOB_TIME_GAMMA)
                                  for i_routine in range(len(self.routing_list))]

        self.total_service_time = sum(self.service_time_list)

        # Current state
        self.state = JobState.NotExist
        self.pos = (0, 0)

        self.curr_routing_index = 0  # 当前正在处理的ROUTING索引
        self.curr_workstation = None
        self.next_workstation = None

        self.start_time = None
        self.end_time = None
        self.total_busy_time = None

    def next_routing(self):
        '''
        当JOB离开当前Station时调用
        :return:
        '''
        # self.duration = time.time() - self.start_time
        self.curr_routing_index += 1

        # Proceed job to its next target
        if self.curr_routing_index == len(self.routing_list):
            self.next_workstation = self.parent # return to factory
        else:
            self.next_workstation = self.routing_workstation_list[self.curr_routing_index]



def generate_all_jobs(max_job_num, job_arrival_rate, seed=42):
    # Set the seed for reproducibility
    np.random.seed(seed)
    random.seed(seed)

    # Mean interarrival time based on job arrival rate
    mean_interarrival_time = 1 / job_arrival_rate

    time_list = []
    job_list = []

    current_time = 0
    # Generate jobs
    for i in range(max_job_num):
        # Generate the interarrival time using an exponential distribution
        interarrival_time = np.random.exponential(mean_interarrival_time)

        # Update the current time with the interarrival time
        current_time += interarrival_time

        # Randomly assign a job type based on the given probabilities
        job_type = random.choices(
            population=range(NUM_JOB_TYPES),  # 任务类型的列表
            weights=JOB_PROBABILITY  # 从job_types中提取生成概率
        )[0]
        new_job = Job(parent=None, index=i,
                      name=f'J{i+1}', job_type=job_type)
        time_list.append(current_time)
        job_list.append(new_job)

    return time_list, job_list
