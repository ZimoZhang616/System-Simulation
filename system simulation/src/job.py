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
        self.arrival_time = 0
        self.interarrival_time = 0

        # Job routing
        self.routing_list = JOB_ROUTING[self.type]  # 路线列表，如 [3, 1, 2, 5]
        self.routing_workstation_list = []

        # Calculate the job service time (Sample from the gamma distribution)
        self.service_time_list = [np.random.gamma(shape=JOB_TIME_GAMMA,
                                                  scale=JOB_TIME_MEAN[self.type][i_routine] / JOB_TIME_GAMMA)
                                  for i_routine in range(len(self.routing_list))]

        self.total_service_time = sum(self.service_time_list)

        self.total_transport_time = self.cal_total_transport() / ROBOT_SPEED

        self.total_process_time = self.total_transport_time + self.total_service_time
        # Current state
        self.state = JobState.NotExist
        self.pos = (0, 0)

        self.curr_routing_index = 0  # 当前正在处理的ROUTING索引
        self.curr_workstation = None
        self.next_workstation = None

        self.start_time = None
        self.end_time = None
        self.total_busy_time = None

    def cal_total_transport(self):
        total_dis = 0
        for i in range(len(self.routing_list) + 1):
            if i == 0:
                total_dis += self.calculate_distance(FACTORY_POS, WORKSTATION_POS[self.routing_list[i] - 1])[2]
                continue
            elif i == len(self.routing_list):
                total_dis += self.calculate_distance(FACTORY_POS, WORKSTATION_POS[self.routing_list[i - 1] - 1])[2]
                continue
            total_dis += self.calculate_distance(WORKSTATION_POS[self.routing_list[i - 1] - 1],
                                                 WORKSTATION_POS[self.routing_list[i] - 1])[2]

        return total_dis

    def calculate_distance(self, pos_start, pos_end):
        """Calculate Euclidean distance between two points (x1, y1) and (x2, y2)."""
        return (pos_end[0] - pos_start[0],
                pos_end[1] - pos_start[1],
                ((pos_end[0] - pos_start[0]) ** 2 + (pos_end[1] - pos_start[1]) ** 2) ** 0.5)

    def next_routing(self):
        '''
        当JOB离开当前Station时调用
        :return:
        '''
        # self.duration = time.time() - self.start_time
        self.curr_routing_index += 1

        # Proceed job to its next target
        if self.curr_routing_index == len(self.routing_list):
            self.next_workstation = self.parent  # return to factory
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
            weights=JOB_GENERATE_PROBABILITY  # 从job_types中提取生成概率
        )[0]
        new_job = Job(parent=None, index=i,
                      name=f'J{i + 1}', job_type=job_type)
        new_job.arrival_time = current_time
        new_job.interarrival_time = interarrival_time

        time_list.append(current_time)
        job_list.append(new_job)

    return time_list, job_list


