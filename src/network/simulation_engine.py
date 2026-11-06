from traffic.traffic_generator import TrafficGenerator
from metrics.qos_metrics import calculate_network_metrics


class SimulationEngine:
    """
    Discrete-time Tactical WiMAX simulation.

    Fixed mode:
        Uses PBS allocations as fixed per-user resource limits.
        Unused resources are not redistributed.

    Adaptive mode:
        Uses allocation preferences with adaptive weighted water-filling.
        This is the mode used by NSGA-II.
    """

    def __init__(
        self,
        network,
        traffic_seed=42,
        max_queue_size=500,
        resource_allocation=None,
        allocation_mode="adaptive",
    ):
        if max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive.")

        if allocation_mode not in ("fixed", "adaptive"):
            raise ValueError(
                "allocation_mode must be 'fixed' or 'adaptive'."
            )

        self.network = network
        self.traffic_generator = TrafficGenerator(seed=traffic_seed)
        self.max_queue_size = max_queue_size
        self.resource_allocation = resource_allocation
        self.allocation_mode = allocation_mode

        self.total_packets_sent = 0
        self.total_packets_delivered = 0
        self.total_packets_lost = 0

        self.total_delivered_bits = 0
        self.total_delay = 0.0

        self.total_allocated_resources = 0.0
        self.total_consumed_resource_time = 0.0

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

        self.packet_queues = {
            user.user_id: [0.0] * int(user.queue_size)
            for user in network.users
        }

        self.service_credits = {
            user.user_id: 0.0 for user in network.users
        }

        self.initial_queued_packets = sum(
            len(queue) for queue in self.packet_queues.values()
        )

        self.total_packets_sent = self.initial_queued_packets

        for user in self.network.users:
            user.packets_delivered = 0
            user.packets_lost = 0
            user.delay = 0.0
            user.throughput = 0.0
            user.allocated_resources = 0.0

        if resource_allocation is not None:
            if len(resource_allocation) != len(network.users):
                raise ValueError(
                    "Allocation length must match the number of users."
                )

            if any(float(value) < 0 for value in resource_allocation):
                raise ValueError(
                    "Resource allocations cannot be negative."
                )

            if any(
                float(value) > user.required_bandwidth + 1e-9
                for value, user in zip(resource_allocation, network.users)
            ):
                raise ValueError(
                    "An allocation exceeds a user's required bandwidth."
                )

            if sum(float(value) for value in resource_allocation) > (
                network.total_resources + 1e-9
            ):
                raise ValueError(
                    "Resource allocations exceed the network budget."
                )

        if allocation_mode == "fixed" and resource_allocation is None:
            raise ValueError(
                "Fixed allocation mode requires resource_allocation."
            )

    def allocate_resources(self, time_step=1.0):
        """Allocate resources using fixed or adaptive scheduling."""

        users = self.network.users
        total_budget = float(self.network.total_resources)

        if self.resource_allocation is not None:
            preferences = [
                float(value) for value in self.resource_allocation
            ]
        else:
            preferences = [
                float(user.priority) for user in users
            ]

        demands = []

        for user in users:
            queue_size = len(self.packet_queues[user.user_id])

            channel_quality = max(
                float(user.channel_quality),
                1e-9,
            )

            demand = queue_size / (
                channel_quality * time_step
            )

            demand = min(
                demand,
                float(user.required_bandwidth),
            )

            demands.append(max(0.0, demand))

        # PBS: preserve the original priority-based allocation shares.
        # Current demand may reduce a user's actual allocation.
        # Unused resources are deliberately not redistributed.
        if self.allocation_mode == "fixed":
            allocations = [
                min(preferences[index], demands[index])
                for index in range(len(users))
            ]

        else:
            max_preference = max(preferences, default=0.0)
            max_preference = max(max_preference, 1e-9)

            weights = [
                max(float(user.priority), 1.0)
                * (
                    0.5 + max(preference, 0.0) / max_preference
                )
                for preference, user in zip(preferences, users)
            ]

            allocations = [0.0] * len(users)
            remaining = total_budget

            active = {
                index
                for index, demand in enumerate(demands)
                if demand > 0
            }

            minimum_service = {}

            for index in active:
                channel_quality = max(
                    float(users[index].channel_quality),
                    1e-9,
                )

                minimum_service[index] = min(
                    demands[index],
                    1.0 / (channel_quality * time_step),
                )

            minimum_total = sum(minimum_service.values())

            if minimum_total <= remaining + 1e-10:
                for index, amount in minimum_service.items():
                    allocations[index] += amount
                    remaining -= amount

            active = {
                index
                for index in active
                if demands[index] - allocations[index] > 1e-10
            }

            while active and remaining > 1e-10:
                total_weight = sum(
                    weights[index] for index in active
                )

                if total_weight <= 0:
                    break

                proposed = {
                    index: remaining * weights[index] / total_weight
                    for index in active
                }

                capped_users = [
                    index
                    for index in active
                    if proposed[index]
                    >= demands[index] - allocations[index]
                ]

                if not capped_users:
                    for index in active:
                        allocations[index] += proposed[index]

                    remaining = 0.0
                    break

                for index in capped_users:
                    amount = demands[index] - allocations[index]

                    allocations[index] += amount
                    remaining -= amount

                    active.remove(index)

        allocations = [
            max(0.0, min(amount, demands[index]))
            for index, amount in enumerate(allocations)
        ]

        allocated_total = sum(allocations)

        if allocated_total > total_budget + 1e-8:
            raise RuntimeError(
                "Dynamic allocation exceeded the resource budget."
            )

        for user, amount in zip(users, allocations):
            if amount > user.required_bandwidth + 1e-8:
                raise RuntimeError(
                    f"Allocation limit exceeded for user {user.user_id}."
                )

            user.allocated_resources = amount

        return allocated_total

    def step(self, time_step=1.0):
        """Run one simulation step."""

        if time_step <= 0:
            raise ValueError("time_step must be positive.")

        arrivals = self.traffic_generator.generate_for_network(
            self.network,
            time_step,
        )

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
            user.queue_size = float(len(queue))

        allocated = self.allocate_resources(time_step)

        self.total_allocated_resources += allocated * time_step

        packet_bits = 1000

        for user in self.network.users:
            user_id = user.user_id
            queue = self.packet_queues[user_id]

            if not queue:
                self.service_credits[user_id] = 0.0
                continue

            channel_quality = float(user.channel_quality)

            new_service = (
                user.allocated_resources
                * channel_quality
                * time_step
            )

            available_service = (
                self.service_credits[user_id] + new_service
            )

            service_capacity = int(available_service)

            delivered = min(
                len(queue),
                service_capacity,
            )

            for _ in range(delivered):
                arrival_time = queue.pop(0)

                packet_delay = (
                    self.simulation_time
                    + time_step
                    - arrival_time
                )

                self.total_delay += packet_delay
                self.user_delay_sum[user_id] += packet_delay

            if queue:
                self.service_credits[user_id] = (
                    available_service - delivered
                )
            else:
                self.service_credits[user_id] = 0.0

            if delivered > 0 and channel_quality > 0:
                self.total_consumed_resource_time += (
                    delivered / channel_quality
                )

            user.packets_delivered += delivered
            self.total_packets_delivered += delivered

            self.user_delivered_count[user_id] += delivered

            delivered_bits = delivered * packet_bits

            self.total_delivered_bits += delivered_bits
            self.user_delivered_bits[user_id] += delivered_bits

            user.queue_size = float(len(queue))
            user.throughput = delivered_bits / time_step

            delivered_count = self.user_delivered_count[user_id]

            user.delay = (
                self.user_delay_sum[user_id] / delivered_count
                if delivered_count > 0
                else 0.0
            )

        self.simulation_time += time_step

    def run(self, steps=10, time_step=1.0):
        """Run the simulation and return aggregate QoS metrics."""

        if steps <= 0:
            raise ValueError("steps must be positive.")

        for _ in range(steps):
            self.step(time_step)

        return self.get_metrics()

    def get_metrics(self):
        """Calculate network-level QoS and resource metrics."""

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

        queued_packet_delays = [
            self.simulation_time - arrival_time
            for queue in self.packet_queues.values()
            for arrival_time in queue
        ]

        queued_packet_count = len(queued_packet_delays)
        queued_total_delay = sum(queued_packet_delays)

        observed_total_delay = (
            self.total_delay + queued_total_delay
        )

        observed_packet_count = (
            self.total_packets_delivered + queued_packet_count
        )

        return calculate_network_metrics(
            total_delivered_bits=self.total_delivered_bits,
            simulation_time=self.simulation_time,
            total_delay=observed_total_delay,
            packets_delivered=observed_packet_count,
            packets_sent=self.total_packets_sent,
            packets_lost=self.total_packets_lost,
            user_throughputs=user_average_throughputs,
            allocated_resources=average_allocated_resources,
            total_resources=self.network.total_resources,
            consumed_resource_time=self.total_consumed_resource_time,
        )

    def display_results(self, metrics):
        """Display aggregate and per-user simulation results."""

        print("\n========== Simulation Results ==========")

        for name, value in metrics.items():
            print(
                f"{name.replace('_', ' ').title():<30}: "
                f"{value:.4f}"
            )

        queued_packets = sum(
            len(queue) for queue in self.packet_queues.values()
        )

        print("\nPacket Accounting:")
        print(f"Initially queued    : {self.initial_queued_packets}")
        print(f"Packets offered     : {self.total_packets_sent}")
        print(f"Packets delivered   : {self.total_packets_delivered}")
        print(f"Packets dropped     : {self.total_packets_lost}")
        print(f"Packets still queued: {queued_packets}")

        print("\nResource Accounting:")
        print(
            f"Allocated resource-time : "
            f"{self.total_allocated_resources:.4f}"
        )
        print(
            f"Consumed resource-time  : "
            f"{self.total_consumed_resource_time:.4f}"
        )

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