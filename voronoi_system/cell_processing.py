from Rhino.Geometry import Transform, Plane, Vector3d, CurveOffsetCornerStyle, Brep


def scale_curve_around_centroid(curve, centroid, scale_factor):
    scaled = curve.DuplicateCurve()
    scale_plane = Plane(centroid, Vector3d.ZAxis)
    xform = Transform.Scale(scale_plane, float(scale_factor), float(scale_factor), float(scale_factor))
    scaled.Transform(xform)
    return scaled


def offset_curve(curve, offset_distance):
    if curve is None:
        return None
    offset_results = curve.Offset(Plane.WorldXY, float(offset_distance), 0.01, CurveOffsetCornerStyle.Sharp)
    if offset_results and len(offset_results) > 0:
        return offset_results[0]
    return None


def create_planar_surfaces(offset_curves):
    surfaces = []
    for curve in offset_curves:
        if curve is None:
            continue
        breps = Brep.CreatePlanarBreps(curve)
        if breps:
            surfaces.extend(breps)
    return surfaces


def create_vertical_vectors(height_values):
    return [Vector3d(0.0, 0.0, float(h)) for h in height_values]


def extrude_surfaces(planar_surfaces, vertical_vectors):
    extrusions = []
    for brep, vector in zip(planar_surfaces, vertical_vectors):
        if brep and brep.Faces.Count > 0:
            extrusion = brep.Faces[0].CreateExtrusion(vector)
            if extrusion:
                extrusions.append(extrusion)
    return extrusions
