import tqdm.auto as tqdm

from .create_percolation_map import create_percolation_map
from .renderer import render_map
from .topology import PartOfInfinitePlane, Sphere


def example(seed, w, h, mcs, topology):
    components = create_percolation_map(
        w, h, seed=seed, min_component_size=mcs, topology=topology
    )
    return render_map(components, w=w, h=h, seed=seed)


def sphere_example(seed):
    return example(seed, w=2000, h=1000, mcs=3e-4, topology=Sphere())


def minecraft_example(seed):
    return example(seed, w=1500, h=1500, mcs=3e-4, topology=PartOfInfinitePlane())


examples_map = dict(sphere=sphere_example, minecraft=minecraft_example)


def main():
    for example_type in examples_map:
        print(example_type)
        for seed in tqdm.tqdm(range(100)):
            examples_map[example_type](seed).save(f"examples/{example_type}_{seed}.png")


if __name__ == "__main__":
    main()
