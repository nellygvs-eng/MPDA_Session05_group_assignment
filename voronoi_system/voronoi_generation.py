from Rhino.Geometry import Interval, Rectangle3d, Plane, Voronoi, Brep, AreaMassProperties


def generate_voronoi_cells(points, width, depth):
    domain_x = Interval(0.0, float(width))
    domain_y = Interval(0.0, float(depth))
    bounding_rect = Rectangle3d(Plane.WorldXY, domain_x, domain_y)
    voronoi = Voronoi.CreateVoronoiDiagram(points, bounding_rect)
    curves = []
    if voronoi:
        for cell in voronoi.Cells:
            boundary = cell.Boundary
            if boundary and boundary.IsClosed:
                curves.append(boundary)
    return curves


def compute_cell_centroids(cell_curves):
    centroids = []
    for curve in cell_curves:
        breps = Brep.CreatePlanarBreps(curve)
        if breps:
            amp = AreaMassProperties.Compute(breps[0])
            if amp:
                centroids.append(amp.Centroid)
    return centroids
