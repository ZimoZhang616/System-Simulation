# Global parameters
NUM_WORKSTATIONS = 6
NUM_FORKLISTS = 6
NUM_MACHINES_IN_WORKSTATION = 5
FORKLIFT_SPEED = 5   # feet per second
THROUGHPUT_GOAL = 120  # jobs per 8-hour day
JOB_ARRIVAL_RATE = 25  # Mean interarrival jobs in hours

# Job details
JOB_TYPES = {
    1: {'operations': [5, 2, 0, 1, 4, 5], 'mean_service_times': [0, 0.25 * 3600, 0.15 * 3600, 0.10 * 3600, 0.30 * 3600, 0], 'generate_probability': 0.3},
    2: {'operations': [5, 3, 0, 2, 5], 'mean_service_times': [0, 0.15 * 3600, 0.20 * 3600, 0.30 * 3600, 0], 'generate_probability': 0.5},
    3: {'operations': [5, 1, 4, 0, 3, 2, 5], 'mean_service_times': [0, 0.15 * 3600, 0.10 * 3600, 0.35 * 3600, 0.20 * 3600, 0.20 * 3600, 0], 'generate_probability': 0.2}
}

# Distance matrix between stations (in feet)
# Station 1 is at index 0, Station 2 at index 1, and so on.
distances = {
    (0, 1): 150, (0, 2): 213, (0, 3): 336, (0, 4): 300, (0, 5): 150,
    (1, 2): 150, (1, 3): 300, (1, 4): 336, (1, 5): 213,
    (2, 3): 150, (2, 4): 213, (2, 5): 150,
    (3, 4): 150, (3, 5): 213,
    (4, 5): 150
}
# Add the reverse distances (symmetrical matrix)
for (i, j), dist in list(distances.items()):
    distances[(j, i)] = dist