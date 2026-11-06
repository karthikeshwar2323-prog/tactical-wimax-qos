
import pandas as pd
from pathlib import Path


def main():

    nsga_file = Path("results/nsga2_high_traffic_results.csv")
    pbs_file = Path("results/pbs_high_traffic_results.csv")

    output_file = Path("results/high_traffic_scheduler_comparison.csv")

    # Check input files
    if not nsga_file.exists():
        raise FileNotFoundError(f"Missing file: {nsga_file}")

    if not pbs_file.exists():
        raise FileNotFoundError(f"Missing file: {pbs_file}")

    # Read experiment results
    nsga = pd.read_csv(nsga_file)
    pbs = pd.read_csv(pbs_file)

    metrics = [
        "throughput",
        "average_delay",
        "packet_loss_ratio",
        "jain_fairness_index",
        "resource_allocation_ratio"
    ]

    # Validate required columns
    for column in metrics:
        if column not in nsga.columns or column not in pbs.columns:
            raise ValueError(f"Missing required metric: {column}")

    if len(pbs) != 1:
        raise ValueError("Expected exactly one PBS baseline row.")

    baseline = pbs.iloc[0]

    # Build comparison table
    rows = []

    rows.append({
        "solution": "PBS Baseline",
        **{metric: baseline[metric] for metric in metrics}
    })

    for index, solution in nsga.iterrows():

        row = {
            "solution": f"NSGA-II-{index + 1}"
        }

        for metric in metrics:
            row[metric] = solution[metric]

        rows.append(row)

    comparison = pd.DataFrame(rows)

    # Calculate difference from PBS
    for metric in metrics:
        comparison[f"{metric}_difference"] = (
            comparison[metric] - baseline[metric]
        )

    # Save results separately
    comparison.to_csv(output_file, index=False)

    # Display readable comparison
    print("\n========== HIGH-TRAFFIC SCHEDULER COMPARISON ==========")

    print(
        comparison[
            [
                "solution",
                "throughput",
                "average_delay",
                "packet_loss_ratio",
                "jain_fairness_index",
                "resource_allocation_ratio"
            ]
        ].round(4).to_string(index=False)
    )

    print("\n========== BEST NSGA-II RESULTS ==========")

    print("Highest throughput:",
          nsga["throughput"].max())

    print("Lowest average delay:",
          nsga["average_delay"].min())

    print("Lowest packet loss:",
          nsga["packet_loss_ratio"].min())

    print("Highest fairness:",
          nsga["jain_fairness_index"].max())

    print("\nTotal NSGA-II solutions:", len(nsga))

    print("\nComparison saved to:", output_file)


if __name__ == "__main__":
    main()
