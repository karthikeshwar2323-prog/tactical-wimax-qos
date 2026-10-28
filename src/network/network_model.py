
from dataclasses import dataclass
import random


@dataclass
class User:
    """Represents a user in the Tactical WiMAX network."""

    user_id: int
    traffic_type: str
    priority: int
    queue_size: float
    packet_arrival_rate: float
    channel_quality: float
    required_bandwidth: float

    allocated_resources: float = 0.0
    packets_delivered: int = 0
    packets_lost: int = 0
    delay: float = 0.0
    throughput: float = 0.0


class TacticalWiMAXNetwork:
    """Represents a simulated Tactical WiMAX network."""

    def __init__(self, total_resources=100):
        if total_resources <= 0:
            raise ValueError("Total resources must be positive.")

        self.total_resources = total_resources
        self.users = []

    def add_user(self, user):
        """Add a user to the network."""
        if any(existing.user_id == user.user_id for existing in self.users):
            raise ValueError(f"Duplicate user ID: {user.user_id}")

        if not 0.0 <= user.channel_quality <= 1.0:
            raise ValueError("Channel quality must be between 0 and 1.")

        if user.queue_size < 0:
            raise ValueError("Queue size cannot be negative.")

        if user.packet_arrival_rate < 0:
            raise ValueError("Packet arrival rate cannot be negative.")

        if user.required_bandwidth < 0:
            raise ValueError("Required bandwidth cannot be negative.")

        self.users.append(user)

    def display_network(self):
        """Display the network configuration and user conditions."""
        print("\n========== Tactical WiMAX Network ==========")
        print(f"Total Resources : {self.total_resources}")
        print(f"Number of Users : {len(self.users)}")

        print("\nUser Details:")
        print(
            f"{'ID':<5}"
            f"{'Traffic Type':<18}"
            f"{'Priority':<10}"
            f"{'Queue':<11}"
            f"{'Arrival Rate':<15}"
            f"{'Channel':<10}"
            f"{'Required BW':<12}"
        )
        print("-" * 81)

        for user in self.users:
            print(
                f"{user.user_id:<5}"
                f"{user.traffic_type:<18}"
                f"{user.priority:<10}"
                f"{user.queue_size:<11.2f}"
                f"{user.packet_arrival_rate:<15.2f}"
                f"{user.channel_quality:<10.2f}"
                f"{user.required_bandwidth:<12.2f}"
            )

        print("-" * 81)


def create_initial_network(seed=42, users_per_class=4, total_resources=100):
    """
    Create a reproducible network with five traffic classes.

    The numerical ranges are abstract simulation assumptions,
    not physical WiMAX equipment specifications.
    """
    if users_per_class <= 0:
        raise ValueError("Users per class must be positive.")

    rng = random.Random(seed)
    network = TacticalWiMAXNetwork(total_resources=total_resources)

    traffic_configuration = {
        "Voice": {
            "priority": 5,
            "queue": (20, 60),
            "arrival": (15, 30),
            "channel": (0.70, 0.95),
            "bandwidth": (5, 10),
        },
        "Video": {
            "priority": 4,
            "queue": (40, 100),
            "arrival": (25, 50),
            "channel": (0.50, 0.90),
            "bandwidth": (10, 20),
        },
        "Tactical Data": {
            "priority": 5,
            "queue": (20, 70),
            "arrival": (10, 25),
            "channel": (0.65, 0.95),
            "bandwidth": (8, 15),
        },
        "Normal Data": {
            "priority": 3,
            "queue": (20, 80),
            "arrival": (10, 25),
            "channel": (0.40, 0.85),
            "bandwidth": (5, 15),
        },
        "Best Effort": {
            "priority": 1,
            "queue": (10, 100),
            "arrival": (5, 20),
            "channel": (0.30, 0.80),
            "bandwidth": (5, 10),
        },
    }

    user_id = 1

    for traffic_type, settings in traffic_configuration.items():
        for _ in range(users_per_class):
            user = User(
                user_id=user_id,
                traffic_type=traffic_type,
                priority=settings["priority"],
                queue_size=rng.uniform(*settings["queue"]),
                packet_arrival_rate=rng.uniform(*settings["arrival"]),
                channel_quality=rng.uniform(*settings["channel"]),
                required_bandwidth=rng.uniform(*settings["bandwidth"]),
            )

            network.add_user(user)
            user_id += 1

    return network


if __name__ == "__main__":
    network = create_initial_network()
    network.display_network()
