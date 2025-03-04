from global_def import *
from job import *


# Temp functions:
def calculate_distance(pos_start, pos_end):
    """Calculate Euclidean distance between two points (x1, y1) and (x2, y2)."""
    return (pos_end[0] - pos_start[0],
            pos_end[1] - pos_start[1],
            ((pos_end[0] - pos_start[0]) ** 2 + (pos_end[1] - pos_start[1]) ** 2) ** 0.5)


class DeviceState(enum.Enum):
    Idle = 0  # no job to do
    Busy = 1  # robot moving / machine processing


class Device:
    def __init__(self, parent=None, index=0, name='', pos=FACTORY_POS):
        self.parent = parent  # parent node
        self.index = index  # index
        self.name = name  # device name
        self.pos = pos  # position in real-word unit

        # current state
        self.state = DeviceState.Idle
        self.is_loaded = False  # if the device is loaded with job/item

        # timing
        self.total_run_time = EPS  # total time since init
        self.curr_busy_time = EPS  # busy time of current job
        self.total_idle_time = EPS
        self.total_busy_time = EPS
        self.time_utilization = EPS  # total_busy_time / total_run_time

        # input queue
        self.input_queue = []
        self.input_queue_len = 0
        self.input_job_count = [0 for i_tmp in range(NUM_JOB_TYPES)]  # count of all input jobs
        self.total_input_job = 0

        # output queue
        self.output_queue = []
        self.output_queue_len = 0
        self.output_job_count = [0 for i_tmp in range(NUM_JOB_TYPES)]  # count of all output jobs
        self.total_output_job = 0

    def update_time(self):  # update the device timing
        self.total_run_time += BACKEND_CYCLE_TIME

        if self.state == DeviceState.Busy:
            self.curr_busy_time += BACKEND_CYCLE_TIME
            self.total_busy_time += BACKEND_CYCLE_TIME
        else:
            self.total_idle_time += BACKEND_CYCLE_TIME

        self.time_utilization = self.total_busy_time / self.total_run_time if self.total_run_time else 0.0

    def add_job(self, job):
        pass

    def drop_job(self, job):
        pass

    def draw(self, screen):  # draw the device on GUI
        pass


class Machine(Device):
    def __init__(self, parent=None, index=0, name='', pos=(0, 0)):
        super().__init__(parent, index, name, pos)

        self.curr_job = None
        self.curr_job_time = 0

    def update(self):
        self.update_time()

        # current job is finished
        if (self.state == DeviceState.Busy and
                self.curr_busy_time >= self.curr_job_time):
            self.drop_job(self.curr_job)

    def add_job(self, job):
        '''

        :param job: the target job
        :return:
            RTN_ERR: 失败，则忽略该Job
            RTN_OK: 成功，则立即开始生产
        '''
        if self.state != DeviceState.Idle:
            return RTN_ERR

        job.state = JobState.Working  # <--------------- Edit Job

        self.curr_job = job
        self.curr_job_time = job.service_time_list[job.curr_routing_index]

        self.state = DeviceState.Busy
        self.curr_busy_time = 0
        self.is_loaded = True

        # record
        self.input_job_count[self.curr_job.type] += 1
        self.total_input_job += 1

        return RTN_OK

    def drop_job(self, job):
        if self.state != DeviceState.Busy:
            return RTN_ERR

        job.state = JobState.Ready  # <--------------- Edit Job
        job.next_routing()  # <--------------- Edit Job

        self.curr_job = None
        self.curr_job_time = 0

        self.state = DeviceState.Idle
        self.curr_busy_time = 0
        self.is_loaded = False

        # add to parent pool/queue
        self.parent.output_queue.append(job)
        self.parent.output_queue_len += 1

        # record
        self.output_job_count[job.type] += 1
        self.total_output_job += 1

        return RTN_OK

    def get_show_text(self):
        if self.state == DeviceState.Busy:
            percentage_complete = int((self.curr_busy_time / self.curr_job_time) * 100)
            return f'**{self.name}** : [{self.curr_job.name}] | {percentage_complete:2d}%', COLOR_GREEN
        else:
            return f'**{self.name}** : Idle', COLOR_YELLOW


