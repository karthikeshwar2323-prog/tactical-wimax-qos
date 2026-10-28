
from pathlib import Path
import csv

from network.network_model import create_initial_network
from network.simulation_engine import SimulationEngine
from optimization.nsga2 import NSGA2


# Reproducible experimental configuration
NETWORK_SEED = 42
TRAFFIC_SEED = 42
SIMULATION_STEPS = 10
TOTAL_RESOURCES = 100
USERS_PER_CLASS = 4
POPULATION_SIZE = 40
GENERATIONS = 50


def create_network():
    """Create a fresh, reproducible Tactical WiMAX network."""
    return create_initial_network(
        seed=NETWORK_SEED,
        users_per_class=USERS_PER_CLASS,
        total_resources=TOTAL_RESOURCES,
    )


def evaluate_allocation(allocation):
    """
    Evaluate one candidate resource allocation.

    A fresh network and simulation are created for each candidate.
    The same random seeds provide consistent traffic conditions.
    """
    network = create_network()

    engine = SimulationEngine(
        network=network,
        traffic_seed=TRAFFIC_SEED,
        max_queue_size=500,
        resource_allocation=allocation,
    )

    return engine.run(steps=SIMULATION_STEPS)


def save_pareto_solutions(solutions):
    """Save the final Pareto solutions and QoS metrics to CSV."""
    results_directory = Path("results")
    results_directory.mkdir(parents=True, exist_ok=True)

    output_file = results_directory / "nsga2_pareto_solutions.csv"

    fieldnames = [
        "solution_id",
        "allocated_resources",
        "throughput",
        "average_delay",
        "packet_loss_ratio",
        "jain_fairness_index",
        "resource_utilization",
    ]

    with output_file.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for index, solution in enumerate(solutions, start=1):
            metrics = solution["metrics"]

            writer.writerow({
                "solution_id": index,
                "allocated_resources": sum(solution["allocation"]),
                "throughput": metrics["throughput"],
                "average_delay": metrics["average_delay"],
                "packet_loss_ratio": metrics["packet_loss_ratio"],
                "jain_fairness_index": metrics["jain_fairness_index"],
                "resource_utilization": metrics["resource_utilization"],
            })

    return output_file


def display_solution(index, solution, users):
    """Print one Pareto solution and its per-user allocation."""
    metrics = solution["metrics"]
    allocation = solution["allocation"]

    print(f"\n{'=' * 58}")
    print(f"PARETO SOLUTION {index}")
    print(f"{'=' * 58}")

    print(f"Pareto rank             : {solution['rank']}")
    print(f"Total allocated resources: {sum(allocation):.4f}")
    print(f"Available resources     : {TOTAL_RESOURCES}")

    print("\nQoS Metrics")
    print("-" * 58)
    print(f"Throughput              : {metrics['throughput']:.4f}")
    print(f"Average delay           : {metrics['average_delay']:.4f}")
    print(f"Packet loss ratio       : {metrics['packet_loss_ratio']:.4f}")
    print(
        "Jain fairness index    : "
        f"{metrics['jain_fairness_index']:.4f}"
    )
    print(
        "Resource utilization   : "
        f"{metrics['resource_utilization']:.4f}"
    )

    print("\nPer-user Resource Allocation")
    print("-" * 58)
    print(
        f"{'User ID':<10}"
        f"{'Traffic Class':<20}"
        f"{'Priority':<10}"
        f"{'Allocation':<12}"
    )
    print("-" * 58)

    for user, amount in zip(users, allocation):
        print(
            f"{user.user_id:<10}"
            f"{user.traffic_type:<20}"
            f"{user.priority:<10}"
            f"{amount:<12.4f}"
        )


def main():
    """Run NSGA-II and save its final Pareto solutions."""
    network = create_network()

    print("=" * 58)
    print("TACTICAL WiMAX QoS OPTIMIZATION USING NSGA-II")
    print("=" * 58)

    print("\nExperimental Configuration")
    print("-" * 58)
    print(f"Traffic classes          : 5")
    print(f"Users per class          : {USERS_PER_CLASS}")
    print(f"Total users              : {len(network.users)}")
    print(f"Total resources          : {network.total_resources}")
    print(f"Simulation steps         : {SIMULATION_STEPS}")
    print(f"Population size          : {POPULATION_SIZE}")
    print(f"Number of generations    : {GENERATIONS}")
    print(f"Network random seed      : {NETWORK_SEED}")
    print(f"Traffic random seed      : {TRAFFIC_SEED}")

    print("\nQoS Optimization Objectives")
    print("-" * 58)
    print("1. Maximize throughput")
    print("2. Minimize average delay")
    print("3. Minimize packet loss ratio")
    print("4. Maximize Jain's fairness index")
    print("5. Maximize resource utilization")

    optimizer = NSGA2(
        network=network,
        objective_evaluator=evaluate_allocation,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        crossover_probability=0.9,
        mutation_probability=None,
        seed=42,
    )

    print("\nStarting NSGA-II optimization...\n")

    pareto_solutions = optimizer.optimize()

    if not pareto_solutions:
        print("\nNo Pareto solutions were returned.")
        return

    print("\n\n" + "=" * 58)
    print("FINAL PARETO-OPTIMAL SOLUTIONS")
    print("=" * 58)
    print(f"Number of returned solutions: {len(pareto_solutions)}")

    for index, solution in enumerate(pareto_solutions, start=1):
        display_solution(index, solution, network.users)

    output_file = save_pareto_solutions(pareto_solutions)

    print("\n\n" + "=" * 58)
    print("EXPERIMENT SUMMARY")
    print("=" * 58)
    print(f"Generations completed : {len(optimizer.history)}")
    print(f"Pareto solutions      : {len(pareto_solutions)}")
    print(f"Results saved to      : {output_file}")

    if optimizer.history:
        print("\nPareto Front Progress")
        print("-" * 58)
        print(f"{'Generation':<15}{'Pareto Solutions':<20}")

        for record in optimizer.history:
            print(
                f"{record['generation']:<15}"
                f"{record['pareto_front_size']:<20}"
            )

    print("\nOptimization completed.")
    print(
        "These are simulated results, not measurements from "
        "physical WiMAX equipment."
    )


if __name__ == "__main__":
    main()
