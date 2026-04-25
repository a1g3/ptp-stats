from scapy.all import rdpcap, UDP
import sys
import statistics
import matplotlib.pyplot as plt

PTP_EVENT_PORT = 319
PTP_GENERAL_PORT = 320


def plot_corrections(values):
    plt.figure(figsize=(12, 5))

    # Line plot (value vs packet index)
    plt.plot(values)
    plt.title("Ed25519: PTP Residence Time Per Packet")
    plt.xlabel("Packet Index")
    plt.ylabel("Correction Field (ns)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("tc_residence_time.png", dpi=300)
    plt.show()


def correction_to_ns(raw_value):
    """
    correctionField is a 64-bit signed fixed-point value:
    upper 48 bits = nanoseconds
    lower 16 bits = fractional nanoseconds
    Value is scaled by 2^16.
    """
    # Convert signed 64-bit (defensive, even though signed=True is used)
    if raw_value & (1 << 63):
        raw_value -= 1 << 64
    return raw_value / 65536.0


def extract_follow_up_corrections(pcap_file):
    packets = rdpcap(pcap_file)
    values = []

    for pkt in packets:
        if pkt.haslayer(UDP):
            udp = pkt[UDP]

            # Follow_Up is a GENERAL message → port 320
            if udp.dport == PTP_GENERAL_PORT:
                payload = bytes(udp.payload)

                if len(payload) < 34:
                    continue

                # PTP messageType = lower 4 bits of first byte
                message_type = payload[0] & 0x0F

                # Follow_Up = 0x8
                if message_type == 0x8:
                    # correctionField = bytes 8–15
                    correction_raw = int.from_bytes(
                        payload[8:16], byteorder="big", signed=True
                    )
                    correction_ns = correction_to_ns(correction_raw)
                    values.append(correction_ns)

    return values


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ptp_avg_followup_udp.py <file.pcap>")
        sys.exit(1)

    file = sys.argv[1]
    corrections = extract_follow_up_corrections(file)

    if not corrections:
        print("No Follow_Up packets found.")
        sys.exit(0)

    count = len(corrections)
    avg = statistics.mean(corrections)
    minimum = min(corrections)
    maximum = max(corrections)
    stddev = statistics.stdev(corrections) if count > 1 else 0.0

    print(f"Follow_Up packets found: {count}")
    print(f"Average correctionField: {avg:.3f} ns")
    print(f"Minimum correctionField: {minimum:.3f} ns")
    print(f"Maximum correctionField: {maximum:.3f} ns")
    print(f"Std Dev correctionField: {stddev:.3f} ns")

    plot_corrections(corrections)