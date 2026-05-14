# TECHNICAL DOCUMENTATION - VORONOI SCRIPT IMPLEMENTATION

## Architecture Overview

```
INPUT LAYER (Grasshopper sliders/curves)
           ↓
┌──────────────────────────────────────┐
│  PHASE 1: Setup & Core Geometry      │  Functions: create_rectangle_surface(),
│  - Rectangle surface                 │             generate_random_points_on_surface(),
│  - Random points on surface          │             create_voronoi_diagram()
│  - Voronoi cells (clipped)           │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│  PHASE 2: Path Processing            │  Functions: offset_curve_both_sides(),
│  - Offset input curve                │             create_loft_surface(),
│  - Loft offset curves (path surface) │             get_rectangle_boundary()
│  - Distance reference created        │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│  PHASE 3: Distance-Based Offset      │  Functions: get_cell_centroid(),
│  - Distance calculation              │             distance_point_to_curve(),
│  - Normalize distances (0-1)         │             normalize_distances(),
│  - Offset cells adaptively           │             offset_voronoi_cells_adaptive(),
│  - Create planar surfaces            │             create_planar_surfaces_from_curves()
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│  PHASE 4: Extrusion & Height Mapping │  Functions: calculate_extrusion_heights(),
│  - Calculate heights per cell        │             extrude_surfaces_adaptive()
│  - Extrude surfaces in Z direction   │
│  - Create moved (3D) surfaces        │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│  PHASE 5: Conditional Lofting        │  Functions: loft_original_to_moved_surfaces()
│  - If Loft Toggle ON:                │
│    Loft original ↔ moved surfaces    │
│  - If Loft Toggle OFF:               │
│    Use moved surfaces only           │
└──────────────────────────────────────┘
           ↓
OUTPUT LAYER (Grasshopper outputs)
```

---

## Function Reference

### PHASE 1: Setup & Core Geometry

#### `create_rectangle_surface(length, width, base_plane=None)`
**Purpose**: Create a rectangle NURBS surface with specified dimensions

**Parameters:**
- `length` (float): Rectangle length along X-axis
- `width` (float): Rectangle width along Y-axis
- `base_plane` (Plane): Optional; default is XY plane at origin

**Returns:**
- `NurbsSurface`: Rectangle surface on success
- `None`: If dimensions invalid or creation failed

**Algorithm:**
1. Validate length, width > 0
2. Define 4 corner points using plane axes
3. Use `NurbsSurface.CreateFromCorners()` to generate surface
4. Handle exceptions gracefully

**Example Usage:**
```python
rect = create_rectangle_surface(50.0, 40.0)
```

---

#### `generate_random_points_on_surface(surface, num_points, seed=None)`
**Purpose**: Generate N uniformly random points on a surface using UV parameterization

**Parameters:**
- `surface` (Surface): Rhino surface to sample
- `num_points` (int): Number of points to generate
- `seed` (int, optional): Random seed for reproducibility

**Returns:**
- `list`: List of Point3d objects on the surface
- `[]`: Empty list if invalid inputs

**Algorithm:**
1. Extract U and V domains from surface
2. For each of N iterations:
   - Generate random U in [u_min, u_max]
   - Generate random V in [v_min, v_max]
   - Evaluate surface.PointAt(U, V)
   - Add resulting 3D point to list
3. Return list of points

**Key Notes:**
- Uses uniform random distribution in parameter space
- Points are guaranteed to lie ON the surface (exact)
- Works for any surface (planar, curved, NURBS, etc.)

**Example Usage:**
```python
points = generate_random_points_on_surface(rect_surface, 20, seed=42)
```

---

#### `create_voronoi_diagram(points, boundary_curve)`
**Purpose**: Generate Voronoi cells from seed points, clipped to boundary

**Parameters:**
- `points` (list): Seed points (Point3d)
- `boundary_curve` (Curve): Closed boundary curve

**Returns:**
- `list`: Closed Curve objects representing Voronoi cells
- `[]`: Empty list if creation failed

**Implementation:**
- Uses native Rhino `rs.Voronoi()` function
- Returns cells automatically clipped to boundary
- Each cell is a closed curve suitable for offset/extrude operations

