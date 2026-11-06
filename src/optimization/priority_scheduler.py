def allocate_priority_resources(users, total_resources):
    """
    Allocate resources using priority-based scheduling.

    Higher-priority users are served first.
    Users with the same priority share resources
    proportionally to their required bandwidth.

    Args:
        users: List of network User objects.
        total_resources: Total available network resources.

    Returns:
        List of allocations in the original user order.
    """

    if total_resources <= 0:
        raise ValueError("Total resources must be positive.")

    allocations = [0.0] * len(users)

    if not users:
        return allocations

    if any(user.required_bandwidth < 0 for user in users):
        raise ValueError("Required bandwidth cannot be negative.")

    remaining = float(total_resources)

    priority_levels = sorted(
        {user.priority for user in users},
        reverse=True
    )

    for priority in priority_levels:

        if remaining <= 1e-12:
            break

        priority_users = [
            (index, user)
            for index, user in enumerate(users)
            if user.priority == priority
        ]

        total_demand = sum(
            user.required_bandwidth
            for _, user in priority_users
        )

        if total_demand <= 0:
            continue

        if total_demand <= remaining:

            for index, user in priority_users:
                allocations[index] = user.required_bandwidth

            remaining -= total_demand

        else:

            sharing_ratio = remaining / total_demand

            for index, user in priority_users:
                allocations[index] = (
                    user.required_bandwidth * sharing_ratio
                )

            remaining = 0.0

    return allocations