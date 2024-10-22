from global_def import *

# 作业类，表示一个生产任务/工单状态
# Job状态只能被动更改
class JobState(enum.Enum):
    NotExist = 0        # 初始化（位于工厂入口）
    Queueing = 1        # 工作站队列中等待    <--- By Workstation
    Transporting = 2    # 运输中   <--- By Workstation
    Processing = 3      # 加工中   <--- By Machine
    Halted = 4          # 滞留在机器中（加工完成，未分配机器人）   <--- By Machine
    Waiting = 5         # 等待运输（已分配机器人）   <--- By Robot
    Perished = 6        # 完成

class Job:
    def __init__(self, index, job_type):
        self.index = index
        self.type = job_type    # start from 0

        # Job routing
        self.routing_list = JOB_ROUTING[self.type]   # 路线列表，如 [3, 1, 2, 5]
        self.routing_workstation_list = []

        # Calculate the job service time (Sample from the gamma distribution)
        self.service_time_list = [np.random.gamma(shape=JOB_TIME_GAMMA,
                                                  scale=JOB_MEAN_TIME[self.type][i_routine] / JOB_TIME_GAMMA)
                                  for i_routine in range(len(self.routing_list))]

        # Current state
        self.state = JobState.NotExist
        self.pos = (0, 0)

        self.curr_routing_index = 0  # 当前正在处理的ROUTING索引
        self.curr_workstation = None
        self.curr_machine = None
        self.next_workstation = None
        self.next_machine = None

        self.start_time = time.time()
        self.duration = 0
    
    def next_routing(self):
        '''
        当JOB离开当前Station时调用
        :return:
        '''
        # self.duration = time.time() - self.start_time
        self.curr_routing_index += 1
        self.next_workstation = self.routing_workstation_list[self.curr_routing_index]

        # 结束条件
        # if self.curr_routing_index == len(self.routing_list):
        #     self.state = JobState.Perished


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
        new_job = Job(index=i, job_type=job_type)
        time_list.append(current_time)
        job_list.append(new_job)

    return time_list, job_list

