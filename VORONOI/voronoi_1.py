"""
GRASSHOPPER VORONOI PARAMETRIC DESIGN SCRIPT
=============================================
Advanced Python Programming - MPDA Session 05 Group Assignment
Authors: Dibbendu P., Nelly V., David G.

This script generates an adaptive Voronoi pattern on a rectangle surface with:
- Distance-based offset (smaller offset for points closer to input curve path)
- Distance-based extrusion (higher extrusion for points closer to path)
- Conditional lofting between original and moved surfaces
- All geometry using native Rhino geometry (rg) and rhinoscriptsyntax (rs)

GRASSHOPPER INPUTS (6 required + 3 optional):
1. length (Float) - Rectangle length along X-axis
2. width (Float) - Rectangle width along Y-axis
3. num_points (Integer) - Number of Voronoi points to generate
4. input_curve (Curve) - Reference curve for path
5. offset_distance (Float) - Distance to offset the input curve on both sides
6. move_distance (Float) - Maximum height to extrude Voronoi cells
7. loft_toggle (Boolean) - If True, loft between original and moved surfaces
8. rectangle_plane (Plane) - Optional: plane to define rectangle orientation (default: XY plane)

GRASSHOPPER OUTPUTS:
1. rect_surface - The base rectangle surface
2. seed_points - The N random points used for Voronoi generation
3. output_curves - Voronoi cells (original or offset, configurable)
4. output_geometry - Moved polygon surfaces or lofted geometry based on toggle
"""

import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
from Rhino.Geometry import Point3d, Vector3d, Plane, NurbsSurface, Brep
import random
import math

# ============================================================================
# PHASE 1: SETUP & CORE GEOMETRY
# ============================================================================

def create_rectangle_surface(length, width, base_plane=None):
    """
    Create a rectangle surface with given dimensions.
    
    Args:
        length (float): Length of rectangle (X direction)
        width (float): Width of rectangle (Y direction)
        base_plane (Plane): Base plane for rectangle (default: XY plane at origin)
        
    Returns:
        NurbsSurface: Rectangle surface; None if invalid
    """
    if length <= 0 or width <= 0:
        return None
    
    if base_plane is None:
        base_plane = Plane.WorldXY
    
    try:
        # Define four corners in local plane coordinates
        origin = base_plane.Origin
        x_axis = base_plane.XAxis
        y_axis = base_plane.YAxis
        
        corners = [
            Point3d(origin.X,                    origin.Y,                    origin.Z),
            Point3d(origin.X + length * x_axis.X, origin.Y + length * x_axis.Y, origin.Z + length * x_axis.Z),
            Point3d(origin.X + length * x_axis.X + width * y_axis.X,
                   origin.Y + length * x_axis.Y + width * y_axis.Y,
                   origin.Z + length * x_axis.Z + width * y_axis.Z),
            Point3d(origin.X + width * y_axis.X, origin.Y + width * y_axis.Y, origin.Z + width * y_axis.Z),
        ]
        
        # Create NURBS surface from corners
        rect_surface = NurbsSurface.CreateFromCorners(corners[0], corners[1], corners[2], corners[3])
        return rect_surface
    
    except Exception as e:
        print("Error creating rectangle surface: {}".format(str(e)))
        return None


def generate_random_points_on_surface(surface, num_points, seed=None):
    """
    Generate random points on a Rhino surface using UV parameterization.
    
    Args:
        surface (Surface): Rhino surface to sample
        num_points (int): Number of points to generate
        seed (int): Random seed for reproducibility (optional)
        
    Returns:
        list: List of Point3d objects on the surface; empty list if invalid
    """
    if surface is None or num_points <= 0:
        return []
    
    if seed is not None:
        random.seed(seed)
    
    try:
        u_domain = surface.Domain(0)
        v_domain = surface.Domain(1)
        
        u_min, u_max = u_domain.Min, u_domain.Max
        v_min, v_max = v_domain.Min, v_domain.Max
        
        points = []
        for _ in range(num_points):
            u = u_min + random.random() * (u_max - u_min)
            v = v_min + random.random() * (v_max - v_min)
            pt = surface.PointAt(u, v)
            points.append(pt)
        
        return points
    
    except Exception as e:
        print("Error generating points on surface: {}".format(str(e)))
        return []


