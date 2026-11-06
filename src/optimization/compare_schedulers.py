
import csv
from pathlib import Path


RESULTS_DIR = Path("results")

NSGA2_FILE = RESULTS_DIR / "nsga2_pareto_solutions.csv"
PBS_FILE = RESULTS_DIR / "pbs_baseline_results.csv"
OUTPUT_FILE = RESULTS_DIR / "scheduler_comparison.csv"


# NSGA-II objectives plus the resource allocation metric.
METRICS = [
    "throughput",
    "average_delay",
    "packet_loss_ratio",
    "jain_fairness_index",
    "resource_utilization_ratio",
    "resource_allocation_ratio"
]


def read_csv_file(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required results file not found: {file_path}"
        )

    with file_path.open("r", newline="") as file:
        return list(csv.DictReader(file))


def validate_columns(results, file_path):

    if not results:
        raise ValueError(
            f"Results file is empty: {file_path}"
        )

    required_columns = set(METRICS)
    available_columns = set(results[0].keys())

    missing_columns = required_columns - available_columns

    if missing_columns:
        raise ValueError(
            f"Missing columns in {file_path}: "
            f"{', '.join(sorted(missing_columns))}"
        )


def main():

    nsga2_results = read_csv_file(NSGA2_FILE)
    pbs_results = read_csv_file(PBS_FILE)

    validate_columns(nsga2_results, NSGA2_FILE)
    validate_columns(pbs_results, PBS_FILE)

    if len(pbs_results) != 1:
        raise ValueError(
            "PBS results file must contain exactly one result."
        )

    pbs = {
        metric: float(pbs_results[0][metric])
        for metric in METRICS
    }

    comparison_rows = []

    # Add PBS baseline.
    pbs_row = {
        "solution": "PBS Baseline",
        "scheduler": "PBS"
    }

    for metric in METRICS:
        pbs_row[metric] = pbs[metric]
        pbs_row[f"{metric}_difference_vs_pbs"] = 0.0

    comparison_rows.append(pbs_row)

    # Compare every NSGA-II Pareto solution against PBS.
    for index, solution in enumerate(nsga2_results, start=1):

        row = {
            "solution": f"NSGA-II-{index}",
            "scheduler": "NSGA-II"
        }

        for metric in METRICS:

            nsga_value = float(solution[metric])

            row[metric] = nsga_value

            row[f"{metric}_difference_vs_pbs"] = (
                nsga_value - pbs[metric]
            )

        comparison_rows.append(row)

    # Save consolidated comparison.
    fieldnames = [
        "solution",
        "scheduler"
    ]

    for metric in METRICS:
        fieldnames.append(metric)
        fieldnames.append(
            f"{metric}_difference_vs_pbs"
        )

    with OUTPUT_FILE.open("w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(comparison_rows)

    print("\n========== Scheduler Comparison ==========")

    print(
        f"{'Solution':<15}"
        f"{'Throughput':<15}"
        f"{'Delay':<12}"
        f"{'Fairness':<12}"
        f"{'Loss':<10}"
        f"{'Utilization':<12}"
    )

    print("-" * 76)

    for row in comparison_rows:

        print(
            f"{row['solution']:<15}"
            f"{float(row['throughput']):<15.2f}"
            f"{float(row['average_delay']):<12.4f}"
            f"{float(row['jain_fairness_index']):<12.4f}"
            f"{float(row['packet_loss_ratio']):<10.4f}"
            f"{float(row['resource_utilization_ratio']):<12.4f}"
        )

    print("\nTotal solutions compared:", len(comparison_rows))
    print("NSGA-II solutions:", len(nsga2_results))
    print("PBS baseline solutions:", len(pbs_results))
    print("Comparison saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