class Workstation(Device):
    """
    One workstation is composed of several machines
    -> Policy: Distribute Jobs in the Queue to IDLE Machines
    """

    def __init__(self, parent=None, index=0, name='', pos=(0, 0)):
        super().__init__(parent, index, name, pos)

        self.num_machines = NUM_MACHINES_WORKSTATION[self.index]
        self.machines = [Machine(parent=self,
                                 index=i_machine,
                                 name=f'M{i_machine + 1}',
                                 pos=self.pos)
                         for i_machine in range(self.num_machines)]

        self.workstation_policy = WORKSTATION_POLICY_NAME
        self.q_table = {}

    def get_current_state(self):
        """获取当前队列状态"""
        return (
            len(self.input_queue),  # 队列长度
            tuple(bottle.remaining_steps for bottle in self.input_queue),  # 每个瓶子的剩余步骤
            tuple(bottle.service_time_list[bottle.curr_routing_index] for bottle in self.input_queue)  # 当前步骤的处理时间
        )

    def get_possible_actions(self):
        """生成所有可能的动作"""
        actions = []
        for i in range(len(self.input_queue)):
            for j in range(i + 1, len(self.input_queue)):
                actions.append((i, j))  # 交换队列中第 i 和第 j 个瓶子
        return actions

    def adjust_queue(self, action):
        """根据动作调整队列"""
        i, j = action
        self.input_queue[i], self.input_queue[j] = self.input_queue[j], self.input_queue[i]

    def compute_reward(self, current_queue, new_queue):
        """计算队列调整后的奖励"""
        current_waiting_time = sum(bottle.total_process_time for bottle in current_queue)
        new_waiting_time = sum(bottle.total_process_time for bottle in new_queue)
        return current_waiting_time - new_waiting_time  # 奖励为等待时间减少量

    def update_q_table(self, state, action, reward, next_state):
        """更新 Q 表"""
        best_next_action = max(
            self.get_possible_actions(),
            key=lambda a: self.q_table.get((next_state, a), 0.0),
            default=None
        )
        # 更新 Q 值
        self.q_table[(state, action)] += ALPHA * (
                reward + GAMMA * self.q_table.get((next_state, best_next_action), 0.0) - self.q_table.get(
            (state, action), 0.0)
        )

        # 调试信息：打印更新的 Q 值
        print(f"Updated Q[{state}, {action}] = {self.q_table[(state, action)]:.2f}")

    def select_action(self, state):
        """基于 epsilon-greedy 策略选择动作"""
        possible_actions = self.get_possible_actions()
        if not possible_actions:
            return None
        if np.random.rand() < EPSILON:  # 探索
            return random.choice(possible_actions)
        else:  # 利用
            return max(possible_actions, key=lambda a: self.q_table.get((state, a), 0.0))

    def initialize_q_table(self):
        """为工作站初始化 Q 表"""
        for i in range(len(self.input_queue)):
            for j in range(i + 1, len(self.input_queue)):
                state = self.get_current_state()
                action = (i, j)  # 交换两个瓶子的动作
                self.q_table[(state, action)] = 0.0  # 初始化 Q 值为 0

    def my_workstation_policy(self):
        ''' Machine Policy Here '''
        if self.workstation_policy == 'FIFO':
            # update machine states
            for machine in self.machines:
                if machine.state == DeviceState.Idle and self.input_queue_len > 0:
                    temp_job = self.input_queue.pop(0)
                    self.input_queue_len = len(self.input_queue)
                    machine.add_job(temp_job)
                machine.update()
        elif self.workstation_policy == 'RANDOM':
            # update machine states
            for machine in self.machines:
                if machine.state == DeviceState.Idle and self.input_queue_len > 0:
                    temp_job = random.choice(self.input_queue)
                    self.input_queue.remove(temp_job)
                    self.input_queue_len = len(self.input_queue)
                    machine.add_job(temp_job)
                machine.update()
        elif self.workstation_policy == 'NEH':
            # NEH policy, find the total processing time of each job (the sum of processing times across all machines).
            for machine in self.machines:
                if machine.state == DeviceState.Idle and self.input_queue_len > 0:
                    self.NEH_ws_policy()
                    self.input_queue_len = len(self.input_queue)
                    #machine.add_job(temp_job)
                machine.update()
        elif self.robot_policy == 'Q_LEARNING_QUEUE':
            for ws in self.workstations:
                state = ws.get_current_state()  # 获取当前状态
                action = ws.select_action(state)  # 选择动作
                if action is None:
                    continue  # 如果没有动作可执行，跳过

                # 执行动作调整队列
                ws.adjust_queue(action)

                # 计算奖励并更新 Q 表
                next_state = ws.get_current_state()
                reward = ws.compute_reward(ws.input_queue, ws.input_queue)  # 比较调整前后队列的奖励
                ws.update_q_table(state, action, reward, next_state)

    def NEH_ws_policy(self):
        """
        NEH policy for job assignment to machines. This policy sorts jobs by total processing time and assigns
        them in a way that minimizes makespan (completion time).
        """
        # Step 1: Calculate total processing time for each job
        job_total_times = []
        for job in self.input_queue:
            #total_time = sum(job.service_time_list)  # Sum of processing times across all machines
            job_total_times.append((job, job.total_process_time))

        # Step 2: Sort jobs in descending order by total processing time
        job_total_times.sort(key=lambda x: x[1], reverse=True)  # Sort by total time (descending)

        # Step 3: Assign jobs to machines
        for job, _ in job_total_times:
            # Find an idle machine and assign the job
            assigned = False  # Flag to track if the job was assigned

            for machine in self.machines:
                if machine.state == DeviceState.Idle:
                    # Add the job to the machine
                    self.input_queue.remove(job)  # Remove job from queue
                    machine.add_job(job)  # Assign job to the machine
                    assigned = True  # Mark job as assigned
                    break  # Exit the machine loop once job is assigned

            if not assigned:
                # If no idle machine was found for this job, it remains in the queue.
                break  # Exit the loop if no machines are available for further job assignment


    def update(self):
        self.update_time()

        # customized workstation policy
        self.my_workstation_policy()

        # curr state:
        if any(machine.state == DeviceState.Busy for machine in self.machines):
            self.state = DeviceState.Busy
        else:
            self.state = DeviceState.Idle

        # timing
        # use mean time of utilization of all machines
        self.time_utilization = np.mean([machine.time_utilization for machine in self.machines])

        # 在 device.py 文件的 Workstation 类的 update() 方法末尾加入
        with open('queue_log_40_R_random_W_random_646444.csv', 'a') as f:
            f.write(f"{self.total_run_time},{self.index},{self.input_queue_len}\n")

    def add_job(self, job):

        job.state = JobState.Queueing  # <--------------- Edit Job
        job.curr_workstation = self  # <--------------- Edit Job

        self.input_queue.append(job)
        self.input_queue_len = len(self.input_queue)

        # record
        self.input_job_count[job.type] += 1
        self.total_input_job += 1
        return RTN_OK

    def drop_job(self, job):
        self.output_queue.remove(job)
        self.output_queue_len -= 1

        # record
        self.output_job_count[job.type] += 1
        self.total_output_job += 1
        return RTN_OK

    def draw(self, screen):

        # Create text to be showed on screen
        show_text_list = [(f'**{self.name}** ', COLOR_LIGHT_GREY)]

        # Add machine info to the text
        for machine in self.machines:
            status_text, color = machine.get_show_text()
            show_text_list.append((status_text, color))

        # Display the mean busy ratio of the machines in this workstation
        show_text_list.append((f'Time Util:{self.time_utilization * 100:3.0f}%', COLOR_LIGHT_BLUE))
        show_text_list.append((f'Q_Out: {[temp_job.name for temp_job in self.output_queue]}', COLOR_LIGHT_BLUE))
        show_text_list.append((f'Output: {self.total_output_job}', COLOR_LIGHT_BLUE))
        show_text_list.append((f'Queue: {self.input_queue_len}', COLOR_LIGHT_BLUE))

        # Draw the text box at the designated position
        box_pos = map_to_screen(self.pos)
        if self.pos[1] > 0:  # For top workstations, bottom center aligned
            draw_text_box(screen, show_text_list, box_pos, top_center=False, align_center=False)
        else:  # For lower workstations, top center aligned
            draw_text_box(screen, show_text_list, box_pos, top_center=True, align_center=False)


