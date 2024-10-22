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
    Halted = 2  # loaded, but could not move,  例如：车上有货，但是没地方去；机器生产完成，但是无法卸货
    Waiting = 3  # loaded, waiting to be unloaded, with tasks assigned


class Device:
    def __init__(self, parent=None, index=0, name='', pos=(0, 0)):
        self.parent = parent  # parent node
        self.index = index  # index
        self.name = name  # device name
        self.pos = pos  # position in real-word unit

        # current state
        self.state = DeviceState.Idle
        self.is_loaded = False  # if the device is loaded with job/item

        # timing
        self.total_run_time = 0  # total time since init
        self.curr_busy_time = 0  # busy time of current job
        self.total_idle_time = 0
        self.total_busy_time = 0
        self.total_halt_time = 0
        self.total_wait_time = 0
        self.time_utilization = 0  # total_busy_time / total_run_time

        # input queue
        self.input_queue = []
        self.input_queue_len = 0
        self.input_job_count = [0 for i_tmp in range(NUM_JOB_TYPES)]  # count of all input jobs
        self.total_input_job = 0

        # output queue
        self.output_queue = []
        self.output_queue_len = 0
        self.output_queue_count = [0 for i_tmp in range(NUM_JOB_TYPES)]  # count of all output jobs
        self.total_output_job = 0

    def update_time(self):  # update the device timing
        self.total_run_time += BACKEND_CYCLE_TIME

        if self.state == DeviceState.Busy:
            self.curr_busy_time += BACKEND_CYCLE_TIME
            self.total_busy_time += BACKEND_CYCLE_TIME
        elif self.state == DeviceState.Halted:
            self.total_halt_time += BACKEND_CYCLE_TIME
        elif self.state == DeviceState.Waiting:
            self.total_wait_time += BACKEND_CYCLE_TIME
        else:
            self.total_idle_time += BACKEND_CYCLE_TIME

        self.time_utilization = self.total_busy_time / self.total_run_time if self.total_run_time else 0.0

    def push_job(self, job):
        pass

    def pop_job(self, job=None):
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
            self.state = DeviceState.Halted  # item still in the machine, waiting robot to move out
            self.curr_busy_time = 0
            self.curr_job.state = JobState.Halted  # <--------------- JobState

    def push_job(self, job):
        '''

        :param job: the target job
        :return:
            RTN_ERR: 失败，则忽略该Job
            RTN_OK: 成功，则立即开始生产
        '''
        if self.state != DeviceState.Idle:
            return RTN_ERR

        job.state = JobState.Processing  # <--------------- JobState
        job.curr_machine = self

        self.curr_job = job
        self.curr_job_time = job.service_time_list[job.curr_routing_index]

        self.state = DeviceState.Busy
        self.curr_busy_time = 0
        self.is_loaded = True

        # record
        self.input_job_count[self.curr_job.type] += 1
        self.total_input_job += 1

        return RTN_OK

    def pop_job(self, job=None):
        if self.state != DeviceState.Waiting:
            return RTN_ERR

        # record
        self.output_queue_count[self.curr_job.type] += 1
        self.total_output_job += 1

        self.curr_job = None
        self.curr_job_time = 0

        self.state = DeviceState.Idle
        self.curr_busy_time = 0
        self.is_loaded = False

        return RTN_OK

    def get_show_text(self):
        if self.state == DeviceState.Busy:
            percentage_complete = int((self.curr_job_time / self.curr_job_time) * 100)
            return f'{self.name}: Busy {percentage_complete:2d}%', COLOR_GREEN
        elif self.state == DeviceState.Halted:
            return f'{self.name}: Halt', COLOR_RED
        elif self.state == DeviceState.Waiting:
            return f'{self.name}: Wait', COLOR_ORANGE
        else:
            return f'{self.name}: Idle', COLOR_YELLOW


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

    def update(self):
        self.update_time()

        # update machine states
        for machine in self.machines:
            if machine.state == DeviceState.Idle and self.input_queue_len > 0:
                temp_job = self.input_queue.pop()
                self.input_queue_len = len(self.input_queue)
                machine.push_job(temp_job)
            machine.update()

        # curr state:
        if any(machine.state == DeviceState.Busy for machine in self.machines):
            self.state = DeviceState.Busy
        else:
            self.state = DeviceState.Idle

        # timing
        # use mean time of utilization of all machines
        self.time_utilization = np.mean([machine.time_utilization for machine in self.machines])

    def push_job(self, job):
        job.state = JobState.Queueing  # <--------------- JobState
        job.curr_workstation = self

        self.input_queue.append(job)
        self.input_queue_len = len(self.input_queue)

        # record
        self.input_job_count[job.type] += 1
        self.total_input_job += 1
        return RTN_OK

    def pop_job(self, job=None):
        # record
        self.output_queue_count[job.type] += 1
        self.total_output_job += 1
        return RTN_OK

    def draw(self, screen):

        # Create text to be showed on screen
        show_text_list = [(f'{self.name}', COLOR_LIGHT_GREY)]

        # Add machine info to the text
        for machine in self.machines:
            status_text, color = machine.get_show_text()
            show_text_list.append((status_text, color))

        # Display the mean busy ratio of the machines in this workstation
        show_text_list.append((f'Time Util:{self.time_utilization * 100:3.0f}%', COLOR_LIGHT_BLUE))
        show_text_list.append((f'Output: {self.total_output_job}', COLOR_LIGHT_BLUE))
        show_text_list.append((f'Queue: {self.input_queue_len}', COLOR_LIGHT_BLUE))

        # Draw the text box at the designated position
        box_pos = map_to_screen(self.pos)
        if self.pos[1] > 0:  # For top workstations, bottom center aligned
            draw_text_box(screen, show_text_list, box_pos, top_center=False)
        else:  # For lower workstations, top center aligned
            draw_text_box(screen, show_text_list, box_pos, top_center=True)