def create_voronoi_diagram(points, boundary_curve):
    """
    Create Voronoi diagram using Rhino's native Voronoi function.
    
    Args:
        points (list): List of Point3d or Point2d objects (seed points)
        boundary_curve (Curve): Boundary curve to clip Voronoi cells
        
    Returns:
        list: List of closed Curve objects representing Voronoi cells
    """
    if not points or boundary_curve is None:
        return []
    
    try:
        # rs.Voronoi requires a list of points and returns closed curves clipped to boundary
        voronoi_cells = rs.Voronoi(points, boundary_curve)
        
        if voronoi_cells is None:
            return []
        
        return voronoi_cells
    
    except Exception as e:
        print("Error computing Voronoi diagram: {}".format(str(e)))
        return []


# ============================================================================
# PHASE 2: PATH PROCESSING
# ============================================================================

def get_rectangle_boundary(rectangle_surface):
    """
    Extract boundary curve from rectangle surface.
    
    Args:
        rectangle_surface (Surface): Rectangle surface
        
    Returns:
        Curve: Boundary curve of the rectangle; None if invalid
    """
    if rectangle_surface is None:
        return None
    
    try:
        # Get the rectangle boundary as a polyline
        u_domain = rectangle_surface.Domain(0)
        v_domain = rectangle_surface.Domain(1)
        
        u_min, u_max = u_domain.Min, u_domain.Max
        v_min, v_max = v_domain.Min, v_domain.Max
        
        # Define four corners of rectangle parameter space
        corners = [
            rectangle_surface.PointAt(u_min, v_min),
            rectangle_surface.PointAt(u_max, v_min),
            rectangle_surface.PointAt(u_max, v_max),
            rectangle_surface.PointAt(u_min, v_max),
        ]
        
        # Create closed polyline
        corners.append(corners[0])  # Close the curve
        boundary = rg.PolylineCurve(corners)
        
        return boundary
    
    except Exception as e:
        print("Error extracting rectangle boundary: {}".format(str(e)))
        return None


def offset_curve_both_sides(curve, distance, plane=None):
    """
    Create two offset curves from a base curve (positive and negative offsets).
    
    Args:
        curve (Curve): Base curve to offset
        distance (float): Offset distance
        plane (Plane): Plane for 2D offset (default: XY plane)
        
    Returns:
        tuple: (offset_pos, offset_neg) - Two offset curve objects; (None, None) if failed
    """
    if curve is None or distance <= 0:
        return (None, None)
    
    if plane is None:
        plane = Plane.WorldXY
    
    try:
        # Create positive offset
        offset_pos_result = curve.Offset(plane, distance, 0.01, rg.CurveOffsetCornerStyle.Sharp)
        offset_pos = offset_pos_result[0] if offset_pos_result else None
        
        # Create negative offset
        offset_neg_result = curve.Offset(plane, -distance, 0.01, rg.CurveOffsetCornerStyle.Sharp)
        offset_neg = offset_neg_result[0] if offset_neg_result else None
        
        return (offset_pos, offset_neg)
    
    except Exception as e:
        print("Error offsetting curve: {}".format(str(e)))
        return (None, None)


def create_loft_surface(curves_list):
    """
    Create a lofted surface through a list of curves.
    
    Args:
        curves_list (list): List of Curve objects (must be ordered)
        
    Returns:
        Brep: Lofted surface; None if failed
    """
    if not curves_list or len(curves_list) < 2:
        return None
    
    try:
        breps = Brep.CreateFromLoft(
            curves_list,
            Point3d.Unset,
            Point3d.Unset,
            rg.LoftType.Normal,
            closed=False,
            angleTol=0.017453  # ~1 degree in radians
        )
        
        return breps[0] if breps else None
    
    except Exception as e:
        print("Error creating loft surface: {}".format(str(e)))
        return None