class Robot(Device):
    def __init__(self, parent=None, index=0, name='', pos=(-200,75)):
        super().__init__(parent, index, name, pos)

        self.speed = ROBOT_SPEED

        self.curr_job = None
        self.pick_up_workstation = None  # 收货位置
        self.deliver_workstation = None  # 送货位置
        self.target_pos = FACTORY_POS  # 当前目标

        self.distance_travelled_pct = 0
        self.total_distance_travelled = 0

    def update(self):
        self.update_time()

        if self.state == DeviceState.Idle:
            return

        # in busy state
        dx, dy, dist = calculate_distance(self.pos, self.target_pos)

        # if arrived:
        if dist <= self.speed * BACKEND_CYCLE_TIME:
            self.pos = self.target_pos  # Snap to target position
            self.distance_travelled_pct = 0

            # 空载跑 -> 去收货 -> 继续送货（BUSY）
            if not self.is_loaded:
                self.state = DeviceState.Busy
                if self.pick_up_workstation == self.parent:
                    self.parent.input_queue.remove(self.curr_job)
                    self.parent.input_queue_len -= 1
                else:
                    self.pick_up_workstation.drop_job(self.curr_job)
                self.curr_job.state = JobState.Moving  # <--------------- Edit Job
                self.target_pos = self.curr_job.next_workstation.pos
                self.is_loaded = True

            # 载货跑 -> 去送货 -> IDLE
            else:
                self.state = DeviceState.Idle
                if self.deliver_workstation == self.parent:
                    self.parent.drop_job(self.curr_job)
                else:
                    self.deliver_workstation.add_job(self.curr_job)
                self.drop_job(self.curr_job)
                self.is_loaded = False

        else:  # not arrived
            self.state = DeviceState.Busy
            distance_travelled = self.speed * BACKEND_CYCLE_TIME
            travel_fraction = distance_travelled / dist
            self.pos = (self.pos[0] + dx * travel_fraction, self.pos[1] + dy * travel_fraction)
            self.total_distance_travelled += distance_travelled
            self.distance_travelled_pct = min(self.distance_travelled_pct + travel_fraction * 100, 100)  # Cap at 100%

    def add_job(self, job):
        '''

        :param job:
        :return:
            RTN_ERR: 不接受当前任务
            RTN_OK: 接受任务后，立即启动
        '''
        if self.state != DeviceState.Idle:
            return RTN_ERR

        job.state = JobState.Waiting  # <--------------- Edit Job

        self.curr_job = job
        self.state = DeviceState.Busy
        self.curr_busy_time = 0

        self.pick_up_workstation = job.curr_workstation
        self.deliver_workstation = job.next_workstation
        self.target_pos = self.pick_up_workstation.pos

        self.is_loaded = False

        # record
        self.input_job_count[job.type] += 1
        self.total_input_job += 1

        return RTN_OK

    def drop_job(self, job):

        self.curr_job = None
        self.state = DeviceState.Idle
        self.curr_busy_time = 0

        self.pick_up_workstation = None
        self.deliver_workstation = None
        self.target_pos = FACTORY_POS

        self.is_loaded = False

        # record
        self.output_job_count[job.type] += 1
        self.total_output_job += 1

        return RTN_OK

    def draw(self, screen):
        font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE)

        if self.state == DeviceState.Busy:
            if self.is_loaded:
                color = COLOR_GREEN
            else:
                color = COLOR_WHITE
        else:
            color = COLOR_YELLOW
        screen_pos = map_to_screen(self.pos)

        pygame.draw.circle(screen, color, screen_pos, ROBOT_DIAMETER // 2)

        # show name
        robot_mark_text = font.render(f'{self.name}', True, COLOR_BLACK)
        screen.blit(robot_mark_text, (screen_pos[0] - 8, screen_pos[1] - 8))

        # show percentage
        percentage_text = f'{int(self.distance_travelled_pct)}%'
        if self.curr_job:
            percentage_text += f'[{self.curr_job.name}]'
        percentage_text = font.render(percentage_text, True, COLOR_BLACK)
        screen.blit(percentage_text, (screen_pos[0] - 15, screen_pos[1] - 35))


class Factory(Device):
    """
    One Factory is composed of several workstations, several robots, and the input/output ports
    """

    def __init__(self, parent=None, index=0, name='', pos=FACTORY_POS):
        super().__init__(parent, index, name, pos)

        # init all workstations
        self.num_workstations = NUM_WORKSTATIONS
        self.workstations = [Workstation(parent=self,
                                         index=i_workstation,
                                         name=f'W{i_workstation + 1}',
                                         pos=WORKSTATION_POS[i_workstation])
                             for i_workstation in range(self.num_workstations)]

        # init all robots
        self.num_robots = NUM_ROBOTS
        self.robots = [Robot(parent=self,
                             index=i_robot,
                             name=f'R{i_robot + 1}',
                             pos=FACTORY_POS)
                       for i_robot in range(self.num_robots)]
        self.robot_policy = ROBOT_POLICY_NAME

        # all jobs
        self.job_times = []
        self.jobs = []
        self.curr_job_index = 0
        self.total_num_jobs = 0

        self.is_job_alive = []

        # pause
        self.is_paused = False

    def set_jobs(self, job_times, jobs):
        '''
        添加预先生成的Job列表，并初始化Job内部参数
        :param job_times:
        :param jobs:
        :return:
        '''
        self.job_times = job_times
        self.jobs = jobs
        for job in self.jobs:
            job.parent = self
            job.routing_workstation_list = [self.workstations[job.routing_list[i_routine] - 1]
                                            for i_routine in range(len(job.routing_list))]
            job.state = JobState.Ready  # <--------------- Edit Job
            #job.pos = self.pos
            job.pos = (-300, 0)  # Job 生成在 (-300, 0)

            job.curr_workstation = self
            job.next_workstation = job.routing_workstation_list[0]

        self.total_num_jobs = len(self.jobs)

        self.is_job_alive = [False for job in self.jobs]

    def generate_job(self):
        # 创建新任务并加入初始化列表
        new_job_list = []

        if self.curr_job_index >= self.total_num_jobs - 1:
            return []

        for i in range(self.curr_job_index, self.total_num_jobs):
            if self.total_run_time >= self.job_times[i]:
                new_job_list.append(self.jobs[i])
            else:
                self.curr_job_index = i
                break

        return new_job_list

    def NEH_robot_policy(self, job_list):
        """
        NEH policy for job assignment to machines. This policy sorts jobs by total processing time and assigns
        them in a way that minimizes makespan (completion time).
        """
        # Step 1: Calculate total processing time for each job
        job_total_times = []
        for job in job_list:
            job_total_times.append((job, job.total_process_time))

        # Step 2: Sort jobs in descending order by total processing time
        job_total_times.sort(key=lambda x: x[1], reverse=True)  # Sort by total time (descending)

        return job_total_times[0][0]
    

    def run_my_policy(self):
        # TODO
        # policy default: based on random assigned jobs
        # policy R_1: Robot-oriented, target is to maximize the robot utilization
        # policy M_1: Machine-oriented, target is to maximize the machine/workstation utilization,
        #           or minimize queue delays
        # policy J_1: Job-oriented, target is to minimize the job queueing/waiting time 
        #           or maximize job throughput

        # random
        if self.robot_policy == 'DEFAULT':
            for robot in self.robots:
                if robot.state == DeviceState.Idle:
                    ready_jobs = [self.jobs[i_job]
                                  for i_job in range(self.total_num_jobs)
                                  if self.is_job_alive[i_job] is True
                                  and self.jobs[i_job].state == JobState.Ready]
                    if len(ready_jobs) > 0:
                        temp_job = random.choice(ready_jobs)
                        robot.add_job(temp_job)
        # Robot-oriented policy: Maximize robot utilization
        elif self.robot_policy == 'DISTANCE' or self.robot_policy == 'DISTANCE_NEH':
            for robot in self.robots:
                if robot.state == DeviceState.Idle:
                    # Find the closest workstation with jobs in the output queue
                    closest_workstation = None
                    min_distance = float('inf')
                    for workstation in self.workstations:
                        if workstation.output_queue_len > 0 and \
                            any(tmp_job.state == JobState.Ready for tmp_job in workstation.output_queue):
                            # Calculate distance between robot and workstation
                            dx, dy, distance = calculate_distance(robot.pos, workstation.pos)
                            if distance < min_distance:
                                min_distance = distance
                                closest_workstation = workstation
                    if (self.input_queue_len > 0 and \
                            any(tmp_job.state == JobState.Ready for tmp_job in self.input_queue)):
                        dx, dy, distance = calculate_distance(robot.pos, self.pos)
                        if distance < min_distance:
                            min_distance = distance
                            closest_workstation = self
                    #print(closest_workstation.index)
                    # If a workstation with jobs is found, move the robot to pick up the job
                    if closest_workstation:
                        if closest_workstation != self:
                            tmp_queue = closest_workstation.output_queue
                            #choosable_jobs = [tmp_job for tmp_job in tmp_queue if tmp_job.state == JobState.Ready]
                        else:
                            tmp_queue = self.input_queue
                        choosable_jobs = [tmp_job for tmp_job in tmp_queue if tmp_job.state == JobState.Ready]
                        if self.robot_policy == 'DISTANCE_NEH':
                            temp_job = self.NEH_robot_policy(choosable_jobs)
                        else:
                            temp_job = random.choice(choosable_jobs)
                        robot.add_job(temp_job)

        elif self.robot_policy == 'Q_LEARNING_QUEUE':
            for ws in self.workstations:
                state = ws.get_current_state()  # 获取当前状态
                action = ws.select_action(state)  # 选择动作
                if action is None:
                    continue  # 如果没有动作可执行，跳过

                # 打印调整前的队列状态
                print(f"Queue before adjustment: {state}")

                # 执行动作调整队列
                ws.adjust_queue(action)

                # 打印调整后的队列状态
                next_state = ws.get_current_state()
                print(f"Queue after adjustment: {next_state}")

                # 计算奖励并更新 Q 表
                reward = ws.compute_reward(ws.input_queue, ws.input_queue)  # 比较调整前后队列的奖励
                print(f"Reward: {reward}")  # 打印奖励信息
                ws.update_q_table(state, action, reward, next_state)

        # # Machine-oriented policy: Maximize machine/workstation utilization
        # elif self.robot_policy == 'M1':
        #     for workstation in self.workstations:
        #         for machine in workstation.machines:
        #             if machine.state == DeviceState.Idle and workstation.input_queue_len > 0:
        #                 # Assign the next job in the queue to the idle machine
        #                 next_job = workstation.input_queue.pop(0)
        #                 machine.add_job(next_job)
        #                 print(
        #                     f"Job {next_job.index} assigned to Machine {machine.name} in Workstation {workstation.name}")

        # # Job-oriented policy: Minimize job queueing/waiting time
        # elif self.robot_policy == 'J1':
        #     # Prioritize jobs that have been in the queue the longest
        #     for workstation in self.workstations:
        #         if workstation.input_queue_len > 0:
        #             # Assign jobs from workstations with the longest queue to available robots
        #             longest_waiting_job = None
        #             longest_queue_workstation = None
        #             max_queue_len = 0
        #             for ws in self.workstations:
        #                 if ws.input_queue_len > max_queue_len:
        #                     max_queue_len = ws.input_queue_len
        #                     longest_waiting_job = ws.input_queue[0]
        #                     longest_queue_workstation = ws

        #             # Find an idle robot to transport the job
        #             for robot in self.robots:
        #                 if robot.state == DeviceState.Idle:
        #                     robot.target_workstation = longest_queue_workstation
        #                     robot.state = DeviceState.Busy
        #                     print(
        #                         f"Robot {robot.name} transporting job {longest_waiting_job.index} from {longest_queue_workstation.name}")
        #                     break

        # elif self.robot_policy == 'NA':
        #     pass
        else:
            raise ValueError(f'POLICY_NAME {self.robot_policy} not recognized')

    def update(self):
        if self.is_paused:
            return

        self.update_time()

        # 随机产生新的job
        new_jobs = self.generate_job()
        for job in new_jobs:
            self.add_job(job)

        # update all workstations
        for workstation in self.workstations:
            workstation.update()

        # update all robots
        for robot in self.robots:
            robot.update()

        # Run user-defined policy
        self.run_my_policy()

    def add_job(self, job):
        job.state = JobState.Ready  # <--------------- Edit Job
        job.start_time = self.total_run_time  # <--------------- Edit Job

        self.input_queue.append(job)
        self.input_queue_len = len(self.input_queue)

        self.is_job_alive[job.index] = True

        # record
        self.input_job_count[job.type] += 1
        self.total_input_job += 1
        return RTN_OK

    def drop_job(self, job):

        job.state = JobState.Perished  # <--------------- Edit Job
        job.end_time = self.total_run_time  # <--------------- Edit Job
        job.total_busy_time = job.end_time - job.start_time  # <--------------- Edit Job

        self.is_job_alive[job.index] = False

        # record
        self.output_job_count[job.type] += 1
        self.total_output_job += 1
        return RTN_OK

    def process_cmd(self, cmd):
        print(f"Processing command: {cmd}")
        pass

    def draw(self, screen):
        ''''''

        '''Factory State'''
        # Create text to be showed on screen
        show_text_list = [
            (f'**{self.name}**', COLOR_LIGHT_GREY),
            (f'Time: {seconds_to_hhmmss(self.total_run_time)}', COLOR_LIGHT_BLUE),
            (f'Out: {self.total_output_job}', COLOR_LIGHT_BLUE),
            (f'Out: {self.total_output_job / self.total_run_time * 3600:.1f} /h', COLOR_LIGHT_BLUE),
            (f'In: {self.total_input_job}', COLOR_LIGHT_BLUE),
            (f'In: {self.total_input_job / self.total_run_time * 3600:.1f} /h', COLOR_LIGHT_BLUE),
            (f'(In-Out): {self.total_input_job - self.total_output_job}', COLOR_LIGHT_BLUE),
            (f'Queue: {int(self.input_queue_len)}', COLOR_LIGHT_BLUE)
        ]

        # Draw the text box at the designated position, top center aligned
        #box_pos = map_to_screen(self.pos)
        # 如果是 Entry 工厂，使用专门的绘制大框方法
        if self.name == 'Entry':
            box_pos = map_to_screen((self.pos[0]-100, self.pos[1]+500))
            self.draw_entry_box(screen, show_text_list, box_pos, max_width=200, max_height=600)
        else:
            # 对于其他工厂，使用通用的绘制方法
            box_pos = map_to_screen((self.pos[0], self.pos[1]))
            draw_text_box(screen, show_text_list, box_pos, top_center=True, align_center=False, max_width=300)  # 默认大小
        for workstation in self.workstations:
            workstation.draw(screen)

        for robot in self.robots:
            robot.draw(screen)

        '''Job State'''
        # Show job status on the side:
        box_pos = map_to_screen((self.pos[0] + WORLD_WIDTH * 0.5 + 370,
                                 self.pos[1] + WORLD_HEIGHT))
        side_text = []
        i_plot = 0
        total_alive_job = sum(self.is_job_alive)
        job_time_mean = np.mean([job.total_busy_time for job in self.jobs if job.total_busy_time is not None])
        side_text.append((f'Total alive jobs: {total_alive_job}', COLOR_LIGHT_GREY))
        side_text.append((f'> Job Total Time (mean): {job_time_mean:.1f} s', COLOR_LIGHT_GREY))

        MAX_JOB_TO_SHOW = 10
        for i_job in range(self.total_num_jobs):
            if i_plot >= MAX_JOB_TO_SHOW:
                break
            if self.is_job_alive[i_job]:
                i_plot += 1
                temp_job = self.jobs[i_job]
                temp_text = f'{temp_job.name}|'
                temp_text += f'idx {temp_job.curr_routing_index}|'
                temp_text += f'{temp_job.routing_list}|'
                temp_text += f'{temp_job.state}'[9:]
                temp_text += f' @ {temp_job.curr_workstation.name}'
                side_text.append((temp_text, COLOR_LIGHT_BLUE))
        draw_text_box(screen, side_text, box_pos,
                      top_center=True, align_center=False, show_box=False,
                      max_width=420)

        '''Robot State'''
        # Show robot status on the side:
        box_pos = map_to_screen((self.pos[0] + WORLD_WIDTH * 0.5 + 370,
                                 self.pos[1] + WORLD_HEIGHT - 450))
        side_text = []
        i_plot = 0
        total_busy_robot = sum([robot.state == DeviceState.Idle for robot in self.robots])
        mean_robot_util = np.mean([robot.time_utilization for robot in self.robots])
        side_text.append((f'Total Busy Robots: {total_busy_robot}', COLOR_LIGHT_GREY))
        side_text.append((f'> Robot Time Util (mean): {mean_robot_util * 100:3.0f}%', COLOR_LIGHT_GREY))

        MAX_ROBOT_TO_SHOW = 10
        for temp_robot in self.robots:
            if i_plot >= MAX_ROBOT_TO_SHOW:
                break

            i_plot += 1
            temp_text = f'{temp_robot.name}|'
            temp_text += f'Time Util: {temp_robot.time_utilization * 100:3.0f}%|'
            temp_text += f'In: {temp_robot.total_input_job}|'
            temp_text += f'Out: {temp_robot.total_output_job}|'
            temp_text += f'{temp_robot.state}'[12:]
            side_text.append((temp_text, COLOR_LIGHT_BLUE))

        draw_text_box(screen, side_text, box_pos,
                      top_center=True, align_center=False, show_box=False,
                      max_width=420)

    def draw_entry_box(self, screen, show_text_list, position, max_width=400, max_height=600):
        """
        为 'Entry' 工厂画一个专门的大框
        """
        line_height = 70  # 行高
        padding = 5
        total_height = len(show_text_list) * line_height + padding  # 计算总高度
        regular_font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE)
        bold_font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE, bold=True)
        italic_font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE, italic=True)
        # 如果设置了最大高度，并且总高度超过了最大高度，则设置为最大高度
        if total_height > max_height:
            total_height = max_height

        box_x = position[0] - max_width // 2
        box_y = position[1] + 30  # Adjust position for better visibility

        # 绘制大框和边框
        pygame.draw.rect(screen, COLOR_BLACK, (box_x - 5, box_y - 5, max_width + 10, total_height + 10), 2)

        # 绘制文本内容
        for i, (text, bg_color) in enumerate(show_text_list):
            line_rect = pygame.Rect(box_x, box_y + i * line_height, max_width, line_height)
            pygame.draw.rect(screen, bg_color, line_rect)

            words = text.split(' ')
            x_offset = line_rect.left + 10

            for word in words:
                word_font = regular_font
                word_surface = word_font.render(word, True, COLOR_BLACK)
                word_rect = word_surface.get_rect()
                word_rect.topleft = (x_offset, line_rect.centery - word_rect.height // 2)
                screen.blit(word_surface, word_rect)
                x_offset += word_rect.width + 5


def seconds_to_hhmmss(seconds):
    # Calculate hours, minutes, and seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    # Return in hh:mm:ss format
    return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02}'