if __name__ == '__main__':
    'Below: Input Analysis'

    import matplotlib.pyplot as plt
    import numpy as np
    import scipy.stats as stats
    import random
    from scipy.stats import chisquare

    PLOT_W = 2.8
    PLOT_H = 2.2


    '''
    Testify Random ness in Python
    '''

    # Generate random numbers
    seed = JOB_GENERATE_SEED
    random.seed(seed)
    random_numbers = [random.random() for _ in range(100000)]
    print('mean', np.mean(random_numbers))
    print('median', np.median(random_numbers))
    print('std', np.std(random_numbers))

    NUM_BINS = 16

    plt.figure(figsize=(PLOT_W, PLOT_H))

    # Plot the histogram
    plt.hist(random_numbers, bins=NUM_BINS,
             edgecolor='black', color='#4c72b0', alpha=0.7)

    # Add titles and labels
    plt.title('Random Numbers')
    plt.xlabel('Value')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig('./../temp/Random Numbers.png')

    # Divide the range [0, 1) into 10 bins
    bins = [i / NUM_BINS for i in range(NUM_BINS+1)]
    observed_counts = [0] * NUM_BINS

    for number in random_numbers:
        for i in range(NUM_BINS):
            if bins[i] <= number < bins[i + 1]:
                observed_counts[i] += 1
                break

    # Chi-square test
    expected_count = len(random_numbers) / NUM_BINS
    chi2_stat, p_value = chisquare(observed_counts, [expected_count] * NUM_BINS)

    print(f"Chi-square Statistic: {chi2_stat}")
    print(f"P-value: {p_value}")

    if p_value > 0.05:
        print("The random number generator passed the test (uniform distribution).")
    else:
        print("The random number generator failed the test (non-uniform distribution).")

    '''
    QQ-plot
    '''

    fig, ax = plt.subplots(figsize=(PLOT_W, PLOT_H))


    # Create a QQ plot comparing to a uniform distribution
    stats.probplot(random_numbers, dist="uniform", plot=plt)

    # Display the plot
    plt.title('Q-Q Plot')
    plt.xlabel('Theoretical Quantiles')
    plt.ylabel('Sample Quantiles')

    # Change the scatter color
    # Change the color of the scatter points in the Q-Q plot
    line = ax.get_lines()[0]  # Access the first line (scatter plot)
    line.set_markerfacecolor('#4c72b0')  # Set the face color of scatter points
    line.set_markeredgecolor('none')  # Set the edge color of scatter points


    plt.tight_layout()
    plt.savefig('./../temp/Random Numbers - QQ plot.png')

    ''' 
    ---------->  Generate Jobs !
    '''

    g_job_times, g_jobs = generate_all_jobs(max_job_num=MAX_JOB_NUM,
                                            job_arrival_rate=JOB_ARRIVAL_RATE,
                                            seed=JOB_GENERATE_SEED)
    print(f'job_times len: {len(g_job_times)}'
          f', mean: {np.mean(g_job_times)}')

    '''
    ----------> Histogram of Interarrival Time
    '''
    # Extract interarrival_time values
    interarrival_times = [job.interarrival_time for job in g_jobs]
    print(f'interarrival_times mean: {np.mean(interarrival_times)}')
    print(f'interarrival_times median: {np.median(interarrival_times)}')
    print(f'interarrival_times std: {np.std(interarrival_times)}')

    # Create the histogram with 10 bins (bars)
    plt.figure(figsize=(PLOT_W, PLOT_H))

    NUM_BINS = 15
    plt.hist(interarrival_times, bins=NUM_BINS,
             edgecolor='black', color='#4c72b0', alpha=0.7)

    # Add labels and title
    plt.xlabel('Interarrival Time (s)')
    plt.ylabel('Frequency')
    plt.title('Job Interarrival Time')

    # Save the plot
    plt.tight_layout()
    plt.savefig('./../temp/hist_interarrival_time.png')

    '''
    ----------> Arrive Time
    '''

    # Extract interarrival_time values
    job_id = [job.index + 1 for job in g_jobs]
    arrive_time = [job.arrival_time for job in g_jobs]
    print(f'arrive_time mean: {np.mean(arrive_time)}')


    # Create the histogram with 10 bins (bars)
    plt.figure(figsize=(PLOT_W, PLOT_H))
    plt.scatter(arrive_time, job_id,
                marker='.',
                s=5,
                color='#4c72b0', alpha=0.7)

    # Add labels and title
    plt.xlabel('Total Time (s)')
    plt.ylabel('Job Count')
    plt.title('Total Input Job vs Time')

    # Save the plot
    plt.tight_layout()
    plt.savefig('./../temp/job_count_vs_time.png')

    '''
    ----------> QQ plot for Arrive Time
    '''

    fig, ax = plt.subplots(figsize=(PLOT_W, PLOT_H))

    # Generate a Q-Q plot to compare the sample data with an exponential distribution
    res = stats.probplot(interarrival_times, dist="expon", plot=plt)

    # Change the scatter color
    # Change the color of the scatter points in the Q-Q plot
    line = ax.get_lines()[0]  # Access the first line (scatter plot)
    line.set_markerfacecolor('#4c72b0')  # Set the face color of scatter points
    line.set_markeredgecolor('none')  # Set the edge color of scatter points

    # Customize the plot
    plt.title('Q-Q Plot')
    plt.xlabel('Theoretical Quantiles')
    plt.ylabel('Sample Quantiles')

    # Save the plot
    plt.tight_layout()
    plt.savefig('./../temp/qq_plot_interarrival_time.png')

    '''
    ----------> Chi-Square Test for arrival time
    '''
    # Step 1: Define the bins (you can adjust this depending on your data)
    bins = np.linspace(0, max(interarrival_times), NUM_BINS + 1)
    # Step 2: Calculate the observed frequencies (histogram of data)
    observed_frequencies, _ = np.histogram(interarrival_times, bins)

    # Step 3: Calculate the expected frequencies under an exponential distribution
    lambda_est = 1 / np.mean(interarrival_times)  # Estimate lambda (1 / mean)
    expected_frequencies = len(interarrival_times) * (
                stats.expon.cdf(bins[1:], scale=1 / lambda_est) - stats.expon.cdf(bins[:-1], scale=1 / lambda_est))

    # Step 3.1: Normalize expected frequencies to match the sum of observed frequencies
    expected_frequencies *= observed_frequencies.sum() / expected_frequencies.sum()

    # Step 4: Apply the Chi-Square Test
    chi_squared_stat, p_value = stats.chisquare(observed_frequencies, expected_frequencies)

    # Output the results
    print(f"Chi-Square Statistic: {chi_squared_stat}")
    print(f"P-Value: {p_value}")

    # Interpretation:
    if p_value < 0.05:
        print("The data does not follow an exponential distribution (reject null hypothesis).")
    else:
        print("The data follows an exponential distribution (fail to reject null hypothesis).")


    '''
    ----------> Job Types Pie chart
    '''
    from collections import Counter
    
    # Step 1: Extract job types from the job_list
    job_types = [job.type for job in g_jobs]

    # Step 2: Count the occurrences of each type
    type_counts = Counter(job_types)

    # Step 3: Create a pie chart
    labels = type_counts.keys()
    labels = [f'Type {label+1}' for label in labels]
    sizes = type_counts.values()
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']  # Add more colors if needed

    # Plot the pie chart
    fig, ax = plt.subplots(figsize=(PLOT_W, PLOT_H))

    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)

    # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.axis('equal')

    # Title of the plot
    plt.title('Job Type Distribution')

    # Save the plot
    plt.tight_layout()
    plt.savefig('./../temp/job_type_pie_chart.png')


    '''
    ----------> Chi-Square Test for arrival time
    '''

    # Step 1: Extract job types from the job_list
    job_types = [job.type for job in g_jobs]

    # Step 2: Count the observed frequencies for each job type
    observed_frequencies = Counter(job_types)
    types = [0, 1, 2]

    # Ensure all types are included in the observed frequencies, even if some types have 0 counts
    observed_frequencies = {key: observed_frequencies.get(key, 0) for key in types}

    # Step 3: Calculate the expected frequencies based on initial probabilities
    initial_probabilities = [0.3, 0.5, 0.2]
    total_jobs = len(g_jobs)
    expected_frequencies = [p * total_jobs for p in initial_probabilities]

    # Step 4: Perform the Chi-Square test
    observed_values = list(observed_frequencies.values())
    chi2_stat, p_value = stats.chisquare(observed_values, expected_frequencies)

    # Step 5: Output the results
    print("Observed Frequencies:", observed_values)
    print("Expected Frequencies:", expected_frequencies)
    print("Chi-Square Statistic:", chi2_stat)
    print("P-Value:", p_value)

    # Step 6: Conclusion based on p-value
    if p_value < 0.05:
        print("The observed distribution does not match the expected distribution (reject H0).")
    else:
        print("The observed distribution matches the expected distribution (fail to reject H0).")


    '''
    ----------> Hist Plot for job service time
    '''
    # Define scale for job.type == 1 (mean for Gamma distribution)
    scale_parameter = 2  # Example scale for job.type == 1
    shape_parameter = 2  # Given shape parameter for the Gamma distribution

    # Step 1: Filter job list for job.type == 1
    job_type_1_list = [job for job in g_jobs if job.type == 1]

    # Step 2: Simulate the service times using the Gamma distribution
    # the second in the list (which is the
    service_times = [job.service_time_list[1] for job in job_type_1_list]
    expected_service_times = 3600 * 0.2

    print('service time mean:', np.mean(service_times))
    print('service time median:', np.median(service_times))
    print('service time stddev:', np.std(service_times))

    # Step 3: Visualize the service times
    fig, ax = plt.subplots(figsize=(PLOT_W, PLOT_H))

    plt.hist(service_times, bins=NUM_BINS,
             edgecolor='black', color='#4c72b0', alpha=0.7)

    plt.title('Service Time Distribution')
    plt.xlabel('Service Time (s)')
    plt.ylabel('Frequency')

    plt.tight_layout()
    plt.savefig('./../temp/job_service_time.png')

    '''
    ----------> Chi-Square Test for job service time
    '''

    # Step 4: Perform Chi-Square Test
    observed_frequencies, bin_edges = np.histogram(service_times, bins=NUM_BINS)

    # Step 5: Calculate the expected frequencies based on the Gamma distribution
    shape_parameter = 2
    scale_parameter = expected_service_times / shape_parameter  # Using mean as a reference for scale

    # Generate expected frequencies using Gamma distribution
    # The number of bins * number of samples must match total number of jobs in job_type_1_list
    total_jobs = len(job_type_1_list)
    expected_frequencies = np.zeros(NUM_BINS)

    # Generate expected frequencies for the same bin edges
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # Calculate bin centers
    expected_frequencies = len(service_times) * stats.gamma.cdf(bin_edges[1:], shape_parameter, scale=scale_parameter) - \
                           len(service_times) * stats.gamma.cdf(bin_edges[:-1], shape_parameter, scale=scale_parameter)

    # Step 6: Normalize the expected frequencies to match the total count of jobs
    expected_frequencies /= np.sum(expected_frequencies)  # Normalize to total count of jobs
    expected_frequencies *= np.sum(observed_frequencies)  # Scale to match the total count


    # Step 6: Run the Chi-Square test
    chi2_stat, p_value = stats.chisquare(observed_frequencies, expected_frequencies)

    # Step 7: Print the Chi-Square test result
    print(f"Chi-Square Statistic: {chi2_stat}")
    print(f"P-Value: {p_value}")

    # Interpretation
    if p_value < 0.05:
        print("The data does not follow the expected Gamma distribution (reject H0).")
    else:
        print("The data follows the expected Gamma distribution (fail to reject H0).")
