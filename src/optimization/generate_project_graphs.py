
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# Project paths
ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
DPI = 300

# Existing experiment files
normal_comparison_file = RESULTS / "scheduler_comparison.csv"
high_comparison_file = RESULTS / "high_traffic_scheduler_comparison.csv"
high_nsga_file = RESULTS / "nsga2_high_traffic_results.csv"
high_pbs_file = RESULTS / "pbs_high_traffic_results.csv"

# Multi-seed validation file
multiseed_summary_file = RESULTS / "multiseed_summary.csv"


def load_csv(path, required_columns):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    data = pd.read_csv(path)

    missing = set(required_columns) - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing columns in {path.name}: {sorted(missing)}"
        )

    return data


def save_figure(fig, filename):
    output = RESULTS / filename

    fig.savefig(
        output,
        dpi=DPI,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Generated: {output.relative_to(ROOT)}")


def normal_traffic_comparison():
    """Generate the existing normal-traffic comparison graph."""

    df = load_csv(
        normal_comparison_file,
        [
            "solution",
            "throughput",
            "jain_fairness_index",
        ],
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(15, 6),
    )

    axes[0].bar(
        df["solution"],
        df["throughput"],
    )

    axes[0].set_title("Throughput Comparison")
    axes[0].set_ylabel("Throughput (bits per time unit)")
    axes[0].set_xlabel("Scheduling solution")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].grid(axis="y", linestyle="--", alpha=0.4)

    axes[1].bar(
        df["solution"],
        df["jain_fairness_index"],
    )

    axes[1].set_title("Jain's Fairness Index")
    axes[1].set_ylabel("Fairness index")
    axes[1].set_xlabel("Scheduling solution")
    axes[1].set_ylim(0, 1)
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle(
        "PBS vs NSGA-II Under Normal Traffic",
        fontsize=15,
    )

    fig.tight_layout()

    save_figure(
        fig,
        "normal_scheduler_comparison.png",
    )


def high_traffic_comparison():
    """Generate the existing high-traffic comparison graph."""

    df = load_csv(
        high_comparison_file,
        [
            "solution",
            "throughput",
            "jain_fairness_index",
        ],
    )

    selected = [
        "PBS Baseline",
        "NSGA-II-3",
        "NSGA-II-4",
        "NSGA-II-5",
        "NSGA-II-8",
    ]

    df = df[df["solution"].isin(selected)].copy()

    if set(df["solution"]) != set(selected):
        raise ValueError(
            "One or more selected high-traffic solutions are missing."
        )

    df["solution"] = pd.Categorical(
        df["solution"],
        categories=selected,
        ordered=True,
    )

    df = df.sort_values("solution")

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(13, 6),
    )

    axes[0].bar(
        df["solution"],
        df["throughput"],
    )

    axes[0].set_title("Throughput Under High Traffic")
    axes[0].set_ylabel("Throughput (bits per time unit)")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].grid(axis="y", linestyle="--", alpha=0.4)

    axes[1].bar(
        df["solution"],
        df["jain_fairness_index"],
    )

    axes[1].set_title("Fairness Under High Traffic")
    axes[1].set_ylabel("Jain Fairness Index")
    axes[1].set_ylim(0, 1)
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle(
        "PBS vs Representative NSGA-II Solutions Under High Traffic",
        fontsize=14,
    )

    fig.tight_layout()

    save_figure(
        fig,
        "high_traffic_scheduler_comparison.png",
    )


def high_traffic_pareto_plots():
    """Generate the existing high-traffic Pareto graphs."""

    nsga = load_csv(
        high_nsga_file,
        [
            "throughput",
            "jain_fairness_index",
            "packet_loss_ratio",
        ],
    )

    pbs = load_csv(
        high_pbs_file,
        [
            "throughput",
            "jain_fairness_index",
            "packet_loss_ratio",
        ],
    ).iloc[0]

    # Graph 1: Throughput versus fairness
    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        nsga["throughput"],
        nsga["jain_fairness_index"],
        s=65,
        label="NSGA-II Pareto solutions",
    )

    ax.scatter(
        pbs["throughput"],
        pbs["jain_fairness_index"],
        marker="*",
        s=220,
        label="PBS baseline",
    )

    balanced = nsga.iloc[7]

    ax.annotate(
        "NSGA-II-8 (balanced)",
        (
            balanced["throughput"],
            balanced["jain_fairness_index"],
        ),
        xytext=(8, 8),
        textcoords="offset points",
    )

    ax.set_title(
        "High-Traffic Pareto Analysis: Throughput vs Fairness"
    )

    ax.set_xlabel("Throughput (bits per time unit)")
    ax.set_ylabel("Jain Fairness Index")
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()

    fig.tight_layout()

    save_figure(
        fig,
        "high_traffic_pareto_throughput_fairness.png",
    )

    # Graph 2: Throughput versus packet loss
    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        nsga["throughput"],
        nsga["packet_loss_ratio"],
        s=65,
        label="NSGA-II Pareto solutions",
    )

    ax.scatter(
        pbs["throughput"],
        pbs["packet_loss_ratio"],
        marker="*",
        s=220,
        label="PBS baseline",
    )

    best_loss = nsga.loc[
        nsga["packet_loss_ratio"].idxmin()
    ]

    ax.annotate(
        "Lowest-loss NSGA-II solution",
        (
            best_loss["throughput"],
            best_loss["packet_loss_ratio"],
        ),
        xytext=(8, 8),
        textcoords="offset points",
    )

    ax.set_title(
        "High-Traffic Pareto Analysis: Throughput vs Packet Loss"
    )

    ax.set_xlabel("Throughput (bits per time unit)")
    ax.set_ylabel("Packet Loss Ratio")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()

    fig.tight_layout()

    save_figure(
        fig,
        "high_traffic_pareto_throughput_packet_loss.png",
    )


