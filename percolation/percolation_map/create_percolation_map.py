from permacache import permacache

import numpy as np
import networkx as nx


@permacache("percolation_map/create_percolation_map/create_percolation_map_2")
def create_percolation_map(w, h, *, seed, min_component_size, topology):
    g = create_graph(w, h, seed, topology=topology)
    components = create_components(g)
    components = merge_components(
        w, h, components, min_component_size=min_component_size
    )
    return sorted((sorted(comp) for comp in components), key=lambda x: (len(x), x))


def to_idx(w, x, y):
    return x + y * w


def create_graph(w, h, seed, *, p=0.5, topology):
    rng = np.random.RandomState(seed)
    hor = rng.choice(2, size=(w - 1, h), p=[p, 1 - p])
    ver = rng.choice(2, size=(w, h - 1), p=[p, 1 - p])
    g = nx.Graph()
    g.add_nodes_from(np.arange(w * h))
    for x, y in zip(*np.where(hor)):
        g.add_edge(to_idx(w, x, y), to_idx(w, x + 1, y))
    for x, y in zip(*np.where(ver)):
        g.add_edge(to_idx(w, x, y), to_idx(w, x, y + 1))

    topology.add_edges(w, h, g)
    return g


def create_components(g):
    components = list(nx.algorithms.connected_components(g))
    return components


def merge_components(w, h, components, min_component_size=0.001):
    size_limit = int(w * h * min_component_size)
    big_components = [comp for comp in components if len(comp) >= size_limit]
    small_components = [comp for comp in components if len(comp) < size_limit]
    for i in range(len(small_components)):
        comp = small_components[i]
        if comp is None:
            continue
        all_neigh = {x for i in comp for x in neighbors(w, h, i)}
        done = False
        for big in big_components:
            if all_neigh & big:
                big |= comp
                done = True
                break
        if done:
            continue
        for j in range(i + 1, len(small_components)):
            if small_components[j] is None:
                continue
            if all_neigh & small_components[j]:
                small_components[j] |= comp
                if len(small_components[j]) >= size_limit:
                    big_components.append(small_components[j])
                    small_components[j] = None
                done = True
                break
        assert done
    return big_components


def neighbors(w, h, idx):
    x, y = idx % w, idx // w
    result = set()
    if x > 0:
        result.add(to_idx(w, x - 1, y))
    if x < w - 1:
        result.add(to_idx(w, x + 1, y))
    if y > 0:
        result.add(to_idx(w, x, y - 1))
    if y < h - 1:
        result.add(to_idx(w, x, y + 1))
    return result
