
from traffic.traffic_generator import TrafficGenerator
from metrics.qos_metrics import calculate_network_metrics


class SimulationEngine:
    """
    Discrete-time Tactical WiMAX network simulation.

    Resource units and packet sizes are abstract simulation assumptions,
    not measurements from physical WiMAX equipment.
    """

    def __init__(
        self,
        network,
        traffic_seed=42,
        max_queue_size=500,
        resource_allocation=None,
    ):
        if max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive.")

        self.network = network
        self.traffic_generator = TrafficGenerator(seed=traffic_seed)
        self.max_queue_size = max_queue_size
        self.resource_allocation = resource_allocation

        self.total_packets_sent = 0
        self.total_packets_delivered = 0
        self.total_packets_lost = 0
        self.total_delivered_bits = 0
        self.total_delay = 0.0
        self.total_allocated_resources = 0.0
        self.simulation_time = 0.0

        self.user_delivered_bits = {
            user.user_id: 0 for user in network.users
        }
        self.user_delay_sum = {
            user.user_id: 0.0 for user in network.users
        }
        self.user_delivered_count = {
            user.user_id: 0 for user in network.users
        }

        # Each queued packet stores its arrival time.
        # Existing queue_size values become initial backlog packets.
        self.packet_queues = {
            user.user_id: [0.0] * int(user.queue_size)
            for user in network.users
        }

        self.initial_queued_packets = sum(
            len(queue) for queue in self.packet_queues.values()
        )

        # Existing backlog is treated as previously offered traffic.
        self.total_packets_sent = self.initial_queued_packets

        for user in self.network.users:
            user.packets_delivered = 0
            user.packets_lost = 0
            user.delay = 0.0
            user.throughput = 0.0
            user.allocated_resources = 0.0

    def allocate_resources(self):
        """
        Apply a candidate allocation or use the temporary priority rule.

        Candidate allocations are used by NSGA-II. The fallback allocation
        is only for running the simulator before optimization is connected.
        """
        users = self.network.users

        if self.resource_allocation is not None:
            if len(self.resource_allocation) != len(users):
                raise ValueError(
                    "Allocation length must match the number of users."
                )

            allocation = [
                float(value) for value in self.resource_allocation
            ]

            if any(value < 0 for value in allocation):
                raise ValueError("Allocations cannot be negative.")

            if any(
                value > user.required_bandwidth + 1e-9
                for value, user in zip(allocation, users)
            ):
                raise ValueError(
                    "An allocation exceeds a user's required bandwidth."
                )

            if sum(allocation) > self.network.total_resources + 1e-9:
                raise ValueError(
                    "Allocations exceed the total resource budget."
                )

            for user, value in zip(users, allocation):
                user.allocated_resources = value

        else:
            remaining = float(self.network.total_resources)

            for user in users:
                user.allocated_resources = 0.0

            for user in sorted(
                users,
                key=lambda item: item.priority,
                reverse=True,
            ):
                if remaining <= 0:
                    break

                amount = min(user.required_bandwidth, remaining)
                user.allocated_resources = amount
                remaining -= amount

        return sum(user.allocated_resources for user in users)

    def step(self, time_step=1.0):
        """Simulate one time step."""
        if time_step <= 0:
            raise ValueError("time_step must be positive.")

        arrivals = self.traffic_generator.generate_for_network(
            self.network,
            time_step,
        )

        allocated = self.allocate_resources()
        self.total_allocated_resources += allocated * time_step

        # Simplifying assumption: every packet contains 1,000 bits.
        packet_bits = 1000

        for user in self.network.users:
            queue = self.packet_queues[user.user_id]
            incoming = arrivals[user.user_id]

            self.total_packets_sent += incoming

            available_slots = max(
                0,
                self.max_queue_size - len(queue),
            )
            accepted = min(incoming, available_slots)
            dropped = incoming - accepted

            queue.extend(
                [self.simulation_time] * accepted
            )

            user.packets_lost += dropped
            self.total_packets_lost += dropped

            service_capacity = int(
                user.allocated_resources
                * user.channel_quality
                * time_step
            )

            delivered = min(len(queue), service_capacity)

            for _ in range(delivered):
                arrival_time = queue.pop(0)

                packet_delay = (
                    self.simulation_time + time_step - arrival_time
                )

                self.total_delay += packet_delay
                self.user_delay_sum[user.user_id] += packet_delay

            user.packets_delivered += delivered
            self.total_packets_delivered += delivered
            self.user_delivered_count[user.user_id] += delivered

            delivered_bits = delivered * packet_bits
            self.total_delivered_bits += delivered_bits
            self.user_delivered_bits[user.user_id] += delivered_bits

            user.queue_size = float(len(queue))

            user.throughput = delivered_bits / time_step

            delivered_count = self.user_delivered_count[user.user_id]
            user.delay = (
                self.user_delay_sum[user.user_id] / delivered_count
                if delivered_count > 0
                else 0.0
            )

        self.simulation_time += time_step

    def run(self, steps=10, time_step=1.0):
        """Run the simulation and return cumulative QoS metrics."""
        if steps <= 0:
            raise ValueError("steps must be positive.")

        for _ in range(steps):
            self.step(time_step)

        return self.get_metrics()

    def get_metrics(self):
        """Calculate the five network-level QoS metrics."""
        user_average_throughputs = [
            self.user_delivered_bits[user.user_id] / self.simulation_time
            if self.simulation_time > 0
            else 0.0
            for user in self.network.users
        ]

        average_allocated_resources = (
            self.total_allocated_resources / self.simulation_time
            if self.simulation_time > 0
            else 0.0
        )

        return calculate_network_metrics(
            total_delivered_bits=self.total_delivered_bits,
            simulation_time=self.simulation_time,
            total_delay=self.total_delay,
            packets_delivered=self.total_packets_delivered,
            packets_sent=self.total_packets_sent,
            packets_lost=self.total_packets_lost,
            user_throughputs=user_average_throughputs,
            allocated_resources=average_allocated_resources,
            total_resources=self.network.total_resources,
        )

    def display_results(self, metrics):
        """Display network metrics and per-user statistics."""
        print("\n========== Simulation Results ==========")

        for name, value in metrics.items():
            print(f"{name.replace('_', ' ').title():<25}: {value:.4f}")

        queued_packets = sum(
            len(queue) for queue in self.packet_queues.values()
        )

        print("\nPacket Accounting:")
        print(f"Initially queued   : {self.initial_queued_packets}")
        print(f"Packets offered    : {self.total_packets_sent}")
        print(f"Packets delivered  : {self.total_packets_delivered}")
        print(f"Packets dropped    : {self.total_packets_lost}")
        print(f"Packets still queued: {queued_packets}")

        print("\nPer-User Results:")
        print(
            f"{'ID':<5}{'Traffic':<18}{'Allocated':<12}"
            f"{'Delivered':<12}{'Dropped':<10}"
            f"{'Queued':<10}{'Throughput':<14}"
        )

        for user in self.network.users:
            print(
                f"{user.user_id:<5}"
                f"{user.traffic_type:<18}"
                f"{user.allocated_resources:<12.2f}"
                f"{user.packets_delivered:<12}"
                f"{user.packets_lost:<10}"
                f"{len(self.packet_queues[user.user_id]):<10}"
                f"{user.throughput:<14.2f}"
            )


if __name__ == "__main__":
    from network.network_model import create_initial_network

    network = create_initial_network()
    engine = SimulationEngine(network)

    results = engine.run(steps=10)
    engine.display_results(results)
