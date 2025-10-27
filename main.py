import re
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats  # Importing the stats module from scipy

def create_offset_plot(data, device_name):
    return create_plot(data, device_name, "Offset")

def create_delay_plot(data, device_name):
    return create_plot(data, device_name, "Delay")

def create_plot(data, device_name, plot_type):
    filename = f"plots/{device_name.lower()}-{plot_type.lower()}.png"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    max_value = np.max(data)
    min_value = np.min(data)

    plt.figure(figsize=(8, 6))
    plt.plot(data, color='red')
    plt.title(f"{device_name} {plot_type}")
    plt.xlabel("Sample Number")
    plt.ylabel("Value (nanoseconds)")
    plt.ylim(min_value, max_value)
    plt.grid()
    plt.savefig(filename)
    plt.close()

def run_shapiro_wilk(data, label):
    """Runs the Shapiro-Wilk Test and prints the results."""
    if len(data) < 3:  # Shapiro-Wilk requires a minimum of 3 samples
        print(f"\t  Not enough data to perform Shapiro-Wilk test for {label}.")
        return
    
    stat, p_value = stats.shapiro(data)
    print(f"\t  Shapiro-Wilk Test for {label}:")
    print(f"\t    Statistic: {stat:.4f}, p-value: {p_value:.4f}")
    
    if p_value > 0.05:
        print("\t    Sample appears to be normally distributed.")
    else:
        print("\t    Sample does NOT appear to be normally distributed.")

def run_mannwhiteneyu_test(data1, data2, label):
    stat, p_value = stats.mannwhitneyu(data1, data2)
    print(f"\t  Mann-Whitney U Test for {label}:")
    print(f"\t    Statistic: {stat:.4f}, p-value: {p_value:.4f}")
    alpha = 0.05
    if p_value < alpha:
        print('Reject Null Hypothesis (Significant difference between two samples)')
    else:
        print('Do not Reject Null Hypothesis (No significant difference between two samples)')

def parse_file(path: str, name: str) -> tuple[np.ndarray, np.ndarray] | None:
    with open(path, 'r') as file:
        lines = file.readlines()

    re_pattern = re.compile(
        r"""ptp4l\[\d+\]: ptp4l\[\d+.\d+\]: master offset\s+([+-]?\d+)\s+s2 freq\s+([+-]?\d+)\s+path delay\s+(\d+)"""
    )

    offsets = []
    delays = []

    for line in lines:
        match = re_pattern.search(line)
        if match:
            offset = match.group(1)
            frequency = match.group(2)
            path_delay = match.group(3)
            offsets.append(float(offset))
            delays.append(float(path_delay))

    if offsets and delays:
        offset_data = np.array(offsets)
        delay_data = np.array(delays)

        print(f"\tOffset Stats:")
        print(f"\t  Mean: {np.mean(offset_data):.2f}")
        print(f"\t  Min: {np.min(offset_data):.2f}")
        print(f"\t  Max: {np.max(offset_data):.2f}")
        print(f"\t  Std Dev: {np.std(offset_data):.2f}")
        run_shapiro_wilk(offset_data, "Offsets")  # Running Shapiro-Wilk Test on offsets
        create_offset_plot(offset_data, name)

        print(f"\n\tDelay Stats:")
        print(f"\t  Mean: {np.mean(delay_data):.2f}")
        print(f"\t  Min: {np.min(delay_data):.2f}")
        print(f"\t  Max: {np.max(delay_data):.2f}")
        print(f"\t  Std Dev: {np.std(delay_data):.2f}")
        run_shapiro_wilk(delay_data, "Delays")  # Running Shapiro-Wilk Test on delays
        create_delay_plot(delay_data, name)

        return offset_data, delay_data
    else:
        print("No valid offset or delay data found.")
        return None

def main(control_path, experimental_path=None):
    control_machines = [
        ("Beta", os.path.join(control_path, "beta.log")),
        ("Charlie", os.path.join(control_path, "charlie.log")),
        ("Delta", os.path.join(control_path, "delta.log")),
        ("Echo", os.path.join(control_path, "echo.log")),
    ]

    control_offset_data = {}
    control_delay_data = {}

    for name, path in control_machines:
        print(name)
        try:
            offset, delay = parse_file(path, name)
            control_offset_data[name] = offset
            control_delay_data[name] = delay
            print("")
        except Exception as err:
            print(f"[{name}] Error: {err}")

    if experimental_path is not None:
        experimental_offset_data = {}
        experimental_delay_data = {}

        experimental_machines = [
            ("Beta", os.path.join(experimental_path, "beta.log")),
            ("Charlie", os.path.join(experimental_path, "charlie.log")),
            ("Delta", os.path.join(experimental_path, "delta.log")),
            ("Echo", os.path.join(experimental_path, "echo.log")),
        ]

        for name, path in experimental_machines:
            print(name)
            try:
                offset, delay = parse_file(path, name)
                experimental_offset_data[name] = offset
                experimental_delay_data[name] = delay
                print("")
            except Exception as err:
                print(f"[{name}] Error: {err}")

        for name in control_offset_data.keys():
            print(f"Comparing Control vs Experimental for {name} Offsets:")
            print()
            run_mannwhiteneyu_test(control_offset_data[name], experimental_offset_data[name], f"{name} Offsets")
            print("")
            print(f"Comparing Control vs Experimental for {name} Delays:")
            run_mannwhiteneyu_test(control_delay_data[name], experimental_delay_data[name], f"{name} Delays")
            print("")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 4 or len(sys.argv) < 2:
        print("Usage: python main.py <control> [experimental]")
        sys.exit(1)

    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main(sys.argv[1], sys.argv[2])