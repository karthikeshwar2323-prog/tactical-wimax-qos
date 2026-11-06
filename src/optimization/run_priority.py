import csv
from pathlib import Path

from network.network_model import create_initial_network
from network.simulation_engine import SimulationEngine
from optimization.priority_scheduler import allocate_priority_resources


def main():

    # Step 1: Create the network
    network = create_initial_network(
        seed=42,
        users_per_class=4,
        total_resources=100
    )

    # Step 2: Calculate fixed PBS allocations
    allocations = allocate_priority_resources(
        network.users,
        network.total_resources
    )

    print("\n========== Priority-Based Scheduling ==========")
    print(f"Total available resources: {network.total_resources}")
    print(f"Total allocated resources: {sum(allocations):.2f}")

    # Step 3: Run simulation using fixed PBS allocation
    engine = SimulationEngine(
        network,
        traffic_seed=42,
        max_queue_size=500,
        resource_allocation=allocations,
        allocation_mode="fixed"
    )

    metrics = engine.run(
        steps=10,
        time_step=1.0
    )

    engine.display_results(metrics)

    # Step 4: Save baseline results
    output_path = Path("results/pbs_baseline_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "scheduler": "Priority-Based Scheduling",
        "network_seed": 42,
        "traffic_seed": 42,
        "simulation_steps": 10,
        "total_resources": network.total_resources,
        **metrics
    }

    with output_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=result.keys()
        )
        writer.writeheader()
        writer.writerow(result)

    print(f"\nPBS results saved to: {output_path}")


if __name__ == "__main__":
    main()