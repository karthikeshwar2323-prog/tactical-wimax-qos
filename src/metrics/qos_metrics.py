
def calculate_throughput(total_delivered_bits, simulation_time):
    """Calculate average throughput in bits per time unit."""
    if simulation_time <= 0:
        raise ValueError("Simulation time must be positive.")
    if total_delivered_bits < 0:
        raise ValueError("Delivered bits cannot be negative.")

    return total_delivered_bits / simulation_time


def calculate_average_delay(total_delay, packets_delivered):
    """Calculate average delay per delivered packet."""
    if total_delay < 0:
        raise ValueError("Total delay cannot be negative.")
    if packets_delivered < 0:
        raise ValueError("Delivered packet count cannot be negative.")
    if packets_delivered == 0:
        return 0.0

    return total_delay / packets_delivered


def calculate_packet_loss_ratio(packets_sent, packets_lost):
    """Calculate the fraction of offered packets that were dropped."""
    if packets_sent < 0 or packets_lost < 0:
        raise ValueError("Packet counts cannot be negative.")
    if packets_lost > packets_sent:
        raise ValueError("Lost packets cannot exceed packets sent.")
    if packets_sent == 0:
        return 0.0

    return packets_lost / packets_sent


def calculate_jain_fairness(values):
    """Calculate Jain's fairness index for nonnegative values."""
    if not values:
        return 0.0
    if any(value < 0 for value in values):
        raise ValueError("Fairness values cannot be negative.")

    total = sum(values)
    sum_of_squares = sum(value ** 2 for value in values)

    if sum_of_squares == 0:
        return 0.0

    return total ** 2 / (len(values) * sum_of_squares)


def calculate_resource_utilization(allocated_resources, total_resources):
    """
    Calculate the fraction of available resources allocated.

    Tiny floating-point excesses are clamped to the resource budget.
    Materially infeasible allocations still raise an error.
    """
    if total_resources <= 0:
        raise ValueError("Total resources must be positive.")
    if allocated_resources < 0:
        raise ValueError("Allocated resources cannot be negative.")

    tolerance = 1e-9 * max(1.0, float(total_resources))

    if allocated_resources > total_resources + tolerance:
        raise ValueError("Allocated resources exceed total resources.")

    safe_allocated = min(float(allocated_resources), float(total_resources))

    return safe_allocated / total_resources


def calculate_network_metrics(
    total_delivered_bits,
    simulation_time,
    total_delay,
    packets_delivered,
    packets_sent,
    packets_lost,
    user_throughputs,
    allocated_resources,
    total_resources,
):
    """Return the five QoS objectives for the simulated network."""
    return {
        "throughput": calculate_throughput(
            total_delivered_bits,
            simulation_time,
        ),
        "average_delay": calculate_average_delay(
            total_delay,
            packets_delivered,
        ),
        "packet_loss_ratio": calculate_packet_loss_ratio(
            packets_sent,
            packets_lost,
        ),
        "jain_fairness_index": calculate_jain_fairness(
            user_throughputs,
        ),
        "resource_utilization": calculate_resource_utilization(
            allocated_resources,
            total_resources,
        ),
    }
