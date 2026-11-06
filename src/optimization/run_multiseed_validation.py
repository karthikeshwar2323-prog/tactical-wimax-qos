
import csv
import statistics
from pathlib import Path

from network.network_model import create_initial_network
from network.simulation_engine import SimulationEngine
from optimization.nsga2 import NSGA2
from optimization.priority_scheduler import allocate_priority_resources


# Reproducible multi-seed configuration
SEEDS = [42, 123, 2026, 7, 99]

USERS_PER_CLASS = 4
TOTAL_RESOURCES = 100
SIMULATION_STEPS = 10
MAX_QUEUE_SIZE = 500

POPULATION_SIZE = 40
GENERATIONS = 50
CROSSOVER_PROBABILITY = 0.9

TRAFFIC_SCENARIOS = {
    "Normal": 1.0,
    "High": 2.0,
}

METRIC_NAMES = [
    "throughput",
    "average_delay",
    "packet_loss_ratio",
    "jain_fairness_index",
    "resource_allocation_ratio",
    "resource_utilization_ratio",
]


def create_network(seed, traffic_multiplier):
    """Create a fresh network for one experiment."""

    network = create_initial_network(
        seed=seed,
        users_per_class=USERS_PER_CLASS,
        total_resources=TOTAL_RESOURCES,
    )

    for user in network.users:
        user.packet_arrival_rate *= traffic_multiplier

    return network


def run_pbs(seed, traffic_multiplier):
    """Run the fixed strict priority-based scheduler."""

    network = create_network(seed, traffic_multiplier)

    allocations = allocate_priority_resources(
        network.users,
        network.total_resources,
    )

    engine = SimulationEngine(
        network=network,
        traffic_seed=seed,
        max_queue_size=MAX_QUEUE_SIZE,
        resource_allocation=allocations,
        allocation_mode="fixed",
    )

    return engine.run(
        steps=SIMULATION_STEPS,
        time_step=1.0,
    )


def run_nsga2(seed, traffic_multiplier):
    """Run NSGA-II using matching network and traffic seeds."""

    base_network = create_network(seed, traffic_multiplier)

    def evaluate_allocation(allocation):
        # Every candidate gets a fresh network with identical
        # conditions within this seed.
        network = create_network(seed, traffic_multiplier)

        engine = SimulationEngine(
            network=network,
            traffic_seed=seed,
            max_queue_size=MAX_QUEUE_SIZE,
            resource_allocation=allocation,
            allocation_mode="adaptive",
        )

        return engine.run(
            steps=SIMULATION_STEPS,
            time_step=1.0,
        )

    optimizer = NSGA2(
        network=base_network,
        objective_evaluator=evaluate_allocation,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        crossover_probability=CROSSOVER_PROBABILITY,
        mutation_probability=None,
        seed=seed,
    )

    pareto_solutions = optimizer.optimize()

    if not pareto_solutions:
        raise RuntimeError(
            f"NSGA-II returned no Pareto solutions for seed {seed}."
        )

    return pareto_solutions


def mean_metrics(solutions):
    """Calculate the mean of each metric across a Pareto front."""

    return {
        metric: statistics.mean(
            float(solution["metrics"][metric])
            for solution in solutions
        )
        for metric in METRIC_NAMES
    }