**Algorithm Flow:**
1. Call rs.Voronoi(points, boundary_curve)
2. Rhino computes Voronoi diagram internally
3. Cells are clipped to intersection with boundary_curve
4. Return list of closed curves

**Example Usage:**
```python
voronoi_cells = create_voronoi_diagram(seed_points, rectangle_boundary)
```

---

### PHASE 2: Path Processing

#### `offset_curve_both_sides(curve, distance, plane=None)`
**Purpose**: Create two offset curves from a base curve (positive and negative)

**Parameters:**
- `curve` (Curve): Base curve to offset
- `distance` (float): Offset distance magnitude
- `plane` (Plane, optional): 2D offset plane (default: XY)

**Returns:**
- `tuple`: (offset_pos, offset_neg) - Two Curve objects
- `(None, None)`: If offset failed

**Algorithm:**
1. Perform positive offset: `curve.Offset(plane, +distance, ...)`
2. Perform negative offset: `curve.Offset(plane, -distance, ...)`
3. Return both offset curves
4. Handle exceptions if offset fails

**Corner Style Options:**
- `Sharp` (default): Sharp corners at offset intersections
- `Round`: Smooth rounded corners
- `Bevel`: Beveled corners

**Example Usage:**
```python
offset_pos, offset_neg = offset_curve_both_sides(input_curve, 5.0)
```

---

#### `create_loft_surface(curves_list)`
**Purpose**: Create a surface by lofting through a list of curves

**Parameters:**
- `curves_list` (list): Ordered list of Curve objects (min 2 required)

**Returns:**
- `Brep`: Lofted surface on success
- `None`: If loft failed

**Algorithm:**
1. Validate input: at least 2 curves
2. Call `Brep.CreateFromLoft(curves_list, ...)`
3. Parameters:
   - `LoftType.Normal`: Natural curvature transitions
   - `closed=False`: Don't connect last curve to first
   - `angleTol=0.017453`: ~1 degree angular tolerance
4. Return first Brep result

**Use Cases:**
- Create path surface between offset curves: `loft([offset_pos, offset_neg])`
- Create transition surfaces between different curve profiles
- Smooth surface generation for architectural forms

**Example Usage:**
```python
path_surface = create_loft_surface([offset_pos, offset_neg])
```

---

#### `get_rectangle_boundary(rectangle_surface)`
**Purpose**: Extract the closed boundary curve from a rectangle surface

**Returns:**
- `Curve`: Polyline curve representing rectangle perimeter
- `None`: If extraction failed

**Algorithm:**
1. Get U and V domain boundaries
2. Evaluate 4 corner points:
   - (u_min, v_min), (u_max, v_min), (u_max, v_max), (u_min, v_max)
3. Connect corners with PolylineCurve
4. Close curve (append first point to end)

---

### PHASE 3: Distance-Based Offset

#### `get_cell_centroid(closed_curve)`
**Purpose**: Calculate centroid of a closed planar curve

**Returns:**
- `Point3d`: Centroid point
- `None`: If calculation failed

**Method:**
- Uses `AreaMassProperties.Compute()` to find center of mass
- Accurate for any closed curve (polygon, ellipse, complex shape)

---

#### `distance_point_to_curve(point, curve)`
**Purpose**: Calculate shortest distance from point to curve

**Algorithm:**
1. Find closest point on curve: `curve.ClosestPoint(t)`
2. Get 3D point at parameter t: `curve.PointAt(t)`
3. Calculate Euclidean distance: `point.DistanceTo(closest_pt)`
4. Return distance

**Returns:**
- `float`: Distance value ≥ 0
- `-1`: If calculation failed

---

#### `normalize_distances(distances)`
**Purpose**: Normalize distance values to [0, 1] range

**Algorithm:**
```
normalized_dist[i] = (dist[i] - min_dist) / (max_dist - min_dist)
```

**Special Cases:**
- All distances equal: return [0.5] × N (midpoint)
- Empty list: return []

**Returns:**
- `list`: Normalized distances in range [0, 1]

**Example:**
```
Input:  [2, 5, 10, 3]
Output: [0.0, 0.43, 1.0, 0.14]
```

