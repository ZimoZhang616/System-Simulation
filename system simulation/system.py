import simpy
import numpy as np

# Global parameters
NUM_WORKSTATIONS = 5
FORKLIFT_SPEED = 5   # feet per second
THROUGHPUT_GOAL = 120  # jobs per 8-hour day
JOB_ARRIVAL_RATE = 3600 / 25  # Mean interarrival time in hours

# Job details
JOB_TYPES = {
    1: {'operations': [3, 1, 2, 5], 'mean_service_times': [0.25 * 3600, 0.15 * 3600, 0.10 * 3600, 0.30 * 3600]},
    2: {'operations': [4, 1, 3], 'mean_service_times': [0.15 * 3600, 0.20 * 3600, 0.30 * 3600]},
    3: {'operations': [2, 5, 1, 4, 3], 'mean_service_times': [0.15 * 3600, 0.10 * 3600, 0.35 * 3600, 0.20 * 3600, 0.20 * 3600]}
}
# Distance matrix between stations (in feet)
# Station 1 is at index 0, Station 2 at index 1, and so on.
distances = {
    (1, 2): 150, (1, 3): 213, (1, 4): 336, (1, 5): 300, (1, 6): 150,
    (2, 3): 150, (2, 4): 300, (2, 5): 336, (2, 6): 213,
    (3, 4): 150, (3, 5): 213, (3, 6): 150,
    (4, 5): 150, (4, 6): 213,
    (5, 6): 150
}
# Add the reverse distances (symmetrical matrix)
for (i, j), dist in list(distances.items()):
    distances[(j, i)] = dist

class ManufacturingSystem:
    def __init__(self, env, workstation_machines, num_forklifts = 3):  #num_forklifts=3
        self.env = env
        # Initialize workstations with variable number of machines
        self.workstations = [simpy.Resource(env, capacity=workstation_machines[i]) for i in range(len(workstation_machines))]
        self.forklifts = simpy.Resource(env, capacity=num_forklifts)

    def process_job(self, job_type, job_id):
        job_info = JOB_TYPES[job_type]
        for i, (operation, service_time) in enumerate(zip(job_info['operations'], job_info['mean_service_times'])):
            with self.workstations[operation - 1].request() as request:
                yield request
                processing_time = np.random.gamma(2, service_time / 2)
                yield self.env.timeout(processing_time)

                if i < len(job_info['operations']) - 1:
                    next_station = job_info['operations'][i + 1]
                    current_station = operation
                    yield self.env.process(self.move_job(current_station, next_station, job_id))

    def move_job(self, from_station, to_station, job_id):
        """Simulate forklift movement between two stations based on distance."""
        distance = distances.get((from_station, to_station), 0)
        travel_time = distance / FORKLIFT_SPEED
        print(f'Moving job {job_id} from station {from_station} to station {to_station}, distance: {distance} feet, time: {travel_time:.2f} seconds')
        yield self.env.timeout(travel_time)

def handle_job(env, system, job_type, job_id):
    print(f'Time {env.now}: Job {job_id} of type {job_type} arrives')
    yield env.process(system.process_job(job_type, job_id))
    print(f'Time {env.now}: Job {job_id} of type {job_type} completed')

def job_generator(env, system):
    job_count = 0
    while True:
        job_type = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
        env.process(handle_job(env, system, job_type, job_count))
        job_count += 1
        yield env.timeout(np.random.exponential(JOB_ARRIVAL_RATE))

# Set the number of machines at each of the 5 workstations (customizable)
workstation_machines = [3, 3, 3, 3, 3]

# Simulation setup
env = simpy.Environment()
manufacturing_system = ManufacturingSystem(env, workstation_machines, num_forklifts=2)
env.process(job_generator(env, manufacturing_system))

# Run the simulation for one 8-hour shift (28800 seconds)
env.run(until=28800)

