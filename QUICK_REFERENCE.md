# QUICK REFERENCE - VORONOI GRASSHOPPER SCRIPT

## 5-Minute Setup

1. **Open Grasshopper** in Rhino
2. **Add Python Script component** (Params > Input > Python Script)
3. **Copy code from** `VORONOI/voronoi_1.py`
4. **Wire 7 inputs** (see Input Checklist below)
5. **Wire outputs** to Preview components
6. **Adjust sliders** and watch the magic happen!

---

## Input Checklist

```
INPUT 0: Length Slider (Float)             [Min: 1, Max: 200, Default: 50]
INPUT 1: Width Slider (Float)              [Min: 1, Max: 200, Default: 50]
INPUT 2: Num Points Slider (Integer)       [Min: 1, Max: 500, Default: 20]
INPUT 3: Input Curve (Curve Object)        [Can be any planar curve]
INPUT 4: Offset Distance Slider (Float)    [Min: 0.1, Max: 50, Default: 5]
INPUT 5: Move Distance Slider (Float)      [Min: 0, Max: 100, Default: 10]
INPUT 6: Loft Toggle (Boolean)             [True or False]
```

---

## Output Checklist

```
OUTPUT 0: rect_surface        → Brep/Preview Component
OUTPUT 1: seed_points         → Point Display Component
OUTPUT 2: output_curves       → Curve Display Component
OUTPUT 3: output_geometry     → Brep/Preview Component ⭐ (Main Output)
```

---

## Key Parameters & Effects

| Slider | Effect | Increase → |
|--------|--------|-----------|
| **Length** | Width of rectangle (X) | Wider rectangle |
| **Width** | Height of rectangle (Y) | Taller rectangle |
| **Num Points** | Number of Voronoi cells | More cells (slower) |
| **Offset Distance** | How much offset near/far path | More offset variation |
| **Move Distance** | Max extrusion height | Taller peaks (near path) |
| **Loft Toggle** | Connect original to moved | OFF = flat surfaces; ON = vertical walls |

---

## Visual Guide: What Each Step Does

### Step 1: Rectangle & Points
```
(Before)                    (After)
                           ●  ●  ●
                          ● ●  ● ●
        □□□               ●  ●  ●
        □□□    ──→        ●  ●  ●
        □□□               ●  ●  ●
```
- Creates XY plane rectangle
- Spreads N random points on surface

### Step 2: Voronoi Diagram
```
(Points)                    (Voronoi Cells)
●  ●  ●                    ┌──┬──┬──┐
● ●  ● ●       ──→         ├──┼──┼──┤
●  ●  ●                    ├──┼──┼──┤
●  ●  ●                    └──┴──┴──┘
●  ●  ●
```
- Creates closed regions around each point
- Cells clipped to rectangle boundary

### Step 3: Offset & Path
```
(Input Curve)              (Offset Curves & Lofted Path)
      ╱╲                   ┌─ (outer offset)
     ╱  ╲         ──→      │  ╱╲
    ╱────╲                 │ ╱  ╲  (lofted surface)
        ╲                  │╱────╲
                           └ (inner offset)
```
- Input curve → ±offset → lofted path surface

### Step 4: Distance-Based Offset
```
(Original Cells)          (After Offset)
Near path: ■■■           Near: ░░░ (small)
Far from:  ■■■           Far:  ░░  (large)
```
- Cells near path: smaller offset
- Cells far from path: larger offset

### Step 5: Adaptive Extrusion
```
(From Side)
  Near: ▲▲▲▲▲  ← Tall (max height)
        Path
  Far:  ▲ ▲   ← Short
```
- Cells near path: taller (up to Move Distance)
- Cells far from path: shorter (close to 0)

### Step 6: Optional Lofting
```
WITHOUT Loft Toggle (OFF):    WITH Loft Toggle (ON):
    ▲ ▲ ▲                          ╱╲ ╱╲ ╱╲
    │ │ │                         ╱  ╲│  ╲│  ╲
 ─────────────                  ┌─────────────┐
    Base                        │  Lofted     │ ← Walls
                                │  surfaces   │
```
- OFF: Only moved surfaces visible
- ON: Lofted walls connect ground to peaks

---

## Common Configurations

### Config A: Flat Pattern (Artistic)
```
Length: 60          Width: 60
Num Points: 25      Offset Distance: 3
Move Distance: 0    Loft Toggle: OFF
Input Curve: Any linear curve
```
**Result**: Flat Voronoi pattern with subtle offset variations

---

### Config B: Organic Landscape
```
Length: 80          Width: 80
Num Points: 35      Offset Distance: 2.5
Move Distance: 15   Loft Toggle: OFF
Input Curve: Curved serpentine path
```
**Result**: 3D topographic landscape with peaks/valleys

