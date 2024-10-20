from job import *
from machine import *
from workstation import *
import enum

class ForkLift_Status(enum.Enum):
    Idle = 1
    Loaded_Moving = 2
    Unloaded_Moving = 3

# 叉车类，用于处理工作站间的作业运输
class ForkLift:
    def __init__(self, forklift_index, speed, workstations, distance):
        """
        初始化叉车
        :param speed: 叉车的移动速度（英尺/秒）
        """
        self.forklift_index = forklift_index
        self.speed = speed
        self.position = 5  # 叉车当前所在的workstation
        self.workstations = workstations
        self.status = ForkLift_Status.Idle
        self.jobs = []  # 车子上的job，目前是1个，如果要做3D打印可以带多个
    
        self.distance = distance # 地图
        self.target_station = None
        self.total_Loaded_Moving_time = 0  # 拖车有货的运行时间
        self.total_Unloaded_Moving_time = 0  # 拖车有货的运行时间
        self.total_idle_time = 0  # 拖车总空闲时间

        self.transporting_time = 0

    def pick_up_job(self, job):
        """
        取走作业
        :param job: 需要运输的作业
        """
        self.jobs.append(job)
        # 将作业送到下一个工作站
        pass

    def update_forklift(self):
        if self.status == ForkLift_Status.Idle:# 空闲的
            self.total_idle_time += 1
            print(f'update_forklift: {self.forklift_index}, forklift_status: {self.status}, forklift_position: {self.position}, forklift_target: {self.target_station}, forklift_job: {self.jobs},  transporting_time: {self.transporting_time}')
            return True # 等待指令
        elif self.status == ForkLift_Status.Loaded_Moving: # 载货跑
            self.total_Loaded_Moving_time += 1
            self.transporting_time -= 1
            if self.transporting_time == 0: #到达目的地，卸货给workstation，然后等待指令
                unload_job = self.jobs.pop(0)
                unload_job.status = Job_Status.Queueing
                self.workstations[self.target_station].input_queue.append(unload_job)
                self.status = ForkLift_Status.Idle
                print(f'update_forklift: {self.forklift_index}, forklift_status: {self.status}, forklift_position: {self.position}, forklift_target: {self.target_station}, forklift_job: {self.jobs},  transporting_time: {self.transporting_time}')
                return True
            else: # 还没到目的地，倒计时继续跑
                print(f'update_forklift: {self.forklift_index}, forklift_status: {self.status}, forklift_position: {self.position}, forklift_target: {self.target_station}, forklift_job: {self.jobs},  transporting_time: {self.transporting_time}')
                return False
        else: # 没载货跑
            self.total_Unloaded_Moving_time += 1
            self.transporting_time -= 1
            if self.transporting_time == 0: #到达目的地，变成空闲的，等待指令装货
                self.status = ForkLift_Status.Idle
                print(f'update_forklift: {self.forklift_index}, forklift_status: {self.status}, forklift_position: {self.position}, forklift_target: {self.target_station}, forklift_job: {self.jobs},  transporting_time: {self.transporting_time}')
                return True
            else: # 还没到目的地，倒计时继续跑
                print(f'update_forklift: {self.forklift_index}, forklift_status: {self.status}, forklift_position: {self.position}, forklift_target: {self.target_station}, forklift_job: {self.jobs},  transporting_time: {self.transporting_time}')
                return False

    def set_target_workstation(self, target_workstation): # 设置移动目标
        self.target_station = target_workstation
        if self.target_station != self.position: # 移动去下一个位置
            dis = self.distance.get((self.position, self.target_station), 0)
            self.transporting_time = int(dis / self.speed) + 1
            self.position = self.target_station
            if len(self.jobs) == 0:
                self.status = ForkLift_Status.Unloaded_Moving
            else:
                self.status = ForkLift_Status.Loaded_Moving
            return True #目标设置成功
        
        return False #目标设置失败
    
    def set_loading_job(self, job): # 给拖车上货，这里上货和移动策略分开，因为可能会有改动
        self.jobs.append(job)

        


    