class Robot(Device):
    def __init__(self, parent=None, index=0, name='', pos=(0, 0)):
        super().__init__(parent, index, name, pos)

        self.speed = ROBOT_SPEED

        self.curr_job = None
        self.pick_up_machine = None  # 收货位置（从machine上收货）
        self.deliver_workstation = None  # 送货位置（向work station送货）
        self.target_pos = (0, 0)  # 当前目标

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
                self.pick_up_machine.pop_job(self.curr_job)
                self.curr_job.state = JobState.Transporting  # <--------------- JobState
                self.is_loaded = True

            # 载货跑 -> 去送货 -> IDLE
            else:
                self.state = DeviceState.Idle
                self.pop_job(self.curr_job)
                self.target_workstation.push_job(self.curr_job)
                self.is_loaded = False

        else:  # not arrived
            self.state = DeviceState.Busy
            distance_travelled = self.speed * BACKEND_CYCLE_TIME
            travel_fraction = distance_travelled / dist
            self.pos = (self.pos[0] + dx * travel_fraction, self.pos[1] + dy * travel_fraction)
            self.total_distance_travelled += distance_travelled
            self.distance_travelled_pct = min(self.distance_travelled_pct + travel_fraction * 100, 100)  # Cap at 100%

    def push_job(self, job):
        '''

        :param job:
        :return:
            RTN_ERR: 不接受当前任务
            RTN_OK: 接受任务后，立即启动
        '''
        if self.state != DeviceState.Idle:
            return RTN_ERR

        self.curr_job = job
        self.state = DeviceState.Busy
        self.curr_busy_time = 0

        self.pick_up_machine = job.curr_machine
        self.deliver_workstation = job.next_workstation
        self.target_pos = self.pick_up_machine.pos

        # record
        self.input_job_count[job.type] += 1
        self.total_input_job += 1

        return RTN_OK

    def pop_job(self, job=None):
        self.curr_job = None
        self.state = DeviceState.Idle
        self.curr_busy_time = 0

        self.pick_up_machine = None
        self.deliver_workstation = None
        self.target_pos = (0, 0)

        self.is_loaded = False

        # record
        self.output_queue_count[job.type] += 1
        self.total_output_job += 1

        return RTN_OK

    def draw(self, screen):
        font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE)

        color = COLOR_GREEN if self.state == DeviceState.Busy else COLOR_YELLOW
        screen_pos = map_to_screen(self.pos)

        pygame.draw.circle(screen, color, screen_pos, ROBOT_DIAMETER // 2)

        # show name
        robot_mark_text = font.render(f'{self.name}', True, COLOR_BLACK)
        screen.blit(robot_mark_text, (screen_pos[0] - 8, screen_pos[1] - 8))

        # show percentage
        percentage_text = font.render(f'{int(self.distance_travelled_pct)}%', True, COLOR_BLACK)
        screen.blit(percentage_text, (screen_pos[0] - 15, screen_pos[1] - 35))


class Factory(Device):
    """
    One Factory is composed of several workstations, several robots, and the input/output ports
    """

    def __init__(self, parent=None, index=0, name='', pos=(0, 0)):
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
                             pos=(0, 0))
                       for i_robot in range(self.num_robots)]

        # all jobs
        self.job_times = []
        self.jobs = []
        self.curr_job_index = 0
        self.total_num_jobs = 0

        self.is_job_alive = []

    def set_jobs(self, job_times, jobs):
        self.job_times = job_times
        self.jobs = jobs
        for job in self.jobs:
            job.routing_workstation_list = [self.workstations[job.routing_list[i_routine] - 1]
                                            for i_routine in range(len(job.routing_list))]
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

    def run_my_policy(self):
        # TODO
        # policy R_1: Robot-oriented, target is to maximize the robot utilization
        # policy M_1: Machine-oriented, target is to maximize the machine/workstation utilization,
        #           or minimize queue delays
        # policy J_1: Job-oriented, target is to minimize the job queueing/waiting time
        #           or maximize job throughput

        # Robot-oriented policy: Maximize robot utilization
        if POLICY_NAME == 'R1':
            for robot in self.robots:
                if robot.state == DeviceState.Idle:
                    # Find the closest workstation with jobs in the output queue
                    closest_workstation = None
                    min_distance = float('inf')
                    for workstation in self.workstations:
                        if workstation.output_queue_len > 0:
                            # Calculate distance between robot and workstation
                            dx, dy, distance = calculate_distance(robot.pos, workstation.pos)
                            if distance < min_distance:
                                min_distance = distance
                                closest_workstation = workstation

                    # If a workstation with jobs is found, move the robot to pick up the job
                    if closest_workstation:
                        robot.target_workstation = closest_workstation
                        robot.state = DeviceState.Busy
                        print(f"Robot {robot.name} assigned to transport job from {closest_workstation.name}")

        # Machine-oriented policy: Maximize machine/workstation utilization
        elif POLICY_NAME == 'M1':
            for workstation in self.workstations:
                for machine in workstation.machines:
                    if machine.state == DeviceState.Idle and workstation.input_queue_len > 0:
                        # Assign the next job in the queue to the idle machine
                        next_job = workstation.input_queue.pop(0)
                        machine.push_job(next_job)
                        print(
                            f"Job {next_job.index} assigned to Machine {machine.name} in Workstation {workstation.name}")

        # Job-oriented policy: Minimize job queueing/waiting time
        elif POLICY_NAME == 'J1':
            # Prioritize jobs that have been in the queue the longest
            for workstation in self.workstations:
                if workstation.input_queue_len > 0:
                    # Assign jobs from workstations with the longest queue to available robots
                    longest_waiting_job = None
                    longest_queue_workstation = None
                    max_queue_len = 0
                    for ws in self.workstations:
                        if ws.input_queue_len > max_queue_len:
                            max_queue_len = ws.input_queue_len
                            longest_waiting_job = ws.input_queue[0]
                            longest_queue_workstation = ws

                    # Find an idle robot to transport the job
                    for robot in self.robots:
                        if robot.state == DeviceState.Idle:
                            robot.target_workstation = longest_queue_workstation
                            robot.state = DeviceState.Busy
                            print(
                                f"Robot {robot.name} transporting job {longest_waiting_job.index} from {longest_queue_workstation.name}")
                            break

        elif POLICY_NAME == 'K1':
            for robot in self.robots:
                if robot.state == DeviceState.Idle:
                    stalled_jobs = [self.jobs[i_job]
                                    for i_job in range(self.total_num_jobs)
                                    if self.is_job_alive[i_job] is True
                                    and self.jobs[i_job].state == JobState.Halted]
                    if len(stalled_jobs) > 0:
                        temp_job = random.choice(stalled_jobs)
                        temp_job.state = DeviceState.Waiting
                        robot.push_job(temp_job)

        elif POLICY_NAME == 'NA':
            pass
        else:
            raise ValueError(f'POLICY_NAME {POLICY_NAME} not recognized')

    def update(self):
        self.update_time()

        # 随机产生新的job
        new_jobs = self.generate_job()
        for job in new_jobs:
            self.push_job(job)

        # update all workstations
        for workstation in self.workstations:
            workstation.update()

        # update all robots
        for robot in self.robots:
            robot.update()

        # Run user-defined policy
        self.run_my_policy()

    def push_job(self, job):
        job.state = JobState.Halted
        self.input_queue.append(job)
        self.input_queue_len = len(self.input_queue)

        self.is_job_alive[job.index] = True

        # record
        self.input_job_count[job.type] += 1
        self.total_input_job += 1
        return RTN_OK

    def pop_job(self, job=None):

        self.is_job_alive[job.index] = False

        # record
        self.output_queue_count[job.type] += 1
        self.total_output_job += 1
        return RTN_OK

    def process_cmd(self, cmd):
        print(f"Processing command: {cmd}")
        pass

    def draw(self, screen):

        # Create text to be showed on screen
        show_text_list = [
            (f'{self.name}', COLOR_LIGHT_GREY),
            (f'Time: {int(self.total_run_time / 60)} min {int(self.total_run_time % 60):2d} sec', COLOR_LIGHT_BLUE),
            (f'Output: {self.total_output_job}', COLOR_LIGHT_BLUE),
            (f'Output: {self.total_output_job / self.total_run_time * 3600:.1f} /h', COLOR_LIGHT_BLUE),
            (f'Input: {self.total_input_job / self.total_run_time * 3600:.1f} /h', COLOR_LIGHT_BLUE),
            (f'(In-Out): {self.total_input_job - self.total_output_job}', COLOR_LIGHT_BLUE),
            (f'Queue: {int(self.input_queue_len)}', COLOR_LIGHT_BLUE)
        ]

        # Draw the text box at the designated position, top center aligned
        box_pos = map_to_screen(self.pos)
        draw_text_box(screen, show_text_list, box_pos, top_center=True)

        for workstation in self.workstations:
            workstation.draw(screen)

        for robot in self.robots:
            robot.draw(screen)


# Draw text box function for top center alignment
def draw_text_box(screen, text_lines, position, top_center=True):
    font = pygame.font.SysFont(FONT_FAMILY, FONT_SIZE)

    max_width = 200
    line_height = 30
    padding = 10

    total_height = len(text_lines) * line_height + padding

    # Calculate the top left position to center the text box at the top/bottome center of the Box
    if top_center:
        box_x = position[0] - max_width // 2
        box_y = position[1]  # Align the top of the text box with the position
    else:
        box_x = position[0] - max_width // 2
        box_y = position[1] - total_height  # Align the bottom of the text box with the position

    # Draw the black border around the text box
    pygame.draw.rect(screen, COLOR_BLACK, (box_x - 5, box_y - 5, max_width + 10, total_height + 10), 2)

    # Draw the text with background colors for each line and center the text
    for i, (text, bg_color) in enumerate(text_lines):
        line_surface = font.render(text, True, COLOR_BLACK)
        line_rect = pygame.Rect(box_x, box_y + i * line_height, max_width, line_height)
        pygame.draw.rect(screen, bg_color, line_rect)
        # Center the text inside the line
        text_rect = line_surface.get_rect(center=(line_rect.centerx, line_rect.centery))
        screen.blit(line_surface, text_rect)
