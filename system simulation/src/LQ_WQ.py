
import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('queue_log_40_R_random_W_random_646444.csv', names=['Time', 'Workstation', 'QueueLength'])

# 计算仿真总时间
T = df['Time'].max()

# 这里必须是仿真中实际到达系统的总任务数 (需要你实际仿真数据来确认)
total_jobs_arrived = 255  # 请根据你的仿真实际任务数修改这个数字！

# 到达率 lambda (jobs per second)
arrival_rate = total_jobs_arrived / T

results = []

for ws in sorted(df['Workstation'].unique()):
    ws_df = df[df['Workstation'] == ws].sort_values(by='Time')
    time_values = ws_df['Time'].values
    queue_lengths = ws_df['QueueLength'].values

    # 梯形积分计算LQ
    LQ = np.trapz(queue_lengths, time_values) / T

    # 正确使用Little's Law计算WQ
    WQ = LQ / arrival_rate if arrival_rate > 0 else np.nan

    results.append({
        'Workstation': ws,
        'LQ (Avg Queue Length)': LQ,
        'WQ (Avg Waiting Time per job)': WQ
    })

# 结果输出
df_results = pd.DataFrame(results)
print(df_results.to_string(index=False))