# ============================================================================
# PHASE 3: DISTANCE MAPPING & OFFSET
# ============================================================================

def get_cell_centroid(closed_curve):
    """
    Calculate the centroid of a closed planar curve.
    
    Args:
        closed_curve (Curve): Closed planar curve
        
    Returns:
        Point3d: Centroid point; None if calculation failed
    """
    if closed_curve is None or not closed_curve.IsClosed:
        return None
    
    try:
        # Use AreaMassProperties to get centroid
        area_props = rg.AreaMassProperties.Compute(closed_curve)
        if area_props:
            return area_props.Centroid
        return None
    
    except Exception as e:
        print("Error calculating cell centroid: {}".format(str(e)))
        return None


def distance_point_to_curve(point, curve):
    """
    Calculate the shortest distance from a point to a curve.
    
    Args:
        point (Point3d): Query point
        curve (Curve): Target curve
        
    Returns:
        float: Distance; -1 if calculation failed
    """
    if point is None or curve is None:
        return -1
    
    try:
        curve_parameter = curve.ClosestPoint(point)
        closest_pt = curve.PointAt(curve_parameter)
        distance = point.DistanceTo(closest_pt)
        return distance
    
    except Exception as e:
        print("Error calculating distance to curve: {}".format(str(e)))
        return -1


def normalize_distances(distances):
    """
    Normalize a list of distances to [0, 1] range.
    
    Args:
        distances (list): List of float distances
        
    Returns:
        list: Normalized distances in [0, 1]; all zeros if invalid input
    """
    if not distances:
        return []
    
    min_dist = min(distances)
    max_dist = max(distances)
    
    if max_dist - min_dist < 0.0001:  # All distances nearly equal
        return [0.5] * len(distances)
    
    normalized = []
    for d in distances:
        norm_d = (d - min_dist) / (max_dist - min_dist)
        normalized.append(max(0.0, min(1.0, norm_d)))
    
    return normalized


def offset_voronoi_cells_adaptive(voronoi_cells, seed_points, path_curves, max_offset):
    """
    Offset each Voronoi cell based on its distance to the path curves.
    Cells closer to path get smaller offsets; cells farther get larger offsets.
    
    Args:
        voronoi_cells (list): List of closed Curve objects
        seed_points (list): Original seed points for reference
        path_curves (list): List of path curves to measure distance to
        max_offset (float): Maximum offset distance
        
    Returns:
        list: List of offset Curve objects; empty if failed
    """
    if not voronoi_cells or not path_curves:
        return []
    
    # Combine all path curves into a single "path" for distance measurement
    # For simplicity, measure to the first path curve (can be enhanced)
    path_curve = path_curves[0]
    
    try:
        # Calculate distances from cell centroids to path curve
        distances = []
        centroids = []
        
        for cell in voronoi_cells:
            centroid = get_cell_centroid(cell)
            if centroid is None:
                distances.append(0)
                centroids.append(None)
            else:
                dist = distance_point_to_curve(centroid, path_curve)
                distances.append(dist if dist >= 0 else 0)
                centroids.append(centroid)
        
        # Normalize distances
        normalized_distances = normalize_distances(distances)
        
        # Offset each cell based on normalized distance
        offset_cells = []
        plane = Plane.WorldXY
        
        for i, cell in enumerate(voronoi_cells):
            if cell is None:
                continue
            
            # Calculate offset for this cell
            # Cells closer to path (normalized_dist → 0) get LARGER offset
            # Cells farther from path (normalized_dist → 1) get SMALLER offset
            offset_amount = max_offset * normalized_distances[i]
            
            if offset_amount < 0.001:  # Skip very small offsets
                offset_cells.append(cell)
                continue
            
            # Offset the cell curve inward (negative offset)
            try:
                offset_result = cell.Offset(plane, -offset_amount, 0.01, rg.CurveOffsetCornerStyle.Sharp)
                offset_curve = offset_result[0] if offset_result else cell
                offset_cells.append(offset_curve)
            except:
                offset_cells.append(cell)
        
        return offset_cells
    
    except Exception as e:
        print("Error offsetting Voronoi cells: {}".format(str(e)))
        return []


