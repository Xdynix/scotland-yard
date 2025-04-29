import math
from collections import Counter
from random import Random


def allocate_by_dirichlet(
    random: Random,
    categories: int,
    total: int,
    concentration: float,
) -> list[int]:  # pragma: no cover
    """
    Distribute a total integer quantity across a fixed number of categories
    according to a Dirichlet distribution.

    Args:
        random: The random number generator to use.
        categories: Number of categories to allocate quantity to.
            Each category may receive zero.
        total: Total integer quantity to distribute among categories.
        concentration: Dirichlet concentration parameter (α).
            Values <1 produce more extreme (sparse) allocations;
            values >1 produce more uniform allocations.

    Returns:
        A list of integer allocations for each category that sums exactly to total.
    """  # noqa: RUF002
    # Sample Gamma variates for Dirichlet
    gamma_samples = [random.gammavariate(concentration, 1.0) for _ in range(categories)]
    total_gamma = sum(gamma_samples)
    raw_counts = [total * g / total_gamma for g in gamma_samples]

    # Floor allocations and distribute remainder randomly
    allocations = [math.floor(x) for x in raw_counts]
    remainder = total - sum(allocations)
    for _ in range(remainder):
        idx = random.randrange(categories)
        allocations[idx] += 1
    return allocations


def sample_poisson_value(random: Random, rate: float) -> int:  # pragma: no cover
    """
    Draw a non-negative integer from a Poisson distribution using Knuth's algorithm.

    Args:
        random: The random number generator to use.
        rate: The Poisson distribution's rate parameter (λ).
            Higher values increase the expected output count.

    Returns:
        A random integer k such that P(k) follows Poisson(rate).
    """
    exp_neg_rate = math.exp(-rate)
    count = 0
    product = 1.0
    while product > exp_neg_rate:
        count += 1
        product *= random.random()
    return count - 1


def sample_lambdas_by_node_count(
    random: Random,
    node_counts: list[int],
    min_rate: float = 0.1,
    rate_factor: float = 2,
    bias_exponent: float = 4,
) -> list[float]:  # pragma: no cover
    """
    Sample a rate (λ) for each tree based on its node count.

    Args:
        random: The random number generator to use.
        node_counts: List of node counts per tree. Zero-count trees get rate=0.
        min_rate: Global minimum rate for all trees.
        rate_factor: Multiplier for maximum rate relative to node count.
            max_rate = min_rate + rate_factor * nodes.
        bias_exponent: Exponent >1 biases samples toward min_rate.

    Returns:
        A list of sampled rate parameters per tree.
    """
    rates: list[float] = []
    for nodes in node_counts:
        if nodes <= 0:
            rates.append(0.0)
            continue
        max_rate = min_rate + rate_factor * nodes
        u = random.random()
        rate = min_rate + (max_rate - min_rate) * u**bias_exponent
        rates.append(rate)
    return rates


def generate_poisson_tree(
    random: Random,
    total_nodes: int,
    rate: float,
) -> dict[int, list[int]]:  # pragma: no cover
    """
    Build a random tree where each node's depth is sampled from a Poisson(rate).

    Args:
        random: The random number generator to use.
        total_nodes: Total number of nodes in the tree including the root.
            If zero or negative, returns an empty tree.
        rate: Poisson rate parameter controlling depth distribution.
            Larger values yield deeper, thinner trees on average.

    Returns:
        A mapping of parent node IDs to lists of their children IDs. The root has ID 0.
    """
    tree: dict[int, list[int]] = {}
    if total_nodes <= 0:
        return tree

    # Sample depth for each non-root node and count frequencies
    depth_counts = Counter(
        sample_poisson_value(random, rate) for _ in range(total_nodes - 1)
    )

    tree[0] = []
    previous_level_nodes = [0]
    next_node_id = 1

    # Attach nodes level by level according to sampled depths
    for _, count in sorted(depth_counts.items()):
        current_level_nodes: list[int] = []
        for _ in range(count):
            parent = random.choice(previous_level_nodes)
            tree[parent].append(next_node_id)
            tree[next_node_id] = []
            current_level_nodes.append(next_node_id)
            next_node_id += 1
        previous_level_nodes = current_level_nodes

    return tree
