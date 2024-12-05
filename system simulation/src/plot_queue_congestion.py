import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
df = pd.read_csv('queue_log_40_R_random_W_random_646444.csv', names=['Time', 'Workstation', 'QueueLength'])

# 找到所有 Workstation 的编号
workstations = sorted(df['Workstation'].unique())

# 依次为每个 Workstation 生成一张图
for ws in workstations:
    ws_df = df[df['Workstation'] == ws]

    plt.figure(figsize=(8, 5))
    plt.plot(ws_df['Time'], ws_df['QueueLength'], label=f'Workstation {ws}', color='b')

    # 设置标题和标签
    plt.xlabel('Time (s)')
    plt.ylabel('Queue Length')
    plt.title(f'Queue Congestion - Workstation {ws}')
    plt.legend()
    plt.grid(True)

    # 保存单独的图像
    plt.savefig(f'queue_congestion_ws{ws}_40_R_distance_W_fifo_646444.png')
    plt.close()  # 关闭当前图，防止占用过多内存

print("✅ Successfully saved individual queue congestion plots for each Workstation.")
