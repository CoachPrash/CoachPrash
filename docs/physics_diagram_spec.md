# Physics Diagram Spec — AP Physics 1 Manifest Generation

Use this spec to produce `scripts/manifests/physics.json`. Read `content/physics_ap_physics_1_mechanics.json` for concept slugs and content context.

## Manifest Structure

```json
{
  "course": "ap-physics-1-mechanics",
  "subject": "physics",
  "images": [ ...entries... ]
}
```

## Entry Schema

```json
{
  "id": "phys1-001",
  "bucket_key": "images/physics/ap-physics-1-mechanics/<descriptive-name>.svg",
  "category": "mechanics",
  "concept_slug": "<slug from content JSON>",
  "location": "content_html" | "question_html",
  "problem_index": null | 0 | 1 | ...,
  "description": "Human-readable figcaption text",
  "alt_text": "Screen-reader description",
  "params": { "type": "<diagram_type>", ... }
}
```

- `id`: Sequential `phys1-001`, `phys1-002`, etc.
- `bucket_key`: Always `images/physics/ap-physics-1-mechanics/<kebab-name>.svg`
- `category`: Always `"mechanics"`
- `location`: `"content_html"` for concept-level diagrams, `"question_html"` for problem diagrams
- `problem_index`: `null` for content_html; 0-indexed for question_html
- `description`: Shown as figcaption below the diagram. Be descriptive.
- `alt_text`: For accessibility. Describe what the diagram shows.

## Diagram Types & Param Schemas

### 1. `free_body_diagram`

```json
{
  "type": "free_body_diagram",
  "title": "Block on Incline",
  "object_shape": "block" | "circle" | "dot",
  "object_label": "m",
  "object_size": 0.4,
  "incline_angle": 0,
  "show_ground": true,
  "show_axes": false,
  "forces": [
    {
      "name": "weight",
      "type": "gravity" | "normal" | "friction" | "tension" | "applied" | "spring" | "net",
      "angle_deg": 270,
      "length": 1.0,
      "label": "$F_g$",
      "label_offset": [0, 0]
    }
  ]
}
```

Force type determines colour automatically. Common force angles:
- Gravity: 270 (straight down)
- Normal on flat: 90 (straight up)
- Normal on incline: 90 + incline_angle
- Friction up incline: incline_angle
- Friction down incline: 180 + incline_angle
- Tension: direction depends on scenario

**Example — flat surface with friction:**
```json
{
  "type": "free_body_diagram",
  "title": "Block on Flat Surface",
  "forces": [
    {"name": "weight", "type": "gravity", "angle_deg": 270, "length": 0.8, "label": "$F_g$", "label_offset": [-0.2, 0]},
    {"name": "normal", "type": "normal", "angle_deg": 90, "length": 0.8, "label": "$F_N$", "label_offset": [0.2, 0]},
    {"name": "applied", "type": "applied", "angle_deg": 0, "length": 0.6, "label": "$F_a$", "label_offset": [0, 0.15]},
    {"name": "friction", "type": "friction", "angle_deg": 180, "length": 0.3, "label": "$f_k$", "label_offset": [0, 0.15]}
  ]
}
```

**Example — inclined plane:**
```json
{
  "type": "free_body_diagram",
  "title": "Block on 30° Incline",
  "incline_angle": 30,
  "show_axes": true,
  "forces": [
    {"name": "weight", "type": "gravity", "angle_deg": 270, "length": 1.0, "label": "$F_g$", "label_offset": [-0.2, 0]},
    {"name": "normal", "type": "normal", "angle_deg": 120, "length": 0.7, "label": "$F_N$", "label_offset": [-0.15, 0.1]},
    {"name": "friction", "type": "friction", "angle_deg": 30, "length": 0.4, "label": "$f$", "label_offset": [0, 0.15]}
  ]
}
```

### 2. `motion_graph`

```json
{
  "type": "motion_graph",
  "title": "Position vs Time",
  "graph_type": "x-t" | "v-t" | "a-t",
  "x_label": "Time (s)",
  "y_label": "Position (m)",
  "segments": [
    {"t_start": 0, "t_end": 3, "y_start": 0, "y_end": 15},
    {"t_start": 3, "t_end": 5, "y_start": 15, "y_end": 15, "label": "at rest"}
  ],
  "annotations": [
    {"t": 3, "y": 15, "text": "stops", "va": "bottom"}
  ]
}
```

