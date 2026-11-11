"""
Run the complete Tactical WiMAX QoS Optimization project.

Place this file in the project root folder (the same folder that contains src/ and results/).
Run from PowerShell:
    python run_all.py
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

PIPELINE = [
    ("Normal traffic: NSGA-II optimization", "src/optimization/run_nsga2.py"),
    ("Normal traffic: Priority-Based Scheduler", "src/optimization/run_priority.py"),
    ("Normal traffic: Scheduler comparison", "src/optimization/compare_schedulers.py"),
    ("High traffic: NSGA-II optimization", "src/optimization/run_high_traffic_nsga2.py"),
    ("High traffic: Priority-Based Scheduler", "src/optimization/run_high_traffic_priority.py"),
    ("High traffic: Scheduler comparison", "src/optimization/compare_high_traffic_schedulers.py"),
    ("Multi-seed robustness validation", "src/optimization/run_multiseed_validation.py"),
    ("Generate project graphs", "src/optimization/generate_project_graphs.py"),
]


def main():
    os.environ["PYTHONPATH"] = str(PROJECT_ROOT / "src") + os.pathsep + os.environ.get(
        "PYTHONPATH", ""
    )

    print("=" * 72)
    print("TACTICAL WiMAX QoS OPTIMIZATION — COMPLETE PROJECT RUN")
    print(f"Project folder: {PROJECT_ROOT}")
    print("=" * 72)

    for index, (description, script_relative) in enumerate(PIPELINE, start=1):
        script_path = PROJECT_ROOT / script_relative

        if not script_path.is_file():
            print(f"\nERROR: Required script not found:\n  {script_path}")
            sys.exit(1)

        print(f"\n[{index}/{len(PIPELINE)}] {description}")
        print("-" * 72)

        # check=True stops the pipeline immediately if any script fails.
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
            check=True,
        )

    print("\n" + "=" * 72)
    print("COMPLETE PROJECT RUN FINISHED SUCCESSFULLY")
    print("Results and graph files have been generated in the project's results/ folder.")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print("\nPIPELINE STOPPED: A script failed.")
        print(f"Failed script: {error.cmd}")
        print(f"Exit code: {error.returncode}")
        sys.exit(error.returncode)
