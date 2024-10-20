# 主流程，运行模拟器
from system_simulator import *
import initial_data



if __name__ == "__main__":
    # 初始化系统模拟器，5个工作站，2台叉车
    simulator = SystemSimulator( 
        initial_data.NUM_WORKSTATIONS,
        initial_data.NUM_MACHINES_IN_WORKSTATION,
        initial_data.NUM_FORKLISTS,
        initial_data.FORKLIFT_SPEED,
        initial_data.distances,
        initial_data.JOB_TYPES,
        initial_data.THROUGHPUT_GOAL,
        initial_data.JOB_ARRIVAL_RATE)
    
    simulator.system_running()
    simulator.system_terminate()

    
    