def multiseed_validation_plots():
    """
    Generate normal- and high-traffic comparisons using
    mean and sample standard deviation across five seeds.

    NSGA-II values represent the mean of each seed's
    Pareto front, followed by aggregation across seeds.
    """

    df = load_csv(
        multiseed_summary_file,
        [
            "scenario",
            "scheduler",
            "metric",
            "seed_count",
            "mean",
            "sample_std_dev",
        ],
    )

    expected_scenarios = ["Normal", "High"]
    expected_schedulers = ["PBS", "NSGA-II"]

    metric_configuration = [
        {
            "name": "throughput",
            "title": "Throughput",
            "ylabel": "Bits per time unit",
            "multiplier": 1,
        },
        {
            "name": "average_delay",
            "title": "Average Delay",
            "ylabel": "Time units",
            "multiplier": 1,
        },
        {
            "name": "packet_loss_ratio",
            "title": "Packet Loss",
            "ylabel": "Packet loss (%)",
            "multiplier": 100,
        },
        {
            "name": "jain_fairness_index",
            "title": "Jain's Fairness Index",
            "ylabel": "Fairness index",
            "multiplier": 1,
        },
        {
            "name": "resource_allocation_ratio",
            "title": "Resource Allocation Ratio",
            "ylabel": "Allocation ratio",
            "multiplier": 1,
        },
        {
            "name": "resource_utilization_ratio",
            "title": "Resource Utilization",
            "ylabel": "Utilization ratio",
            "multiplier": 1,
        },
    ]

    for scenario in expected_scenarios:

        scenario_data = df[
            df["scenario"] == scenario
        ].copy()

        if scenario_data.empty:
            raise ValueError(
                f"No multi-seed results found for {scenario} traffic."
            )

        fig, axes = plt.subplots(
            2,
            3,
            figsize=(16, 9),
        )

        for ax, metric in zip(
            axes.flat,
            metric_configuration,
        ):

            metric_data = scenario_data[
                scenario_data["metric"] == metric["name"]
            ]

            if set(metric_data["scheduler"]) != set(
                expected_schedulers
            ):
                raise ValueError(
                    f"Missing scheduler results for "
                    f"{scenario} / {metric['name']}."
                )

            metric_data = metric_data.set_index("scheduler")

            if (
                metric_data.loc["PBS", "seed_count"] != 5
                or metric_data.loc["NSGA-II", "seed_count"] != 5
            ):
                raise ValueError(
                    f"Expected five seeds for "
                    f"{scenario} / {metric['name']}."
                )

            means = [
                metric_data.loc[scheduler, "mean"]
                * metric["multiplier"]
                for scheduler in expected_schedulers
            ]

            deviations = [
                metric_data.loc[scheduler, "sample_std_dev"]
                * metric["multiplier"]
                for scheduler in expected_schedulers
            ]

            positions = [0, 1]

            ax.bar(
                positions,
                means,
                yerr=deviations,
                capsize=6,
            )

            ax.set_xticks(positions)
            ax.set_xticklabels(expected_schedulers)

            ax.set_title(metric["title"])
            ax.set_ylabel(metric["ylabel"])

            ax.grid(
                axis="y",
                linestyle="--",
                alpha=0.4,
            )

            if metric["name"] == "jain_fairness_index":
                ax.set_ylim(0, 1)

            elif metric["name"] in (
                "resource_allocation_ratio",
                "resource_utilization_ratio",
            ):
                ax.set_ylim(0, 1.1)

            # Display the mean value above each bar.
            for position, value in zip(positions, means):
                ax.annotate(
                    f"{value:.4f}" if value < 10 else f"{value:.1f}",
                    (position, value),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                )

        fig.suptitle(
            f"Multi-Seed Validation: PBS vs NSGA-II "
            f"({scenario} Traffic)\n"
            "Mean ± Sample Standard Deviation | 5 Seeds",
            fontsize=15,
        )

        fig.tight_layout(
            rect=[0, 0, 1, 0.93]
        )

        filename = (
            "normal_multiseed_validation.png"
            if scenario == "Normal"
            else "high_traffic_multiseed_validation.png"
        )

        save_figure(fig, filename)


def main():

    RESULTS.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Generating final project visualizations...\n")

    normal_traffic_comparison()
    high_traffic_comparison()
    high_traffic_pareto_plots()
    multiseed_validation_plots()

    print("\nAll six project graphs generated successfully.")


if __name__ == "__main__":
    main()
