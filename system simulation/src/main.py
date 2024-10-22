from global_def import *
from device import *
from gui import *
import threading

# Global pointer
g_factory = Factory(name='Entry', pos=(0, 0))
g_job_times, g_jobs = generate_all_jobs(max_job_num=MAX_JOB_NUM,
                                        job_arrival_rate=JOB_ARRIVAL_RATE,
                                        seed=JOB_GENERATE_SEED)
g_factory.set_jobs(g_job_times, g_jobs)


# Backend system logic (time-critical)
def backend_system():
    while True:

        # Stop the backend if the maximum running time is reached
        if g_factory.total_run_time >= TOTAL_BACKEND_RUN_TIME:
            print(f"Backend stopped after {g_factory.total_run_time:.2f} seconds.")
            break

        # Loop update
        g_factory.update()
        time.sleep(BACKEND_CYCLE_TIME / BACKEND_SPEED_RATIO)


# Starting both threads
if __name__ == "__main__":
    # Create the backend thread
    backend_thread = threading.Thread(target=backend_system)
    backend_thread.daemon = True  # Ensure the backend stops when the main program exits
    backend_thread.start()

    # Run the frontend GUI in the main thread
    gui = GraphicUserInterface(factory=g_factory)
    gui.run()
    gui.stop()
