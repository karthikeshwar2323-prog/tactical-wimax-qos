import shutil
from pathlib import Path

import optimization.run_nsga2 as nsga2_runner


def main():

    original_results = Path("results/nsga2_pareto_solutions.csv")
    high_traffic_results = Path("results/nsga2_high_traffic_results.csv")

    if not original_results.exists():
        raise FileNotFoundError(
            "Original NSGA-II results are missing."
        )

    # Preserve the original normal-traffic results
    original_backup = original_results.read_bytes()

    # Keep a reference to the original network creator
    original_network_creator = nsga2_runner.create_initial_network

    # Create a network with doubled traffic arrivals
    def create_high_traffic_network(*args, **kwargs):

        network = original_network_creator(*args, **kwargs)

        for user in network.users:
            user.packet_arrival_rate *= 2.0

        return network

    try:

        # Use the high-traffic network in the existing NSGA-II runner
        nsga2_runner.create_initial_network = create_high_traffic_network

        print("\n========== High-Traffic NSGA-II Experiment ==========")
        print("Traffic multiplier: 2.0x")
        print("Using the existing NSGA-II configuration.")

        nsga2_runner.main()

        # Preserve the new high-traffic results separately
        shutil.copy2(
            original_results,
            high_traffic_results
        )

        print(
            "\nHigh-traffic NSGA-II results saved to:",
            high_traffic_results
        )

    finally:

        # Restore the original normal-traffic results
        original_results.write_bytes(original_backup)

        # Restore the original network creator
        nsga2_runner.create_initial_network = original_network_creator

        print("Original normal-traffic NSGA-II results preserved.")


if __name__ == "__main__":
    main()