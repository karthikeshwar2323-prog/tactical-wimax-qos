
import random
from math import inf


class NSGA2:
    """
    NSGA-II multi-objective evolutionary optimizer.

    The optimizer minimizes all objectives internally. The objective
    evaluator must return a dictionary containing:
        throughput
        average_delay
        packet_loss_ratio
        jain_fairness_index
        resource_utilization

    Throughput, fairness, and utilization are maximized.
    Delay and packet loss are minimized.
    """

    OBJECTIVE_NAMES = (
        "throughput",
        "average_delay",
        "packet_loss_ratio",
        "jain_fairness_index",
        "resource_utilization",
    )

    def __init__(
        self,
        network,
        objective_evaluator,
        population_size=40,
        generations=50,
        crossover_probability=0.9,
        mutation_probability=None,
        seed=42,
    ):
        if population_size < 2:
            raise ValueError("population_size must be at least 2.")

        if generations < 1:
            raise ValueError("generations must be at least 1.")

        if not 0 <= crossover_probability <= 1:
            raise ValueError(
                "crossover_probability must be between 0 and 1."
            )

        self.network = network
        self.objective_evaluator = objective_evaluator
        self.population_size = population_size
        self.generations = generations
        self.crossover_probability = crossover_probability
        self.seed = seed
        self.rng = random.Random(seed)

        self.users = network.users
        self.total_resources = float(network.total_resources)

        if not self.users:
            raise ValueError("The network must contain at least one user.")

        if self.total_resources <= 0:
            raise ValueError("Total resources must be positive.")

        self.lower_bounds = [0.0 for _ in self.users]
        self.upper_bounds = [
            float(user.required_bandwidth) for user in self.users
        ]

        if any(bound < 0 for bound in self.upper_bounds):
            raise ValueError("Required bandwidth cannot be negative.")

        self.mutation_probability = (
            mutation_probability
            if mutation_probability is not None
            else 1.0 / len(self.users)
        )

        if not 0 <= self.mutation_probability <= 1:
            raise ValueError(
                "mutation_probability must be between 0 and 1."
            )

        self.history = []

    def _repair(self, allocation):
        """
        Enforce gene bounds and the total resource budget.

        Allocations are nonnegative and cannot exceed each user's
        required bandwidth. If their sum exceeds the budget, all
        allocations are proportionally scaled down.
        """
        repaired = [
            min(max(float(value), low), high)
            for value, low, high in zip(
                allocation,
                self.lower_bounds,
                self.upper_bounds,
            )
        ]

        total = sum(repaired)

        if total > self.total_resources:
            scale = self.total_resources / total
            repaired = [value * scale for value in repaired]

        return repaired

    def _random_individual(self):
        """Generate a feasible random resource allocation."""
        allocation = [
            self.rng.uniform(low, high)
            for low, high in zip(
                self.lower_bounds,
                self.upper_bounds,
            )
        ]

        return self._repair(allocation)

    @staticmethod
    def _to_minimization_objectives(metrics):
        """Convert all five objectives to minimization form."""
        missing = [
            name
            for name in NSGA2.OBJECTIVE_NAMES
            if name not in metrics
        ]

        if missing:
            raise ValueError(
                "Objective evaluator is missing metrics: "
                + ", ".join(missing)
            )

        throughput = float(metrics["throughput"])
        delay = float(metrics["average_delay"])
        loss = float(metrics["packet_loss_ratio"])
        fairness = float(metrics["jain_fairness_index"])
        utilization = float(metrics["resource_utilization"])

        values = [
            throughput,
            delay,
            loss,
            fairness,
            utilization,
        ]

        if any(
            value != value or abs(value) == inf
            for value in values
        ):
            raise ValueError(
                "Objective metrics must be finite numbers."
            )

        if throughput < 0 or delay < 0:
            raise ValueError(
                "Throughput and delay cannot be negative."
            )

        if not 0 <= loss <= 1:
            raise ValueError(
                "Packet loss ratio must be between 0 and 1."
            )

        if not 0 <= fairness <= 1:
            raise ValueError(
                "Jain's fairness index must be between 0 and 1."
            )

        if not 0 <= utilization <= 1:
            raise ValueError(
                "Resource utilization must be between 0 and 1."
            )

        return (
            -throughput,
            delay,
            loss,
            -fairness,
            -utilization,
        )

    def _evaluate(self, individual):
        """Evaluate an allocation using the supplied network simulator."""
        metrics = self.objective_evaluator(individual[:])

        if not isinstance(metrics, dict):
            raise TypeError(
                "objective_evaluator must return a metrics dictionary."
            )

        individual_metrics = dict(metrics)
        objectives = self._to_minimization_objectives(metrics)

        return {
            "allocation": individual[:],
            "metrics": individual_metrics,
            "objectives": objectives,
            "rank": None,
            "crowding_distance": 0.0,
        }

    @staticmethod
    def _dominates(first, second):
        """Return True if first Pareto-dominates second."""
        first_values = first["objectives"]
        second_values = second["objectives"]

        no_worse = all(
            a <= b for a, b in zip(first_values, second_values)
        )

        strictly_better = any(
            a < b for a, b in zip(first_values, second_values)
        )

        return no_worse and strictly_better

    def _fast_non_dominated_sort(self, population):
        """Partition a population into Pareto fronts."""
        domination_counts = [0] * len(population)
        dominated_solutions = [[] for _ in population]
        fronts = [[]]

        for i, first in enumerate(population):
            for j, second in enumerate(population):
                if i == j:
                    continue

                if self._dominates(first, second):
                    dominated_solutions[i].append(j)
                elif self._dominates(second, first):
                    domination_counts[i] += 1

            if domination_counts[i] == 0:
                first["rank"] = 0
                fronts[0].append(i)

        front_index = 0

        while front_index < len(fronts) and fronts[front_index]:
            next_front = []

            for i in fronts[front_index]:
                for j in dominated_solutions[i]:
                    domination_counts[j] -= 1

                    if domination_counts[j] == 0:
                        population[j]["rank"] = front_index + 1
                        next_front.append(j)

            if next_front:
                fronts.append(next_front)

            front_index += 1

        return [
            [population[index] for index in front]
            for front in fronts
        ]

    def _calculate_crowding_distance(self, front):
        """Estimate solution isolation within a Pareto front."""
        for individual in front:
            individual["crowding_distance"] = 0.0

        if len(front) <= 2:
            for individual in front:
                individual["crowding_distance"] = inf
            return

        number_of_objectives = len(front[0]["objectives"])

        for objective_index in range(number_of_objectives):
            sorted_front = sorted(
                front,
                key=lambda item: item["objectives"][objective_index],
            )

            sorted_front[0]["crowding_distance"] = inf
            sorted_front[-1]["crowding_distance"] = inf

            minimum = sorted_front[0]["objectives"][objective_index]
            maximum = sorted_front[-1]["objectives"][objective_index]

            if maximum == minimum:
                continue

            for index in range(1, len(sorted_front) - 1):
                individual = sorted_front[index]

                if individual["crowding_distance"] == inf:
                    continue

                previous_value = sorted_front[index - 1][
                    "objectives"
                ][objective_index]

                next_value = sorted_front[index + 1][
                    "objectives"
                ][objective_index]

                individual["crowding_distance"] += (
                    next_value - previous_value
                ) / (maximum - minimum)

    def _rank_population(self, population):
        """Assign Pareto ranks and crowding distances."""
        fronts = self._fast_non_dominated_sort(population)

        for front in fronts:
            self._calculate_crowding_distance(front)

        return fronts

    def _tournament_selection(self, population):
        """Select a parent using rank and crowding distance."""
        first = self.rng.choice(population)
        second = self.rng.choice(population)

        if first["rank"] < second["rank"]:
            return first

        if second["rank"] < first["rank"]:
            return second

        if first["crowding_distance"] > second["crowding_distance"]:
            return first

        if second["crowding_distance"] > first["crowding_distance"]:
            return second

        return self.rng.choice([first, second])

    def _crossover(self, first, second):
        """
        Perform blend crossover on two real-valued allocations.

        Both offspring are repaired to respect allocation bounds
        and the total resource budget.
        """
        child_one = []
        child_two = []

        for value_one, value_two in zip(
            first["allocation"],
            second["allocation"],
        ):
            if self.rng.random() <= self.crossover_probability:
                alpha = self.rng.random()

                new_one = (
                    alpha * value_one + (1 - alpha) * value_two
                )

                new_two = (
                    alpha * value_two + (1 - alpha) * value_one
                )
            else:
                new_one = value_one
                new_two = value_two

            child_one.append(new_one)
            child_two.append(new_two)

        return self._repair(child_one), self._repair(child_two)

    def _mutate(self, allocation):
        """Apply bounded Gaussian mutation to allocation genes."""
        mutated = allocation[:]

        for index, value in enumerate(mutated):
            if self.rng.random() > self.mutation_probability:
                continue

            low = self.lower_bounds[index]
            high = self.upper_bounds[index]

            if high <= low:
                mutated[index] = low
                continue

            standard_deviation = (high - low) * 0.1

            mutated[index] = value + self.rng.gauss(
                0.0,
                standard_deviation,
            )

        return self._repair(mutated)

    def _make_offspring(self, population):
        """Create and evaluate the next offspring population."""
        offspring = []

        while len(offspring) < self.population_size:
            parent_one = self._tournament_selection(population)
            parent_two = self._tournament_selection(population)

            child_one, child_two = self._crossover(
                parent_one,
                parent_two,
            )

            child_one = self._mutate(child_one)
            child_two = self._mutate(child_two)

            offspring.append(self._evaluate(child_one))

            if len(offspring) < self.population_size:
                offspring.append(self._evaluate(child_two))

        return offspring

    def _environmental_selection(self, combined_population):
        """Select the next generation using NSGA-II ranking."""
        fronts = self._rank_population(combined_population)
        selected = []

        for front in fronts:
            remaining = self.population_size - len(selected)

            if remaining <= 0:
                break

            if len(front) <= remaining:
                selected.extend(front)
            else:
                front.sort(
                    key=lambda item: item["crowding_distance"],
                    reverse=True,
                )
                selected.extend(front[:remaining])
                break

        return selected

    def optimize(self):
        """
        Run NSGA-II and return the final non-dominated solutions.

        The objective evaluator must independently evaluate each
        candidate allocation using a consistent simulation scenario.
        """
        self.history = []

        population = [
            self._evaluate(self._random_individual())
            for _ in range(self.population_size)
        ]

        for generation in range(self.generations):
            self._rank_population(population)

            offspring = self._make_offspring(population)
            combined = population + offspring

            population = self._environmental_selection(combined)

            fronts = self._rank_population(population)
            first_front = fronts[0] if fronts else []

            self.history.append(
                {
                    "generation": generation + 1,
                    "population_size": len(population),
                    "pareto_front_size": len(first_front),
                }
            )

            print(
                f"Generation {generation + 1:>3}/{self.generations} | "
                f"Pareto solutions: {len(first_front)}"
            )

        final_fronts = self._rank_population(population)
        final_front = final_fronts[0] if final_fronts else []

        return [
            {
                "allocation": item["allocation"][:],
                "metrics": dict(item["metrics"]),
                "rank": item["rank"],
                "crowding_distance": item["crowding_distance"],
            }
            for item in final_front
        ]
