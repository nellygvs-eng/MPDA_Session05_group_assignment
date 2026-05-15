# GRASSHOPPER VORONOI PARAMETRIC DESIGN - SETUP GUIDE

## Overview
This guide explains how to set up and use the Voronoi parametric design script (`voronoi_1.py`) in Rhinoceros Grasshopper with Python 3.

---

## Part 1: Grasshopper Component Configuration

### Step 1: Create a Grasshopper Python Component

1. Open Rhinoceros and launch Grasshopper (Grasshopper menu or `GH` command)
2. In the Grasshopper canvas, add a **Python Script** component:
   - Go to `Params > Input > Python Script` or
   - Search for "Python" in the component menu
3. Double-click the component to open the Python editor

### Step 2: Load the Script

1. In the Python editor, replace all content with the code from `voronoi_1.py`
2. Save the component (Ctrl+S or File > Save)

---

## Part 2: Configure Inputs & Outputs

### Input Configuration (7 total inputs)

Right-click on the Python component and select **"Manage Component Data..."** to add inputs. Alternatively, wire inputs directly from sliders and other components.

#### **INPUT 0: Length (Float)**
- **Type**: Number slider
- **Purpose**: Rectangle length (X-axis direction)
- **Recommended Range**: 10.0 to 100.0
- **Default**: 50.0

**Setup in Grasshopper:**
- Add a `Number Slider` component
- Set range: Min=1, Max=200, Value=50
- Wire output to Python component INPUT 0

#### **INPUT 1: Width (Float)**
- **Type**: Number slider
- **Purpose**: Rectangle width (Y-axis direction)
- **Recommended Range**: 10.0 to 100.0
- **Default**: 50.0

**Setup:**
- Add another `Number Slider` component
- Set range: Min=1, Max=200, Value=50
- Wire to INPUT 1

#### **INPUT 2: Num Points (Integer)**
- **Type**: Integer slider
- **Purpose**: Number of Voronoi seed points
- **Recommended Range**: 5 to 100
- **Default**: 20

**Setup:**
- Add an `Integer Slider` component
- Set range: Min=1, Max=500, Value=20
- Wire to INPUT 2

#### **INPUT 3: Input Curve (Curve)**
- **Type**: Curve object
- **Purpose**: Reference curve that defines the "path" for proximity-based offset/extrusion
- **Requirements**: 
  - Must be planar (on XY plane)
  - Should be within or near the rectangle bounds
  - Can be a single curve or multiple curves