def create_planar_surfaces_from_curves(curves):
    """
    Convert closed curves to planar Brep surfaces.
    
    Args:
        curves (list): List of closed Curve objects
        
    Returns:
        list: List of planar Brep surfaces; empty if failed
    """
    surfaces = []
    
    for curve in curves:
        if curve is None or not curve.IsClosed:
            continue
        
        try:
            breps = Brep.CreatePlanarBreps(curve)
            if breps:
                surfaces.extend(breps)
        except Exception as e:
            print("Error creating planar surface: {}".format(str(e)))
            continue
    
    return surfaces


# ============================================================================
# PHASE 4: HEIGHT MAPPING & EXTRUSION
# ============================================================================

def calculate_extrusion_heights(voronoi_cells, path_curves, max_height):
    """
    Calculate extrusion height for each Voronoi cell based on distance to path.
    Cells closer to path get HIGHER extrusion; cells farther get LOWER extrusion.
    (Inverse of offset logic)
    
    Args:
        voronoi_cells (list): List of closed Curve objects
        path_curves (list): List of path curves to measure distance to
        max_height (float): Maximum extrusion height
        
    Returns:
        list: List of extrusion heights; empty if failed
    """
    if not voronoi_cells or not path_curves:
        return []
    
    path_curve = path_curves[0]
    
    try:
        distances = []
        
        for cell in voronoi_cells:
            centroid = get_cell_centroid(cell)
            if centroid is None:
                distances.append(0)
            else:
                dist = distance_point_to_curve(centroid, path_curve)
                distances.append(dist if dist >= 0 else 0)
        
        # Normalize distances
        normalized_distances = normalize_distances(distances)
        
        # Calculate heights: cells closer to path (low normalized_dist) get HIGH height
        heights = []
        for norm_dist in normalized_distances:
            height = max_height * (1.0 - norm_dist)  # Inverse relationship
            heights.append(height)
        
        return heights
    
    except Exception as e:
        print("Error calculating extrusion heights: {}".format(str(e)))
        return []


def get_surface_normal(surface, u_param, v_param):
    """
    Get the surface normal at a given UV parameter.
    
    Args:
        surface (Surface): Rhino surface
        u_param (float): U parameter
        v_param (float): V parameter
        
    Returns:
        Vector3d: Normal vector; None if failed
    """
    if surface is None:
        return None
    
    try:
        normal = surface.NormalAt(u_param, v_param)
        if normal.Length > 0:
            normal.Unitize()
        return normal
    
    except Exception as e:
        print("Error calculating surface normal: {}".format(str(e)))
        return Vector3d(0, 0, 1)  # Default to Z-up


def extrude_surfaces_adaptive(surfaces, voronoi_cells, rectangle_surface, heights):
    """
    Extrude surfaces along the surface normal by calculated heights.
    
    Args:
        surfaces (list): List of Brep surfaces to extrude
        voronoi_cells (list): Original Voronoi cell curves
        rectangle_surface (Surface): Base rectangle surface for normal calculation
        heights (list): List of extrusion heights (must match number of surfaces)
        
    Returns:
        list: List of extruded (moved) Brep surfaces; empty if failed
    """
    if not surfaces or not heights or len(surfaces) != len(heights):
        return []
    
    try:
        extruded_surfaces = []
        
        for i, surface in enumerate(surfaces):
            if surface is None or i >= len(heights):
                continue
            
            height = heights[i]
            
            if height < 0.001:  # Very small height, skip extrusion
                extruded_surfaces.append(surface)
                continue
            
            try:
                # Get a point on the surface to calculate normal
                # For planar surfaces created from Voronoi cells (on XY plane), normal is Z
                normal = Vector3d(0, 0, 1)  # Default: vertical
                
                # Create extrusion
                extrusion_vector = normal * height
                transform = rg.Transform.Translation(extrusion_vector)
                
                # Transform the surface
                extruded = surface.Duplicate()
                extruded.Transform(transform)
                extruded_surfaces.append(extruded)
            
            except Exception as e:
                print("Error extruding surface {}: {}".format(i, str(e)))
                extruded_surfaces.append(surface)
        
        return extruded_surfaces
    
    except Exception as e:
        print("Error in extrude_surfaces_adaptive: {}".format(str(e)))
        return []