# Draw text box function for top center alignment
def draw_text_box(screen, text_lines, position,
                  top_center=True,
                  align_center=True,
                  show_box=True,
                  max_width=200, max_height = None):
    # Create fonts only once for efficiency
    regular_font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE)
    bold_font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE, bold=True)
    italic_font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE, italic=True)

    line_height = 26
    padding = 5
    total_height = len(text_lines) * line_height + padding
    # 如果设置了最大高度，并且总高度超过了最大高度，则设置为最大高度
    if max_height and total_height > max_height:
        total_height = max_height

        # 将文本裁剪为适应框高的内容
        max_lines = max_height // line_height
        text_lines = text_lines[:max_lines]  # 只保留显示框内的行


    # Calculate the top left position to center the text box at the top/bottom center of the Box
    box_x = position[0] - max_width // 2
    box_y = position[1] + 30 if top_center else position[1] - total_height - 40

    # Draw the black border around the text box
    if show_box:
        pygame.draw.rect(screen, COLOR_BLACK, (box_x - 5, box_y - 5, max_width + 10, total_height + 10), 2)

    # Preprocess text and split once per line
    for i, (text, bg_color) in enumerate(text_lines):
        line_rect = pygame.Rect(box_x, box_y + i * line_height, max_width, line_height)
        pygame.draw.rect(screen, bg_color, line_rect)

        # Split the text into words and process bold/italic tags
        words = text.split(' ')
        x_offset = line_rect.left + 10

        for word in words:
            # Check for bold/italic tags once, strip them, and select the correct font
            if word.startswith('**') and word.endswith('**'):
                word = word[2:-2]
                word_font = bold_font
            elif word.startswith('*') and word.endswith('*'):
                word = word[1:-1]
                word_font = italic_font
            else:
                word_font = regular_font

            # Render the word
            word_surface = word_font.render(word, True, COLOR_BLACK)
            word_rect = word_surface.get_rect()

            # Vertically center the word
            word_rect.topleft = (x_offset, line_rect.centery - word_rect.height // 2)

            # Draw the word on the screen
            screen.blit(word_surface, word_rect)

            # Update the x_offset for the next word
            x_offset += word_rect.width + 5

