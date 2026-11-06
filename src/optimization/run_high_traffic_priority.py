import csv
from pathlib import Path

from network.network_model import create_initial_network
from network.simulation_engine import SimulationEngine
from optimization.priority_scheduler import allocate_priority_resources


def main():

    # Experiment configuration
    NETWORK_SEED = 42
    TRAFFIC_SEED = 42
    USERS_PER_CLASS = 4
    TOTAL_RESOURCES = 100
    SIMULATION_STEPS = 10
    TRAFFIC_MULTIPLIER = 2.0

    print("\n========== High-Traffic PBS Experiment ==========")
    print(f"Traffic multiplier: {TRAFFIC_MULTIPLIER}x")

    # Step 1: Create the network
    network = create_initial_network(
        seed=NETWORK_SEED,
        users_per_class=USERS_PER_CLASS,
        total_resources=TOTAL_RESOURCES
    )

    print(f"Total users: {len(network.users)}")
    print(f"Available resources: {network.total_resources}")

    # Step 2: Increase packet arrival rates for high traffic
    for user in network.users:
        user.packet_arrival_rate *= TRAFFIC_MULTIPLIER

    # Step 3: Calculate strict priority-based allocations
    allocations = allocate_priority_resources(
        network.users,
        network.total_resources
    )

    print(f"Allocated resources: {sum(allocations):.2f}")

    # Step 4: Initialize simulation with FIXED PBS allocation
    engine = SimulationEngine(
        network,
        traffic_seed=TRAFFIC_SEED,
        max_queue_size=500,
        resource_allocation=allocations,
        allocation_mode="fixed"
    )

    # Step 5: Run high-traffic simulation
    metrics = engine.run(
        steps=SIMULATION_STEPS,
        time_step=1.0
    )

    # Step 6: Display results
    engine.display_results(metrics)

    # Step 7: Save results
    project_root = Path(__file__).resolve().parents[2]
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / "pbs_high_traffic_results.csv"

    result_row = {
        "scheduler": "PBS",
        "traffic_scenario": "High Traffic",
        "traffic_multiplier": TRAFFIC_MULTIPLIER,
        "network_seed": NETWORK_SEED,
        "traffic_seed": TRAFFIC_SEED,
        "simulation_steps": SIMULATION_STEPS,
        **metrics
    }

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(result_row.keys())
        )

        writer.writeheader()
        writer.writerow(result_row)

    print(
        f"\nHigh-traffic PBS results saved to: {output_file}"
    )


if __name__ == "__main__":
    main()