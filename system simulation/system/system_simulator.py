# 系统模拟器类，负责控制整体的流程
from workstation import *
from forklift import *
from job import *
from machine import *
from hub import *



class SystemSimulator:
    def __init__(self, num_workstations, num_machines ,num_forklifts, \
                 forklift_speed, distances, job_types, \
                    thoughtput_goal, job_arrival_rate):
        self.total_time = 28800 # 总时间

        self.workstations = [WorkStation(i) for i in range(0, num_workstations - 1)]  # 创建workstation

        for idx, workstation in enumerate(self.workstations):
            machines = [Machine(i, idx) for i in range(0, num_machines)]  # 为每个workstation创造machine
            workstation.set_machines(machines)

        # 创造收货和进货的站点
        self.workstations.append(Hub(num_workstations - 1, job_types, thoughtput_goal, job_arrival_rate))
        self.workstations[-1].generate_job(self.total_time) # 随机数种子生成

        self.forklifts = [ForkLift(i, forklift_speed, self.workstations, distances) for i in range(num_forklifts)]  # 创建叉车
    
        
        # 随机生成的job，用一个列表存储，其中每个元素[time, type]指在time时添加到5号工作站的输出队列，type为job的种类
        self.job_generated = [] 
    
    def update_machines(self):
        # 更新machine 状态。machine不需要策略，加工什么零件由workstation决定。因此直接update就好
        for idx, workstation in enumerate(self.workstations):
            if idx != len(self.workstations) - 1:
                print(f'update_workstation_num: {idx}')
                for machine in workstation.machines:
                    finished_job = machine.update_machine()
                    if finished_job != None:# 如果这个机器返回的有job,那么放到workstation的输出队列中
                        workstation.output_queue.append(finished_job)
        return

    def update_forklifts(self):
        # 更新 forklifts 状态。forklifts需要策略
        # forklifts策略分为两部分，一部分是否是上货策略，一部分是移动策略

        # 获取所有idle的小车
        for idx, forklift in enumerate(self.forklifts):
            is_idle = forklift.status == ForkLift_Status.Idle
            if is_idle:# 是idle的，需要规划
                #job_queue = self.workstations[forklift.position].output_queue
                # 如果有，这里直接拿一个workstation的输出列表的
                if len(self.workstations[forklift.position].output_queue) != 0:
                    load_job = self.workstations[forklift.position].output_queue.pop(0)
                    load_job.current_station_index += 1
                    forklift.set_loading_job(load_job)
                    # 根据这个job直接去下一个地方。
                    forklift.set_target_workstation(load_job.routing[load_job.current_station_index])
                    load_job.status = Job_Status.Transporting
                # 如果没有，则找一个距离最近的workstation且output里面有货的,这个
                else:
                    find_workstation = None
                    find_dis = 9e9
                    for ws_idx, workstation in enumerate(self.workstations):
                        dis = forklift.distance.get((forklift.position, ws_idx))
                        if len(workstation.output_queue) != 0 and \
                            dis < find_dis:
                             # 找到需要运输的workstation，比较距离
                            find_workstation = workstation
                            find_dis = dis
                    if find_workstation != None: # 都没货，停留不动 有货就去那个地方
                        forklift.set_target_workstation(find_workstation.station_id)
            forklift.update_forklift()
        return
  
    def update_workstations(self):# 更新workstation状态,为machine分配job
        for idx, workstation in enumerate(self.workstations):
            if idx != len(self.workstations) - 1:
                workstation.update_workstation()
        return

    def update_hub(self, time):
        self.workstations[-1].update_hub(time)
        return

    def system_running(self):
        # 主流程控制逻辑
        for time in range(self.total_time):
            # 更新机器，小车，和workstation，找到需要输入指令的小车
            print('***************************************************************************************')
            print(f'time: {time}')
            self.update_machines()
            self.update_forklifts()
            self.update_workstations()
            self.update_hub(time)
            #self.print_sys_info()
            print('***************************************************************************************')

    def print_sys_info(self):

        print("Workstations info:")
        for workstation in self.workstations:
            print(f'workstation_id: {workstation.station_id}: workstation_input_number: {job_id} of type {job_type} completed')


        
    def system_terminate(self):
        pass