**Setup:**
- Create a curve in Rhino (e.g., using `Curve` from Grasshopper's Curve menu)
- Or use a curve from Rhino's geometry
- Wire to INPUT 3
- **Fallback**: If no curve provided, the script uses the rectangle boundary

#### **INPUT 4: Offset Distance (Float)**
- **Type**: Number slider
- **Purpose**: Distance to offset the input curve on both sides
- **Recommended Range**: 0.5 to 20.0
- **Default**: 5.0
- **Logic**: Offsets are created +/- this distance from the input curve; a lofted surface is created between them (the "path" reference)

**Setup:**
- Add a `Number Slider` component
- Set range: Min=0.1, Max=50, Value=5
- Wire to INPUT 4

#### **INPUT 5: Move Distance (Float)**
- **Type**: Number slider
- **Purpose**: Maximum extrusion height for Voronoi cells
- **Recommended Range**: 1.0 to 50.0
- **Default**: 10.0
- **Logic**: Cells closest to the path get height ≈ Move Distance; cells farthest get height ≈ 0

**Setup:**
- Add a `Number Slider` component
- Set range: Min=0, Max=100, Value=10
- Wire to INPUT 5

#### **INPUT 6: Loft Toggle (Boolean)**
- **Type**: Toggle (True/False)
- **Purpose**: If ON, loft between original Voronoi cells and moved surfaces (creates vertical walls); if OFF, output only moved surfaces
- **Default**: False

**Setup:**
- Add a `Boolean Toggle` component (right-click to switch between True/False)
- Wire to INPUT 6

---

### Output Configuration (4 total outputs)

After wiring all inputs, the component automatically creates outputs. You can visualize them by wiring to **Preview** or **Data** components.

#### **OUTPUT 0: rect_surface**
- **Type**: Surface (Brep)
- **Description**: The base rectangle surface (defined by Length × Width sliders)
- **Usage**: Connect to a `Brep Display` or `Srf` component for visualization

#### **OUTPUT 1: seed_points**
- **Type**: Points (list)
- **Description**: The N random seed points used to generate the Voronoi diagram
- **Usage**: Connect to a `Point Display` component to visualize

#### **OUTPUT 2: output_curves**
- **Type**: Curves (list)
- **Description**: Output Voronoi cell curves (original cells, not offset)
- **Usage**: Connect to a `Curve` component for visualization

#### **OUTPUT 3: output_geometry**
- **Type**: Geometry (Brep/Surface list)
- **Description**: Final output geometry
  - If **Loft Toggle = OFF**: Extruded (moved) Voronoi cell surfaces
  - If **Loft Toggle = ON**: Lofted surfaces connecting original cells to moved cells (vertical walls)
- **Usage**: Connect to a `Brep Display` for final visualization

---

## Part 3: Step-by-Step Setup Instructions

### Complete Grasshopper File Structure

1. **Create Sliders:**
   ```
   [Length Slider: 10-100] → Python INPUT 0
   [Width Slider: 10-100] → Python INPUT 1
   [Num Points Slider: 1-100] → Python INPUT 2
   [Offset Distance Slider: 0.1-50] → Python INPUT 4
   [Move Distance Slider: 0-100] → Python INPUT 5
   ```

2. **Create Input Curve:**
   ```
   [Rhino Curve Object] → Python INPUT 3
   ```
   OR wire a curve from other Grasshopper components

3. **Create Toggle:**
   ```
   [Boolean Toggle] → Python INPUT 6
   ```

4. **Wire Outputs to Display Components:**
   ```
   Python OUTPUT 0 (rect_surface) → Brep Display (or "Preview")
   Python OUTPUT 1 (seed_points) → Point Display
   Python OUTPUT 2 (output_curves) → Curve Display
   Python OUTPUT 3 (output_geometry) → Brep Display
   ```

5. **Connect to Export (optional):**
   ```
   Python OUTPUT 3 → Export to Rhino or File
   ```

---

## Part 4: Understanding the Algorithm

### Workflow Summary

1. **PHASE 1 - Rectangle & Points:**
   - Creates a rectangle surface (Length × Width) on XY plane
   - Generates N random points on the surface using UV parameterization

2. **PHASE 2 - Voronoi & Path:**
   - Computes Voronoi diagram from seed points, clipped to rectangle boundary
   - Offsets input curve ±Offset Distance
   - Creates a lofted surface between offset curves (reference "path")

3. **PHASE 3 - Distance-Based Offset:**
   - For each Voronoi cell, calculates distance from its centroid to the path curve
   - Cells **closer to path** get **smaller offset** (closer to original shape)
   - Cells **farther from path** get **larger offset** (more distorted)
   - New offset cells are created by inward offsetting

4. **PHASE 4 - Distance-Based Extrusion:**
   - For each offset cell, calculates extrusion height based on distance to path (inverse logic)
   - Cells **closer to path** get **higher extrusion** (up to Move Distance)
   - Cells **farther from path** get **lower extrusion** (closer to 0)
   - Surfaces are moved upward in Z direction

5. **PHASE 5 - Conditional Lofting:**
   - If **Loft Toggle = ON**: Creates lofted surfaces between original cells and moved cells
   - If **Loft Toggle = OFF**: Outputs moved cells only

---

## Part 5: Example Configurations

### Example 1: Simple Voronoi Pattern
**Inputs:**
- Length: 50
- Width: 50
- Num Points: 15
- Input Curve: (a line across the middle of the rectangle)
- Offset Distance: 2
- Move Distance: 0 (no extrusion)
- Loft Toggle: OFF

**Expected Output:**
- Flat Voronoi cells with small offsets near the input curve; larger offsets farther away

---

### Example 2: Parametric Landscape
**Inputs:**
- Length: 80
- Width: 80
- Num Points: 40
- Input Curve: (a curved path through the rectangle)
- Offset Distance: 3
- Move Distance: 15
- Loft Toggle: OFF

**Expected Output:**
- 3D landscape where peaks are aligned with the path and valleys are far from the path

---

### Example 3: Lofted Architecture
**Inputs:**
- Length: 60
- Width: 60
- Num Points: 25
- Input Curve: (a serpentine curve)
- Offset Distance: 2.5
- Move Distance: 20
- Loft Toggle: ON

**Expected Output:**
- Complex lofted architecture with vertical walls between ground-level cells and elevated cells

---

## Part 6: Troubleshooting

### Issue: "ERROR: Failed to create rectangle surface"
**Cause**: Length or Width slider is 0 or negative
**Solution**: Set both sliders to positive values (e.g., Length=50, Width=50)

### Issue: "WARNING: Failed to create Voronoi diagram"
**Cause**: Seed points not generated or invalid rectangle boundary
**Solution**: 
- Ensure Num Points ≥ 1
- Check that Length/Width are positive
- Verify sliders are correctly wired

### Issue: "WARNING: No input curve provided; using rectangle boundary as path"
**Cause**: No curve wired to INPUT 3
**Solution**: 
- Wire an input curve to the Python component INPUT 3
- Or use a `Curve` component to create a test curve

### Issue: Output geometry is empty or missing
**Cause**: Script error or invalid inputs
**Solution**:
- Check the Grasshopper console for error messages (right-click component > "Errors" tab)
- Verify all 7 inputs are correctly wired
- Try with default values first

### Issue: Extrusion heights are all zero
**Cause**: Move Distance slider is 0
**Solution**: Increase the Move Distance slider to a positive value (e.g., 10)

### Issue: Loft Toggle doesn't work
**Cause**: Loft surfaces cannot be created (insufficient cells or invalid geometry)
**Solution**:
- Ensure Num Points ≥ 5 for reasonable Voronoi cells
- Check that moved surfaces were created successfully
- Try with simpler input curves first

---

## Part 7: Advanced Customization

### Modify Offset Logic (in Python code)
Find this line in the script:
```python
offset_amount = max_offset * normalized_distances[i]
```

**Current Logic**: `offset = normalized_distance × max_offset`
- Cells closer to path (low normalized_dist) → low offset
- Cells farther from path (high normalized_dist) → high offset

**To Reverse** (farther cells get smaller offset):
```python
offset_amount = max_offset * (1.0 - normalized_distances[i])
```

---

### Modify Extrusion Logic
Find this line:
```python
height = max_height * (1.0 - norm_dist)
```

**Current Logic**: `height = max_height × (1 - normalized_distance)`
- Cells closer to path (low normalized_dist) → high height
- Cells farther from path (high normalized_dist) → low height

**To Reverse** (farther cells get higher extrusion):
```python
height = max_height * norm_dist
```

---

### Use Different Offset Method
Replace the offset corner style:
```python
offset_result = cell.Offset(plane, -offset_amount, 0.01, rg.CurveOffsetCornerStyle.Round)
```

Options:
- `Sharp` (default) - Sharp corners at offset points
- `Round` - Rounded corners
- `Bevel` - Beveled corners

---

## Part 8: Expected Performance

| Num Points | Cells | Processing Time* |
|-----------|-------|------------------|
| 10        | ~8-12 | <0.5s            |
| 20        | ~15-25| ~1s              |
| 50        | ~40-60| ~3-5s            |
| 100       | ~80-120| ~10-15s         |

*Approximate times on standard PC; may vary based on curve complexity and offset operations

---

## Part 9: References & Additional Resources

### Rhino Python Documentation
- [RhinoCommon API Reference](https://developer.rhino3d.com/api/)
- [Grasshopper Python Guide](https://developer.rhino3d.com/guides/grasshopper/python-guides/)

### Voronoi Diagrams
- [Voronoi Diagram on Wikipedia](https://en.wikipedia.org/wiki/Voronoi_diagram)
- [Spatial Decomposition in Architecture](https://www.researchgate.net/topic/Voronoi-Diagrams)

---

## Summary

This script provides a powerful tool for parametric design based on Voronoi patterns. The key features are:

✅ **Flexible rectangle dimensions** via sliders
✅ **Configurable point count** for pattern density
✅ **Distance-aware offset** based on path proximity
✅ **Distance-aware extrusion** for 3D landscape effect
✅ **Optional lofting** for architectural applications
✅ **Real-time feedback** via Grasshopper preview

Experiment with different slider values and curve inputs to explore the design space!

---

**Authors**: Dibbendu P., Nelly V., David G.  
**Date**: May 2026  
**Course**: MPDA Session 05 - Advanced Python Programming