Segments can use `y_start`/`y_end` (linear) or `expr` (Python expression in `t`):
```json
{"t_start": 0, "t_end": 4, "expr": "5*t - 0.5*2*t**2"}
```

### 3. `vector_diagram`

**Components style:**
```json
{
  "type": "vector_diagram",
  "title": "Force Components",
  "style": "components",
  "vectors": [{"magnitude": 50, "angle_deg": 37, "label": "F = 50 N"}]
}
```

**Addition style (head-to-tail):**
```json
{
  "type": "vector_diagram",
  "title": "Vector Addition",
  "style": "addition",
  "vectors": [
    {"magnitude": 3, "angle_deg": 0, "label": "$\\vec{A}$"},
    {"magnitude": 4, "angle_deg": 90, "label": "$\\vec{B}$"}
  ],
  "resultant_label": "$\\vec{R}$"
}
```

### 4. `energy_bar_chart`

```json
{
  "type": "energy_bar_chart",
  "title": "Energy Conservation: Ball Drop",
  "states": [
    {"label": "Top", "KE": 0, "PE": 50},
    {"label": "Mid", "KE": 25, "PE": 25},
    {"label": "Bottom", "KE": 50, "PE": 0}
  ]
}
```

Available energy types: `KE`, `PE`, `W` (work done), `Eth` (thermal/dissipated).

### 5. `collision_diagram`

```json
{
  "type": "collision_diagram",
  "title": "Inelastic Collision",
  "collision_type": "perfectly_inelastic",
  "before": [
    {"label": "A", "mass": 4, "velocity": 6},
    {"label": "B", "mass": 2, "velocity": 0}
  ],
  "after": [
    {"label": "AB", "mass": 6, "velocity": 4}
  ]
}
```

### 6. `circular_motion`

```json
{
  "type": "circular_motion",
  "title": "Uniform Circular Motion",
  "radius": 1.2,
  "positions": [
    {"angle_deg": 0, "show_v": true, "show_ac": true},
    {"angle_deg": 90, "show_v": true, "show_F": true},
    {"angle_deg": 180, "show_v": true, "show_ac": true}
  ]
}
```

- `show_v`: velocity tangent arrow (green)
- `show_ac`: centripetal acceleration arrow toward center (red)
- `show_F`: centripetal force arrow toward center (red, labelled Fc)

### 7. `shm_diagram`

**Wave style (x vs t sinusoid):**
```json
{
  "type": "shm_diagram",
  "style": "wave",
  "title": "Displacement vs Time",
  "amplitude": 0.1,
  "period": 2.0,
  "n_cycles": 2
}
```

**Spring-mass style (horizontal system):**
```json
{
  "type": "shm_diagram",
  "style": "spring_mass",
  "title": "Spring-Mass at Equilibrium",
  "equilibrium_x": 2.0,
  "displacement": 0.5
}
```

### 8. `torque_diagram`

```json
{
  "type": "torque_diagram",
  "title": "Seesaw",
  "beam_length": 3.0,
  "pivot_pos": 0.5,
  "forces": [
    {"pos": 0.0, "angle_deg": 270, "length": 0.6, "label": "$F_1$", "type": "gravity", "show_lever_arm": true, "r_label": "$r_1$"},
    {"pos": 1.0, "angle_deg": 270, "length": 0.4, "label": "$F_2$", "type": "applied", "show_lever_arm": true, "r_label": "$r_2$"}
  ]
}
```

`pos` is a fraction (0.0 = left end, 1.0 = right end). `pivot_pos` is also a fraction.

### 9. `fluid_diagram`

**Buoyancy:**
```json
{
  "type": "fluid_diagram",
  "style": "buoyancy",
  "title": "Buoyant Force on Submerged Object",
  "object_y": -0.3,
  "fg_length": 0.8,
  "fb_length": 0.6
}
```

**Pressure-depth:**
```json
{
  "type": "fluid_diagram",
  "style": "pressure_depth",
  "title": "Pressure Increases with Depth",
  "depth": 3.0,
  "depths_shown": [0.5, 1.5, 2.5]
}
```

**U-tube manometer:**
```json
{
  "type": "fluid_diagram",
  "style": "u_tube",
  "title": "U-Tube Manometer",
  "h_diff": 0.5,
  "left_label": "Water",
  "right_label": "Oil"
}
```

---

## Concept Slug Reference (AP Physics 1)