---

### Config C: Architectural Shells
```
Length: 100         Width: 80
Num Points: 40      Offset Distance: 2
Move Distance: 20   Loft Toggle: ON
Input Curve: Circular or organic curve
```
**Result**: Complex lofted shell structures

---

### Config D: Fine Detail Pattern
```
Length: 50          Width: 50
Num Points: 60      Offset Distance: 1
Move Distance: 8    Loft Toggle: OFF
Input Curve: Tightly wound spiral
```
**Result**: Dense fine pattern with precise detail control

---

## Troubleshooting at a Glance

| Problem | Check | Solution |
|---------|-------|----------|
| No output geometry | All inputs wired? | Wire all 7 inputs |
| Blank/empty surfaces | Num Points = 0? | Set Num Points ≥ 5 |
| All same height | Move Distance = 0? | Increase Move Distance slider |
| No variation in offset | Offset Distance = 0? | Increase Offset Distance slider |
| Loft toggle doesn't work | Are moved surfaces valid? | Check console for errors |
| Script runs very slowly | Num Points too high? | Reduce to <50 points |
| "No input curve" warning | Curve input missing? | Wire a curve to INPUT 3 |

---

## Export & Fabrication

### Export Geometry to Rhino
1. Right-click on OUTPUT 3 (geometry output)
2. Select "Bake" or wire to `Rhino Export` component
3. Geometry appears in Rhino document
4. Export as `.step`, `.iges`, or `.stl` as needed

### Adjust for 3D Printing
- **Decrease Move Distance** to reduce wall height
- **Increase Offset Distance** for structural integrity
- **Reduce Num Points** for simpler geometry (fewer parts to print)
- **Add base surface** to ensure solid printing

---

## Tips & Tricks

✨ **Tip 1**: Use a slider for Move Distance to animate smoothly
✨ **Tip 2**: Change input curve dynamically via Grasshopper sketch
✨ **Tip 3**: Record slider animation for presentation video
✨ **Tip 4**: Combine multiple Voronoi outputs for compound patterns
✨ **Tip 5**: Export as mesh for faster rendering
✨ **Tip 6**: Layer different configurations (multiple Python components)

---

## Advanced Customization

### Change Offset Direction (Inward → Outward)
In script, find line ~470:
```python
offset_result = cell.Offset(plane, -offset_amount, ...)
```
Change `-offset_amount` to `+offset_amount`

### Change Extrusion Direction (Z → Surface Normal)
In script, find line ~550:
```python
normal = Vector3d(0, 0, 1)  # ← Change this
```
Use surface normal calculation instead

### Reverse Height Logic (Close→Low, Far→High)
In script, find line ~475:
```python
height = max_height * (1.0 - norm_dist)
```
Change to:
```python
height = max_height * norm_dist
```

---

## Performance Reference

| Setup | Num Points | Processing Time | Cells | Notes |
|-------|-----------|-----------------|-------|-------|
| Fast | 10 | <0.5s | ~10 | For real-time interaction |
| Balanced | 25 | ~1-2s | ~25 | Recommended for exploration |
| Detailed | 50 | ~3-5s | ~50 | Good output quality |
| Complex | 100+ | 10-30s | 100+ | Final render/export |

---

## Video Demo Script (Optional)

1. **Start**: Set all sliders to defaults (L=50, W=50, Pts=20, Off=5, Mov=10, Loft=OFF)
2. **Adjust Length**: Slowly drag Length slider left/right (watch rectangle change)
3. **Add Points**: Increase Num Points to 40 (watch Voronoi cells multiply)
4. **Adjust Offset**: Increase Offset Distance to 10 (watch cells offset more)
5. **Add Height**: Increase Move Distance to 20 (watch surfaces rise)
6. **Enable Loft**: Toggle Loft ON (watch vertical walls appear)
7. **Final Result**: Render OUTPUT 3 at high quality

---

## Quick Commands Reference

```python
# Test if script loaded:
print("Script loaded successfully!")

# Check Grasshopper version:
print(ghenv.Component)

# Enable console debugging:
import sys
sys.stdout.write("Debug message here\n")
```

---

## Getting Help

**Script Not Running?**
1. Check Grasshopper console (right-click component)
2. Look for error messages
3. Verify all inputs are connected
4. Try with default slider values first

**Questions about Algorithm?**
- See TECHNICAL_DOCUMENTATION.md

**Questions about Setup?**
- See GRASSHOPPER_SETUP_GUIDE.md

**Questions about Code?**
- Check comments in VORONOI/voronoi_1.py

---

**Quick Start Card v1.0 — May 2026**  
**Created for MPDA Session 05**
