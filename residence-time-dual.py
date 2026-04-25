from scapy.all import rdpcap, UDP
import sys
import statistics
import matplotlib.pyplot as plt

PTP_EVENT_PORT = 319
PTP_GENERAL_PORT = 320

def plot_corrections_combined(all_values, labels):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    fig.suptitle("PTP Residence Time Per Packet", fontsize=14)
    i = 0

    for ax, values, label in zip(axes, all_values, labels):
        if i == 0:
            label = 'Control (No Encryption)'
        else:
            label = 'SHA-256 (Encrypted)'
            
        ax.plot(values, label=label)
        ax.set_title(label)
        ax.set_xlabel("Packet Index")
        ax.set_ylabel("Correction Field (ns)")
        ax.grid(True)
        i += 1

    plt.tight_layout()
    plt.savefig("tc_residence_time.png", dpi=300)

def correction_to_ns(raw_value):
    """
    correctionField is a 64-bit signed fixed-point value:
    upper 48 bits = nanoseconds
    lower 16 bits = fractional nanoseconds
    Value is scaled by 2^16.
    """
    if raw_value & (1 << 63):
        raw_value -= 1 << 64
    return raw_value / 65536.0

def extract_follow_up_corrections(pcap_file):
    packets = rdpcap(pcap_file)
    values = []
    for pkt in packets:
        if pkt.haslayer(UDP):
            udp = pkt[UDP]
            if udp.dport == PTP_GENERAL_PORT:
                payload = bytes(udp.payload)
                if len(payload) < 34:
                    continue
                message_type = payload[0] & 0x0F
                if message_type == 0x8:
                    correction_raw = int.from_bytes(
                        payload[8:16], byteorder="big", signed=True
                    )
                    correction_ns = correction_to_ns(correction_raw)
                    values.append(correction_ns)
    return values

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ptp_avg_followup_udp.py <file1.pcap> <file2.pcap>")
        sys.exit(1)

    files = sys.argv[1:3]
    all_corrections = []

    for file in files:
        corrections = extract_follow_up_corrections(file)
        label = file.split("/")[-1]

        if not corrections:
            print(f"[{label}] No Follow_Up packets found.")
            all_corrections.append([])
        else:
            count = len(corrections)
            avg = statistics.mean(corrections)
            minimum = min(corrections)
            maximum = max(corrections)
            stddev = statistics.stdev(corrections) if count > 1 else 0.0

            print(f"\n--- {label} ---")
            print(f"Follow_Up packets found: {count}")
            print(f"Average correctionField: {avg:.3f} ns")
            print(f"Minimum correctionField: {minimum:.3f} ns")
            print(f"Maximum correctionField: {maximum:.3f} ns")
            print(f"Std Dev correctionField: {stddev:.3f} ns")

            all_corrections.append(corrections)

    labels = [f.split("/")[-1] for f in files]
    plot_corrections_combined(all_corrections, labels)