---

#### `offset_voronoi_cells_adaptive(voronoi_cells, seed_points, path_curves, max_offset)`
**Purpose**: Apply distance-based offset to each Voronoi cell

**Key Logic:**
```
For each cell:
  centroid = get_cell_centroid(cell)
  distance = distance_point_to_curve(centroid, path_curve)
  normalized_dist = normalize(distance, all_distances)
  offset_amount = max_offset × normalized_dist
  offset_cell = cell.Offset(-offset_amount)  # Inward offset
```

**Distance Logic:**
- Cells **closer to path** (low distance) → **smaller offset**
- Cells **farther from path** (high distance) → **larger offset**
- Offset is applied **inward** (negative offset) for all cells

**Returns:**
- `list`: Offset curves (same length as input)

**Visual Effect:**
```
Original Voronoi:        After adaptive offset:
[||||||||||||||||]       [|  |    ||   | ||]
  close  far from path      smaller  larger offsets
```

---

#### `create_planar_surfaces_from_curves(curves)`
**Purpose**: Convert closed curves to planar Brep surfaces

**Algorithm:**
1. For each curve:
   - Check if closed
   - Call `Brep.CreatePlanarBreps(curve)`
   - Add result to surface list
2. Return all surfaces

**Returns:**
- `list`: Planar Brep surfaces

---

### PHASE 4: Extrusion & Height Mapping

#### `calculate_extrusion_heights(voronoi_cells, path_curves, max_height)`
**Purpose**: Calculate extrusion height for each cell based on path distance

**Key Logic (INVERSE of offset):**
```
For each cell:
  centroid = get_cell_centroid(cell)
  distance = distance_point_to_curve(centroid, path_curve)
  normalized_dist = normalize(distance, all_distances)
  height = max_height × (1 - normalized_dist)  # INVERSE!
```

**Distance Logic:**
- Cells **closer to path** (low distance) → **higher extrusion** (close to max_height)
- Cells **farther from path** (high distance) → **lower extrusion** (close to 0)

**Returns:**
- `list`: Height values for each cell

**Visual Effect:**
```
From above:              Side view:
[Close]  [Far]          High │  Low
  ↓       ↓              │  /╲   ╱╲
  ▓▓▓     ▓▓▓            │ ╱  ╲ ╱  ╲
                         └─────────────
```

---

#### `extrude_surfaces_adaptive(surfaces, voronoi_cells, rectangle_surface, heights)`
**Purpose**: Move surfaces upward by calculated heights

**Algorithm:**
1. For each surface and corresponding height:
   - Create extrusion vector: (0, 0, height)
   - Create translation transform: `Transform.Translation(vector)`
   - Duplicate surface: `surface.Duplicate()`
   - Apply transform: `extruded.Transform(transform)`
   - Add to result list
2. Return extruded surfaces

**Key Notes:**
- Extrusion is always in +Z direction (perpendicular to XY plane)
- Heights can be 0 (no extrusion) for cells far from path
- Each surface is moved independently

**Returns:**
- `list`: Moved (extruded) surfaces

---

### PHASE 5: Conditional Lofting

#### `loft_original_to_moved_surfaces(original_curves, moved_surfaces)`
**Purpose**: Create lofted surfaces connecting original cells to moved cells

**Algorithm:**
1. For each original curve and moved surface pair:
   - Extract boundary edges from moved surface
   - Get top curve from moved surface edges
   - Loft between original curve and top curve
   - Add lofted surface to results
2. Return all lofted surfaces

**Visual Effect:**
```
Side view (Cross-section):

Moved surface top:   ┌─────────┐
                    │         │  ← Lofted walls
Original cell:      └─────────┘
  (on ground)
```

**Returns:**
- `list`: Lofted Brep surfaces

---

## Algorithm Complexity