# ============================================================================
# PHASE 5: CONDITIONAL LOFTING & FINALIZATION
# ============================================================================

def loft_original_to_moved_surfaces(original_curves, moved_surfaces):
    """
    Loft between original Voronoi cells and moved surfaces to create vertical walls.
    
    Args:
        original_curves (list): List of original Voronoi cell curves (on base surface)
        moved_surfaces (list): List of moved (extruded) surfaces
        
    Returns:
        list: List of lofted Brep surfaces; empty if failed
    """
    if not original_curves or not moved_surfaces or len(original_curves) != len(moved_surfaces):
        return []
    
    try:
        lofted_surfaces = []
        
        for i in range(len(original_curves)):
            orig_curve = original_curves[i]
            moved_surface = moved_surfaces[i]
            
            if orig_curve is None or moved_surface is None:
                continue
            
            # Extract the boundary curve of the moved surface
            # (For simple lofting, we create vertical faces between base and top)
            try:
                # Get the perimeter of the moved surface
                moved_boundary_edges = moved_surface.Edges
                if moved_boundary_edges and len(moved_boundary_edges) > 0:
                    # Use the first edge as the top curve
                    top_curve = moved_boundary_edges[0]
                    
                    # Loft between original and top curve
                    loft_breps = Brep.CreateFromLoft([orig_curve, top_curve], Point3d.Unset, Point3d.Unset,
                                                      rg.LoftType.Normal, False, 0.017453)
                    
                    if loft_breps:
                        lofted_surfaces.extend(loft_breps)
            except:
                pass
        
        return lofted_surfaces
    
    except Exception as e:
        print("Error in lofting: {}".format(str(e)))
        return []


# ============================================================================
# MAIN EXECUTION - GRASSHOPPER COMPONENT
# ============================================================================