Below are all 43 concept slugs grouped by topic. For each, recommend 1-2 diagrams. Use `location: "content_html"` for concept-level diagrams. Add `location: "question_html"` for problems that reference a specific physical setup.

### Kinematics (5 concepts)
- `scalars-vectors-1d` → vector_diagram (1D vectors, positive/negative direction)
- `displacement-velocity-acceleration` → motion_graph (x-t and v-t showing constant acceleration)
- `representing-motion` → motion_graph (multi-segment v-t graph)
- `reference-frames-relative-motion` → vector_diagram (addition, relative velocity)
- `vectors-motion-2d` → vector_diagram (components of a 2D vector)

### Force and Translational Dynamics (9 concepts)
- `systems-center-of-mass` → (skip or simple dot diagram — low diagram value)
- `forces-free-body-diagrams` → free_body_diagram (flat surface, all basic forces labeled)
- `newtons-third-law` → free_body_diagram (two objects with action-reaction pairs)
- `newtons-first-law` → free_body_diagram (balanced forces, object at rest or constant v)
- `newtons-second-law` → free_body_diagram (net force → acceleration arrow)
- `gravitational-force` → free_body_diagram (object in freefall, only Fg)
- `kinetic-static-friction` → free_body_diagram (block on surface with friction opposing motion)
- `spring-forces` → shm_diagram (spring_mass style) + motion_graph (F vs x)
- `circular-motion` → circular_motion

### Work, Energy, and Power (5 concepts)
- `translational-kinetic-energy` → energy_bar_chart (single state showing KE)
- `work` → free_body_diagram (force at angle to displacement) or vector_diagram
- `potential-energy` → energy_bar_chart (height vs PE)
- `conservation-of-energy` → energy_bar_chart (3 states: top/mid/bottom)
- `power` → (skip — mostly formula-based, low diagram value)

### Linear Momentum (4 concepts)
- `linear-momentum-concept` → vector_diagram (momentum arrow proportional to mass × velocity)
- `change-in-momentum-impulse` → motion_graph (F vs t graph with area = impulse)
- `conservation-linear-momentum` → collision_diagram (before/after with arrows)
- `elastic-inelastic-collisions` → collision_diagram (elastic vs perfectly inelastic)

### Torque and Rotational Dynamics (6 concepts)
- `rotational-kinematics` → motion_graph (ω-t graph)
- `connecting-linear-rotational` → (skip — formula relationships, low diagram value)
- `torque` → torque_diagram (force at lever arm)
- `rotational-inertia` → (skip — conceptual/formula, low diagram value)
- `rotational-equilibrium` → torque_diagram (balanced seesaw)
- `newtons-second-law-rotational` → torque_diagram (net torque → angular acceleration)

### Energy and Momentum in Rotating Systems (6 concepts)
- `rotational-kinetic-energy` → energy_bar_chart (KE_rot vs KE_trans)
- `torque-and-work` → (skip — closely tied to torque, duplicate)
- `angular-momentum-angular-impulse` → (skip — analogous to linear, low unique diagram value)
- `conservation-angular-momentum` → (skip or reuse circular motion style)
- `rolling` → free_body_diagram (sphere rolling down incline)
- `orbiting-satellites` → circular_motion (satellite around Earth)

### Oscillations (4 concepts)
- `defining-shm` → shm_diagram (spring_mass style at equilibrium)
- `frequency-period-shm` → shm_diagram (wave with period T and amplitude A labeled)
- `representing-analyzing-shm` → shm_diagram (wave, x vs t)
- `energy-shm` → energy_bar_chart (KE and PE at different x positions in oscillation)

### Fluids (4 concepts)
- `internal-structure-density` → (skip — conceptual)
- `pressure` → fluid_diagram (pressure_depth)
- `fluids-newtons-laws` → fluid_diagram (buoyancy)
- `fluids-conservation-laws` → (skip — Bernoulli is complex; or simple pipe diagram)

---

## Rules

1. Target ~55 total entries (concept + problem level combined)
2. Every concept that gets a diagram should have at least 1 `content_html` entry
3. Add `question_html` entries only for problems that describe a specific physical setup needing visualisation (e.g., "A 5 kg block on a 30° incline...")
4. Use consistent force lengths: gravity ~0.8-1.0, normal similar to gravity, friction ~0.3-0.5, applied varies
5. Keep titles short (under 40 chars)
6. For incline problems, always set `show_axes: true`
7. label_offset: use small values like [-0.2, 0] to nudge labels away from arrows
8. All angles in degrees, CCW from +x axis