| Operation | Time Complexity | Space Complexity | Notes |
|-----------|-----------------|------------------|-------|
| Rectangle surface creation | O(1) | O(1) | Constant 4-point operation |
| Point generation | O(n) | O(n) | n = num_points |
| Voronoi computation | O(n log n) | O(n) | Rhino native, uses spatial index |
| Distance calculation | O(n × m) | O(1) | n = cells, m = curve complexity |
| Normalization | O(n) | O(n) | Single pass + allocation |
| Offset operations | O(n × m) | O(n) | Curve offset is expensive |
| Surface extrusion | O(n) | O(n) | Geometric transform per surface |
| Lofting | O(n × k) | O(n) | k = curve discretization factor |

**Overall**: O(n log n + n² m) where n = point count, m = avg curve complexity

---

## Key Design Decisions

### 1. Distance-Based Logic (Offset vs. Extrusion)

**Offset**: closer to path → SMALLER offset
**Extrusion**: closer to path → TALLER extrusion (INVERSE relationship)

**Rationale:**
- Creates visual balance: cells near path are constrained (small offset) but rise high (tall extrusion)
- Cells far from path spread out (large offset) but stay low (short extrusion)
- Mimics natural patterns (trees growing taller near water, spreading in open areas)

### 2. Inward Offset (Negative Offset Applied)

All Voronoi cell offsets are **inward** (shrinking cells), never outward.

**Rationale:**
- Prevents adjacent cells from disconnecting
- Maintains topology and adjacency relationships
- Creates nested, self-similar patterns

### 3. Z-Direction Extrusion (Not Surface Normal)

Extrusion is always in +Z direction, not along surface normal.

**Rationale:**
- Simpler implementation and faster computation
- More predictable results for planar input surfaces
- Aligns with typical architectural workflows (building height along Z)
- Can be modified to use surface normal if needed

### 4. Lofting Between Original and Moved

When loft toggle is ON, lofts connect ground-level cells to elevated cells.

**Rationale:**
- Creates dramatic vertical surfaces (walls/shells)
- Visualizes the transformation from original to extruded state
- Suitable for architectural form generation

### 5. Native rs.Voronoi() Over scipy.spatial.Voronoi

**Why not scipy:**
- Rhino doesn't include scipy by default in Grasshopper
- rs.Voronoi() returns clipped, usable curves immediately
- No need for custom clipping/polygon conversion logic

---

## Error Handling Strategy

The script uses **graceful degradation**:
- If rectangle creation fails → script stops (critical)
- If Voronoi fails → continue with empty cell list
- If path surface creation fails → use original curve as reference
- If offset fails on a cell → use original cell
- If extrusion fails → use unextruded surface

**Logging:**
- All errors printed to Grasshopper console
- Warnings help user identify input issues
- Progress messages indicate stage completion

---

## Performance Optimization Tips

1. **Reduce Num Points**: Start with 10-20 points for interactive testing
2. **Simplify Input Curve**: Use simple curves (lines, arcs); complex curves slow offset
3. **Disable Lofting**: Turn Loft Toggle OFF if only interested in extruded cells
4. **Use Reasonable Offsets**: Very large offset_distance values cause expensive curve operations
5. **Rectangle Size**: Larger rectangles may slow point generation slightly

---

## Extension Possibilities

### Future Enhancements:
1. **3D Voronoi**: Extend to 3D by using scipy.spatial.Voronoi
2. **Multiple Paths**: Support multiple curves as reference paths
3. **Normal-Direction Extrusion**: Extrude along surface normal instead of Z
4. **Material Mapping**: Output cell properties (area, perimeter) for analysis
5. **Mesh Export**: Convert output to mesh for faster visualization
6. **Animation**: Animate slider values over time
7. **Custom Offset Functions**: Non-linear offset based on cell properties
8. **Boundary Trimming**: Advanced clipping of cells at domain edges

---

## References

### Algorithms
- Voronoi Diagrams: https://en.wikipedia.org/wiki/Voronoi_diagram
- Curve Offsetting: https://www.w3schools.com/geometry/offsetting.html
- Lofting in CAD: https://en.wikipedia.org/wiki/Lofting_(CAD)

### Rhino/Grasshopper Documentation
- RhinoCommon API: https://developer.rhino3d.com/api/RhinoCommon/
- Grasshopper Python: https://www.grasshopper3d.com/

---

**Document Version**: 1.0  
**Last Updated**: May 2026  
**Authors**: Dibbendu P., Nelly V., David G.

