import attr

from .create_percolation_map import to_idx


@attr.s
class PartOfInfinitePlane:
    def add_edges(self, w, h, g):
        pass


@attr.s
class Sphere:
    def add_edges(self, w, h, g):
        for y in range(h):
            g.add_edge(to_idx(w, 0, y), to_idx(w, w - 1, y))
        for x in range(w // 2):
            for y in (0, h - 1):
                g.add_edge(to_idx(w, x, y), to_idx(w, w - 1 - x, y))


@attr.s
class Torus:
    def add_edges(self, w, h, g):
        for x in range(w):
            g.add_edge(to_idx(w, x, 0), to_idx(w, x, h - 1))
        for y in range(h):
            g.add_edge(to_idx(w, 0, y), to_idx(w, w - 1, y))