def main():
    """
    Main execution function - Grasshopper component logic.
    This function is called by the Grasshopper Python component.
    """
    
    # ========== PHASE 1: Setup & Core Geometry ==========
    
    # Create rectangle surface
    rect_surface = create_rectangle_surface(length, width)
    if rect_surface is None:
        print("ERROR: Failed to create rectangle surface")
        return
    
    # Get rectangle boundary for Voronoi clipping
    rect_boundary = get_rectangle_boundary(rect_surface)
    if rect_boundary is None:
        print("ERROR: Failed to extract rectangle boundary")
        return
    
    # Generate random points on surface
    seed_points = generate_random_points_on_surface(rect_surface, num_points)
    if not seed_points:
        print("WARNING: Failed to generate seed points")
        seed_points = []
    
    # Create Voronoi diagram
    voronoi_cells = create_voronoi_diagram(seed_points, rect_boundary)
    if not voronoi_cells:
        print("WARNING: Failed to create Voronoi diagram")
        voronoi_cells = []
    
    # ========== PHASE 2: Path Processing ==========
    
    # Handle input curves
    if input_curve is None:
        print("WARNING: No input curve provided; using rectangle boundary as path")
        path_base_curve = rect_boundary
    else:
        path_base_curve = input_curve
    
    # Offset the input curve on both sides
    offset_pos, offset_neg = offset_curve_both_sides(path_base_curve, offset_distance)
    
    # Create lofted path surface
    if offset_pos and offset_neg:
        path_surface = create_loft_surface([offset_pos, offset_neg])
        path_curves = [offset_pos, offset_neg, path_base_curve]
    else:
        print("WARNING: Could not create offset curves for path")
        path_surface = None
        path_curves = [path_base_curve] if path_base_curve else []
    
    # ========== PHASE 3: Distance-Based Offset ==========
    
    # Offset Voronoi cells adaptively based on distance to path
    offset_cells = offset_voronoi_cells_adaptive(voronoi_cells, seed_points, path_curves, offset_distance)
    
    # Create surfaces from offset cells
    offset_surfaces = create_planar_surfaces_from_curves(offset_cells)
    
    # ========== PHASE 4: Extrusion & Height Mapping ==========
    
    # Calculate extrusion heights for each cell
    extrusion_heights = calculate_extrusion_heights(voronoi_cells, path_curves, move_distance)
    
    # Extrude surfaces adaptively
    if offset_surfaces and extrusion_heights:
        moved_surfaces = extrude_surfaces_adaptive(offset_surfaces, voronoi_cells, rect_surface, extrusion_heights)
    else:
        print("WARNING: Could not extrude surfaces; using offset surfaces as-is")
        moved_surfaces = offset_surfaces
    
    # ========== PHASE 5: Conditional Lofting ==========
    
    # Determine output geometry based on loft toggle
    if loft_toggle and voronoi_cells and moved_surfaces:
        # Loft between original cells and moved surfaces
        lofted_output = loft_original_to_moved_surfaces(voronoi_cells, moved_surfaces)
        output_geometry = lofted_output if lofted_output else moved_surfaces
    else:
        output_geometry = moved_surfaces
    
    # ========== SET GRASSHOPPER OUTPUTS ==========
    
    ghenv.Component.Params.Output[0].SetData(0, rect_surface)  # Rectangle surface
    
    for i, pt in enumerate(seed_points):
        ghenv.Component.Params.Output[1].SetData(i, pt)  # Seed points
    
    for i, curve in enumerate(voronoi_cells):
        ghenv.Component.Params.Output[2].SetData(i, curve)  # Output curves (Voronoi cells)
    
    for i, geom in enumerate(output_geometry):
        ghenv.Component.Params.Output[3].SetData(i, geom)  # Output geometry
    
    print("Script execution completed successfully!")
    print("Generated {} Voronoi cells".format(len(voronoi_cells)))
    print("Created {} offset surfaces".format(len(offset_surfaces)))
    print("Extruded {} surfaces".format(len(moved_surfaces)))
    print("Output geometry count: {}".format(len(output_geometry)))


# ============================================================================
# GRASSHOPPER COMPONENT INPUTS
# ============================================================================

# These inputs come from Grasshopper component sliders/inputs
# NOTE: In actual Grasshopper, these are provided via gh.Input or component inputs
# For this template, we access them directly

try:
    # PHASE 1 inputs
    length = ghenv.Component.Params.Input[0].VolatileData.get_Branch(0)[0].Value  # Length slider
    width = ghenv.Component.Params.Input[1].VolatileData.get_Branch(0)[0].Value   # Width slider
    num_points = int(ghenv.Component.Params.Input[2].VolatileData.get_Branch(0)[0].Value)  # Num points
    
    # PHASE 2-4 inputs
    input_curve = ghenv.Component.Params.Input[3].VolatileData.get_Branch(0)[0].Value  # Input curve
    offset_distance = ghenv.Component.Params.Input[4].VolatileData.get_Branch(0)[0].Value  # Offset distance
    move_distance = ghenv.Component.Params.Input[5].VolatileData.get_Branch(0)[0].Value  # Move distance
    
    # PHASE 5 input
    loft_toggle = ghenv.Component.Params.Input[6].VolatileData.get_Branch(0)[0].Value  # Loft toggle
    
    # Execute main script
    main()

except Exception as e:
    print("ERROR: {}".format(str(e)))
    import traceback
    traceback.print_exc()
