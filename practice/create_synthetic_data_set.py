"""Script generates synthetic host CPU and memory usage data. using numpy and pandas"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_host_metrics_dataset(num_entries, num_hosts):
    """Generates a synthetic dataset for host CPU and memory usage.
    Args: num_entries (int): The total number of data points (rows) to generate.
        num_hosts (int): The number of unique hosts to simulate.
    Returns:
        pd.DataFrame: A DataFrame containing the synthetic data.
    """
    # 1. Generate Timestamps
    # Start time
    start_time = datetime.now() - timedelta(minutes=num_entries)
    # Generate a time range with a fixed interval (e.g., 1 minute)
    timestamps = [start_time + timedelta(minutes=i) for i in range(num_entries)]

    # 2. Generate Host IDs
    host_ids = [f'host_{i + 1:02d}' for i in range(num_hosts)]
    # Repeat host IDs to match the total number of entries
    hosts = np.random.choice(host_ids, num_entries)

    # 3. Generate CPU Usage (Gaussian/Normal distribution around specific parameters)
    # Simulate different typical CPU usages for different hosts
    cpu_means = {f'host_{i + 1:02d}': np.random.uniform(20, 70) for i in range(num_hosts)}
    cpu_stds = {f'host_{i + 1:02d}': np.random.uniform(5, 15) for i in range(num_hosts)}

    cpu_usage = []
    for host in hosts:
        mean = cpu_means[host]
        std = cpu_stds[host]
        # Generate a value using a normal distribution, clipped between 0 and 100
        value = np.random.normal(mean, std)
        cpu_usage.append(np.clip(value, 0, 100))  # CPU usage is a percentage

    # 4. Generate Memory Usage (Completely random parameters)
    # Using a uniform distribution for simple randomness, clipped between 0 and 100
    memory_usage = np.random.uniform(0, 100, num_entries)  # Memory usage is a percentage

    # 5. Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'host_id': hosts,
        'cpu_usage_percent': cpu_usage,
        'memory_usage_percent': memory_usage
    })

    # Sort by timestamp and host for better time-series representation
    data = data.sort_values(by=['timestamp', 'host_id']).reset_index(drop=True)
    return data

if __name__ == "__main__":
    synthetic_data = create_host_metrics_dataset(num_hosts=10, num_entries=20)
    print(synthetic_data)



