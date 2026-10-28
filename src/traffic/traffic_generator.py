
import random


class TrafficGenerator:
    """
    Generates packet arrivals for Tactical WiMAX users.

    The arrival rate represents the expected number of packets
    arriving per simulation time unit.
    """

    def __init__(self, seed=42):
        self.rng = random.Random(seed)

    def generate_arrivals(self, user, time_step=1.0):
        """
        Generate arrivals for one user during a time step.

        Uses a Poisson distribution approximation through
        a sum of independent Bernoulli trials when the expected
        arrival count is small, and a normal approximation for
        larger arrival counts.
        """
        if time_step < 0:
            raise ValueError("time_step cannot be negative.")

        if user.packet_arrival_rate < 0:
            raise ValueError("Packet arrival rate cannot be negative.")

        expected = user.packet_arrival_rate * time_step

        if expected == 0:
            return 0

        # Exact Poisson sampling using Knuth's algorithm
        # for practical arrival rates.
        if expected <= 30:
            threshold = self._exp_negative(expected)
            product = 1.0
            count = 0

            while product > threshold:
                count += 1
                product *= self.rng.random()

            return count - 1

        # Normal approximation to Poisson for larger means.
        # Round to the nearest nonnegative integer.
        sample = self.rng.gauss(expected, expected ** 0.5)
        return max(0, int(sample + 0.5))

    @staticmethod
    def _exp_negative(value):
        """Return exp(-value) using Python's standard math library."""
        import math
        return math.exp(-value)

    def generate_for_network(self, network, time_step=1.0):
        """Generate arrivals for every user in a network."""
        return {
            user.user_id: self.generate_arrivals(user, time_step)
            for user in network.users
        }
