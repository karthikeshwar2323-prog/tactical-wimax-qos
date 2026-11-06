
def calculate_throughput(total_delivered_bits, simulation_time):
    """Calculate average throughput in bits per time unit."""
    if simulation_time <= 0:
        raise ValueError("Simulation time must be positive.")

    if total_delivered_bits < 0:
        raise ValueError("Delivered bits cannot be negative.")

    return total_delivered_bits / simulation_time


def calculate_average_delay(total_delay, packets_delivered):
    """
    Calculate average observed packet delay.

    The packet count may include delivered packets and packets
    still waiting in queues at the end of simulation.
    """
    if total_delay < 0:
        raise ValueError("Total delay cannot be negative.")

    if packets_delivered < 0:
        raise ValueError("Packet count cannot be negative.")

    if packets_delivered == 0:
        return 0.0

    return total_delay / packets_delivered


def calculate_packet_loss_ratio(packets_sent, packets_lost):
    """Calculate the fraction of offered packets that were lost."""
    if packets_sent < 0 or packets_lost < 0:
        raise ValueError("Packet counts cannot be negative.")

    if packets_lost > packets_sent:
        raise ValueError("Lost packets cannot exceed sent packets.")

    if packets_sent == 0:
        return 0.0

    return packets_lost / packets_sent


def calculate_jain_fairness(values):
    """Calculate Jain's fairness index."""
    if not values:
        return 0.0

    if any(value < 0 for value in values):
        raise ValueError("Fairness values cannot be negative.")

    total = sum(values)
    sum_of_squares = sum(value ** 2 for value in values)

    if sum_of_squares == 0:
        return 0.0

    return (total ** 2) / (len(values) * sum_of_squares)


def calculate_resource_allocation_ratio(
    allocated_resources,
    total_resources
):
    """
    Calculate the fraction of available resources allocated.

    This measures assigned resources, not actual consumption.
    """
    if total_resources <= 0:
        raise ValueError("Total resources must be positive.")

    if allocated_resources < 0:
        raise ValueError("Allocated resources cannot be negative.")

    if allocated_resources > total_resources + 1e-9:
        raise ValueError("Allocated resources exceed available resources.")

    return min(allocated_resources / total_resources, 1.0)


def calculate_resource_utilization_ratio(
    consumed_resource_time,
    total_resources,
    simulation_time
):
    """
    Calculate the fraction of available resource-time actually consumed.

    consumed_resource_time is measured in resource-unit time.
    """
    if total_resources <= 0:
        raise ValueError("Total resources must be positive.")

    if simulation_time <= 0:
        raise ValueError("Simulation time must be positive.")

    if consumed_resource_time < 0:
        raise ValueError("Consumed resource-time cannot be negative.")

    available_resource_time = total_resources * simulation_time

    if consumed_resource_time > available_resource_time + 1e-8:
        raise ValueError(
            "Consumed resource-time exceeds available resource-time."
        )

    return min(
        consumed_resource_time / available_resource_time,
        1.0
    )


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
    consumed_resource_time=0.0
):
    """Calculate network-level QoS and resource metrics."""

    return {
        "throughput": calculate_throughput(
            total_delivered_bits,
            simulation_time
        ),
        "average_delay": calculate_average_delay(
            total_delay,
            packets_delivered
        ),
        "packet_loss_ratio": calculate_packet_loss_ratio(
            packets_sent,
            packets_lost
        ),
        "jain_fairness_index": calculate_jain_fairness(
            user_throughputs
        ),
        "resource_allocation_ratio": calculate_resource_allocation_ratio(
            allocated_resources,
            total_resources
        ),
        "resource_utilization_ratio": calculate_resource_utilization_ratio(
            consumed_resource_time,
            total_resources,
            simulation_time
        )
    }