def save_raw_results(rows, output_file):
    """Save all PBS results and individual NSGA-II Pareto solutions."""

    fieldnames = [
        "scenario",
        "scheduler",
        "seed",
        "traffic_multiplier",
        "solution_id",
        "pareto_front_size",
        *METRIC_NAMES,
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


def save_summary(seed_level_results, output_file):
    """
    Calculate mean and sample standard deviation across seeds.

    For NSGA-II, each seed contributes the mean metrics
    of its own Pareto front.
    """

    grouped = {}

    for result in seed_level_results:
        key = (result["scenario"], result["scheduler"])

        grouped.setdefault(key, []).append(result)

    summary_rows = []

    for (scenario, scheduler), results in grouped.items():

        for metric in METRIC_NAMES:

            values = [
                result[metric]
                for result in results
            ]

            summary_rows.append({
                "scenario": scenario,
                "scheduler": scheduler,
                "metric": metric,
                "seed_count": len(values),
                "mean": statistics.mean(values),
                "sample_std_dev": statistics.stdev(values),
            })

    fieldnames = [
        "scenario",
        "scheduler",
        "metric",
        "seed_count",
        "mean",
        "sample_std_dev",
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(summary_rows)


def main():

    project_root = Path(__file__).resolve().parents[2]
    results_directory = project_root / "results"
    results_directory.mkdir(parents=True, exist_ok=True)

    raw_rows = []
    seed_level_results = []

    total_runs = len(SEEDS) * len(TRAFFIC_SCENARIOS) * 2
    completed_runs = 0

    print("=" * 65)
    print("TACTICAL WiMAX MULTI-SEED EXPERIMENTAL VALIDATION")
    print("=" * 65)

    print(f"Seeds                 : {SEEDS}")
    print(f"Number of seeds       : {len(SEEDS)}")
    print(f"Traffic scenarios     : {len(TRAFFIC_SCENARIOS)}")
    print(f"Total scheduler runs  : {total_runs}")
    print(f"Population size       : {POPULATION_SIZE}")
    print(f"Generations           : {GENERATIONS}")
    print(f"Simulation steps      : {SIMULATION_STEPS}")

    for scenario, multiplier in TRAFFIC_SCENARIOS.items():

        print("\n" + "=" * 65)
        print(f"SCENARIO: {scenario.upper()}")
        print(f"Traffic multiplier: {multiplier}x")
        print("=" * 65)

        for seed in SEEDS:

            print("\n" + "-" * 55)
            print(f"Seed: {seed} | Scenario: {scenario}")
            print("-" * 55)

            # PBS experiment
            print("\nRunning PBS...")

            pbs_metrics = run_pbs(seed, multiplier)

            raw_rows.append({
                "scenario": scenario,
                "scheduler": "PBS",
                "seed": seed,
                "traffic_multiplier": multiplier,
                "solution_id": 1,
                "pareto_front_size": 1,
                **pbs_metrics,
            })

            seed_level_results.append({
                "scenario": scenario,
                "scheduler": "PBS",
                "seed": seed,
                **{
                    metric: float(pbs_metrics[metric])
                    for metric in METRIC_NAMES
                },
            })

            completed_runs += 1

            print(
                f"PBS completed | Throughput: "
                f"{pbs_metrics['throughput']:.2f} | "
                f"Fairness: "
                f"{pbs_metrics['jain_fairness_index']:.4f}"
            )

            # NSGA-II experiment
            print("\nRunning NSGA-II...")

            pareto_solutions = run_nsga2(seed, multiplier)

            for index, solution in enumerate(
                pareto_solutions,
                start=1,
            ):
                raw_rows.append({
                    "scenario": scenario,
                    "scheduler": "NSGA-II",
                    "seed": seed,
                    "traffic_multiplier": multiplier,
                    "solution_id": index,
                    "pareto_front_size": len(pareto_solutions),
                    **solution["metrics"],
                })

            front_mean = mean_metrics(pareto_solutions)

            seed_level_results.append({
                "scenario": scenario,
                "scheduler": "NSGA-II",
                "seed": seed,
                **front_mean,
            })

            completed_runs += 1

            print(
                f"\nNSGA-II completed | "
                f"Pareto solutions: {len(pareto_solutions)}"
            )

            print(
                f"Front mean throughput: "
                f"{front_mean['throughput']:.2f}"
            )

            print(
                f"Front mean fairness: "
                f"{front_mean['jain_fairness_index']:.4f}"
            )

            print(
                f"\nCompleted scheduler runs: "
                f"{completed_runs}/{total_runs}"
            )

    raw_output = (
        results_directory / "multiseed_raw_results.csv"
    )

    summary_output = (
        results_directory / "multiseed_summary.csv"
    )

    save_raw_results(raw_rows, raw_output)

    save_summary(
        seed_level_results,
        summary_output,
    )

    print("\n" + "=" * 65)
    print("MULTI-SEED VALIDATION COMPLETED")
    print("=" * 65)

    print(f"Total scheduler runs: {completed_runs}")
    print(f"Raw results saved   : {raw_output}")
    print(f"Summary saved       : {summary_output}")

    print("\nSummary: Mean and Sample Standard Deviation")
    print("-" * 65)

    for result in seed_level_results:
        print(
            f"{result['scenario']:<8} "
            f"{result['scheduler']:<10} "
            f"Seed {result['seed']:<5} "
            f"Throughput {result['throughput']:.2f} "
            f"Fairness {result['jain_fairness_index']:.4f}"
        )


if __name__ == "__main__":
    main()
