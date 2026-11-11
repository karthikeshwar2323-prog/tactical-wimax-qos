
from pathlib import Path

import sys
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

SUMMARY_FILE = RESULTS / "multiseed_summary.csv"

PARETO_FILES = {
    "Normal Traffic": RESULTS / "nsga2_pareto_solutions.csv",
    "High Traffic": RESULTS / "nsga2_high_traffic_results.csv",
}

GRAPH_FILES = [
    "normal_scheduler_comparison.png",
    "high_traffic_scheduler_comparison.png",
    "high_traffic_pareto_throughput_fairness.png",
    "high_traffic_pareto_throughput_packet_loss.png",
    "normal_multiseed_validation.png",
    "high_traffic_multiseed_validation.png",
]

METRICS = {
    "throughput": "Throughput",
    "average_delay": "Average Delay",
    "packet_loss_ratio": "Packet Loss",
    "jain_fairness_index": "Jain Fairness",
    "resource_utilization_ratio": "Resource Utilization",
    "resource_allocation_ratio": "Resource Allocation",
}


# ---------------------------------------------------------
# FORMATTING
# ---------------------------------------------------------

def format_metric(metric, mean, std):
    if metric in (
        "packet_loss_ratio",
        "resource_utilization_ratio",
        "resource_allocation_ratio",
    ):
        return f"{mean * 100:.2f}% +/- {std * 100:.2f}%"

    if metric == "throughput":
        return f"{mean:,.2f} +/- {std:,.2f}"

    return f"{mean:.4f} +/- {std:.4f}"


def print_heading(title):
    print("\n" + "=" * 76)
    print(title)
    print("=" * 76)


# ---------------------------------------------------------
# CHECK REQUIRED FILES
# ---------------------------------------------------------

def check_files():
    required_files = [
        SUMMARY_FILE,
        PARETO_FILES["Normal Traffic"],
        PARETO_FILES["High Traffic"],
    ]

    missing = [file for file in required_files if not file.exists()]

    if missing:
        print("\nERROR: Required project result files are missing.")

        for file in missing:
            print(f"Missing: {file.relative_to(ROOT)}")

        print("\nRun the complete project pipeline first.")
        sys.exit(1)


# ---------------------------------------------------------
# MULTI-SEED AVERAGE AND STANDARD DEVIATION
# ---------------------------------------------------------

def show_average_results():
    print_heading("MULTI-SEED VALIDATION: AVERAGE RESULTS")

    df = pd.read_csv(SUMMARY_FILE)

    required_columns = {
        "scenario",
        "scheduler",
        "metric",
        "seed_count",
        "mean",
        "sample_std_dev",
    }

    if not required_columns.issubset(df.columns):
        raise ValueError(
            "Unexpected columns in multiseed_summary.csv"
        )

    for scenario in ["Normal", "High"]:
        print(f"\nSCENARIO: {scenario.upper()} TRAFFIC")
        print("-" * 76)

        scenario_data = df[df["scenario"].str.lower() == scenario.lower()]

        for metric, label in METRICS.items():
            metric_data = scenario_data[
                scenario_data["metric"] == metric
            ]

            if metric_data.empty:
                continue

            print(f"\n{label}")

            for scheduler in ["PBS", "NSGA-II"]:
                row = metric_data[
                    metric_data["scheduler"] == scheduler
                ]

                if row.empty:
                    print(f"  {scheduler:<10} Data unavailable")
                    continue

                mean = float(row.iloc[0]["mean"])
                std = float(row.iloc[0]["sample_std_dev"])
                seeds = int(row.iloc[0]["seed_count"])

                result = format_metric(metric, mean, std)

                print(
                    f"  {scheduler:<10} {result} "
                    f"(seeds: {seeds})"
                )


# ---------------------------------------------------------
# PARETO FRONT SUMMARY
# ---------------------------------------------------------

def show_pareto_results():
    print_heading("NSGA-II PARETO FRONT SUMMARY")

    for scenario, file_path in PARETO_FILES.items():
        print(f"\n{scenario.upper()}")
        print("-" * 76)

        df = pd.read_csv(file_path)

        required = [
            "throughput",
            "average_delay",
            "packet_loss_ratio",
            "jain_fairness_index",
        ]

        missing = [column for column in required if column not in df.columns]

        if missing:
            print(f"Required columns missing: {missing}")
            continue

        print(f"Number of Pareto solutions: {len(df)}")

        print(
            f"Throughput range: "
            f"{df['throughput'].min():,.2f} - "
            f"{df['throughput'].max():,.2f}"
        )

        print(
            f"Average delay range: "
            f"{df['average_delay'].min():.4f} - "
            f"{df['average_delay'].max():.4f}"
        )

        print(
            f"Packet loss range: "
            f"{df['packet_loss_ratio'].min() * 100:.3f}% - "
            f"{df['packet_loss_ratio'].max() * 100:.3f}%"
        )

        print(
            f"Fairness range: "
            f"{df['jain_fairness_index'].min():.4f} - "
            f"{df['jain_fairness_index'].max():.4f}"
        )


# ---------------------------------------------------------
# DISPLAY PROJECT GRAPHS
# ---------------------------------------------------------

def show_graphs():
    print_heading("PROJECT GRAPHS")

    available_graphs = []

    for filename in GRAPH_FILES:
        graph_path = RESULTS / filename

        if graph_path.exists():
            available_graphs.append(graph_path)
            print(f"Available: {filename}")
        else:
            print(f"Missing: {filename}")

    if not available_graphs:
        print("\nNo project graphs are available.")
        return

    count = len(available_graphs)

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(18, 10)
    )

    axes = axes.flatten()

    for index, ax in enumerate(axes):
        if index < count:
            image = plt.imread(available_graphs[index])

            ax.imshow(image)
            ax.set_title(
                available_graphs[index].stem.replace("_", " ").title(),
                fontsize=10
            )
            ax.axis("off")
        else:
            ax.axis("off")

    fig.suptitle(
        "Tactical WiMAX QoS Optimization - Project Results",
        fontsize=16
    )

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------
# MAIN DEMONSTRATION
# ---------------------------------------------------------

def main():
    print("\n")
    print("=" * 76)
    print("TACTICAL WiMAX NETWORK QoS OPTIMIZATION")
    print("MULTI-OBJECTIVE EVOLUTIONARY SCHEDULING USING NSGA-II")
    print("=" * 76)

    print("\nDemonstration mode: Reading previously generated results.")
    print("No simulations or optimization runs will be started.")

    check_files()

    show_average_results()

    show_pareto_results()

    show_graphs()

    print_heading("DEMONSTRATION COMPLETED")
    print("All available project results have been displayed.")
    print("These results are from network simulation, not physical WiMAX hardware.")


if __name__ == "__main__":
    main()
