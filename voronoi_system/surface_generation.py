import random
from Rhino.Geometry import PlaneSurface, Plane, Interval


def create_rectangle_surface(width, depth):
    width = float(width)
    depth = float(depth)
    return PlaneSurface(Plane.WorldXY, Interval(0.0, width), Interval(0.0, depth))


def populate_random_points(surface, point_count):
    u_domain = surface.Domain(0)
    v_domain = surface.Domain(1)
    count = max(1, int(point_count))
    points = []
    for _ in range(count):
        u = random.uniform(u_domain.Min, u_domain.Max)
        v = random.uniform(v_domain.Min, v_domain.Max)
        points.append(surface.PointAt(u, v))
    return points
