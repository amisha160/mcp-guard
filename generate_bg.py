"""
generate_bg.py — Generates the MCP Guard cybersecurity background SVG
and saves it as bg.svg in the project root for verification,
plus prints the base64 data URI for embedding in CSS.

Run: python generate_bg.py
"""
import math, base64, textwrap

W, H = 1920, 1080

def pt(x, y): return f"{x:.1f},{y:.1f}"

lines = []

# ── Background fill: deep graphite gradient
lines.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <!-- Base background gradient -->
  <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%"   stop-color="#060a14"/>
    <stop offset="35%"  stop-color="#0a1020"/>
    <stop offset="70%"  stop-color="#0d1528"/>
    <stop offset="100%" stop-color="#080d18"/>
  </linearGradient>

  <!-- Globe radial glow -->
  <radialGradient id="globeGlow" cx="50%" cy="48%" r="32%">
    <stop offset="0%"   stop-color="#1a3a6e" stop-opacity="0.55"/>
    <stop offset="40%"  stop-color="#0e2040" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="#060a14" stop-opacity="0"/>
  </radialGradient>

  <!-- Shield core radial -->
  <radialGradient id="shieldCore" cx="50%" cy="48%" r="8%">
    <stop offset="0%"   stop-color="#3a7abf" stop-opacity="0.4"/>
    <stop offset="100%" stop-color="#3a7abf" stop-opacity="0"/>
  </radialGradient>

  <!-- Corner ambient light -->
  <radialGradient id="cornerTL" cx="0%" cy="0%" r="45%">
    <stop offset="0%"  stop-color="#1a2e4a" stop-opacity="0.4"/>
    <stop offset="100%" stop-color="#060a14" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="cornerBR" cx="100%" cy="100%" r="40%">
    <stop offset="0%"  stop-color="#0d2236" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="#060a14" stop-opacity="0"/>
  </radialGradient>

  <!-- Clip for globe -->
  <clipPath id="globeClip">
    <circle cx="960" cy="518" r="310"/>
  </clipPath>

  <!-- Node glow filter -->
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glowSoft" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="8" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="shieldGlow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="12" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>

<!-- ── Base background ── -->
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#cornerTL)"/>
<rect width="{W}" height="{H}" fill="url(#cornerBR)"/>
''')

# ── Fine digital grid
lines.append('<!-- ── Fine grid ── -->')
GRID = 65
lines.append(f'<g opacity="0.06" stroke="#7090b0" stroke-width="0.5">')
for x in range(0, W+1, GRID):
    lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>')
for y in range(0, H+1, GRID):
    lines.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
lines.append('</g>')

# ── Globe: latitude/longitude lines
CX, CY, R = 960, 518, 290
lines.append(f'\n<!-- ── Globe ── -->')
lines.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#globeGlow)"/>')
lines.append(f'<g clip-path="url(#globeClip)" opacity="0.18" stroke="#4a80c0" stroke-width="0.7" fill="none">')

# Latitude lines (ellipses)
for lat_deg in range(-75, 90, 15):
    lat = math.radians(lat_deg)
    ry = R * math.cos(lat)
    cy_offset = CY + R * math.sin(lat)
    if ry > 2:
        lines.append(f'<ellipse cx="{CX}" cy="{cy_offset:.1f}" rx="{R:.1f}" ry="{ry:.1f}"/>')

# Longitude lines (ellipses rotated via transform)
for lon_deg in range(0, 180, 15):
    # Draw as rotated ellipses
    angle = lon_deg
    lines.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{R}" ry="{R}" '
                 f'transform="rotate({angle} {CX} {CY})" '
                 f'rx="{R*0.18:.1f}" ry="{R:.1f}"/>')

lines.append('</g>')

# Globe outer ring
lines.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="#3a6aaa" stroke-width="0.8" opacity="0.3"/>')

# Globe glow pulse rings
for i, (r_off, op) in enumerate([(20, 0.12), (50, 0.06), (90, 0.03)]):
    lines.append(f'<circle cx="{CX}" cy="{CY}" r="{R+r_off}" fill="none" stroke="#3a7abf" stroke-width="0.6" opacity="{op}"/>')

# ── Global network nodes — distributed across globe surface and edges
import random
random.seed(42)

NODE_POSITIONS = [
    # Major hub cities approximate screen positions
    (960, 518),   # Center/core
    (720, 390),   # NW quadrant
    (1200, 390),  # NE quadrant
    (720, 650),   # SW quadrant
    (1200, 650),  # SE quadrant
    (540, 300),   # Far NW
    (1380, 300),  # Far NE
    (540, 740),   # Far SW
    (1380, 740),  # Far SE
    (960, 260),   # North pole
    (960, 780),   # South
    (380, 520),   # Far West
    (1540, 520),  # Far East
    (820, 440),
    (1100, 440),
    (820, 600),
    (1100, 600),
    (650, 340),
    (1270, 340),
    (650, 700),
    (1270, 700),
    # Outer/edge nodes
    (180, 200), (300, 150), (160, 420), (200, 660),
    (1740, 200), (1620, 150), (1760, 420), (1720, 660),
    (500, 120), (1420, 120), (480, 950), (1440, 950),
    (900, 100), (1060, 100), (900, 950), (1060, 950),
    # Mid scatter
    (420, 460), (1500, 460), (760, 200), (1160, 200),
    (760, 840), (1160, 840), (600, 520), (1320, 520),
]

# Node sizes: center=large, outer=small
NODE_SIZES = []
for (nx, ny) in NODE_POSITIONS:
    dist = math.sqrt((nx-CX)**2 + (ny-CY)**2)
    r = max(1.5, 5 - dist/120)
    NODE_SIZES.append(r)

# ── Connection edges (connect nearby nodes)
CONNECT_DIST = 380
edges_drawn = set()
edge_lines = []
for i, (ax, ay) in enumerate(NODE_POSITIONS):
    for j, (bx, by) in enumerate(NODE_POSITIONS):
        if i >= j: continue
        d = math.sqrt((ax-bx)**2 + (ay-by)**2)
        if d < CONNECT_DIST:
            alpha = max(0.04, 0.22 * (1 - d/CONNECT_DIST))
            # Brighter for closer pairs
            col = "#4a80c0" if d < 200 else "#3a6090"
            edge_lines.append((ax, ay, bx, by, alpha, col))

lines.append('\n<!-- ── Network edges ── -->')
lines.append('<g stroke-width="0.6" fill="none">')
for (ax, ay, bx, by, alpha, col) in edge_lines:
    lines.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{col}" stroke-opacity="{alpha:.3f}"/>')
lines.append('</g>')

# ── Data-flow path highlights (brighter, thicker selected connections)
FLOW_PATHS = [
    (0, 1), (0, 2), (0, 3), (0, 4),   # core to quadrants
    (1, 5), (2, 6), (3, 7), (4, 8),   # quadrants to corners
    (1, 13), (2, 14), (3, 15), (4, 16), # internal web
    (5, 17), (6, 18), (9, 13), (9, 14),
    (0, 10), (0, 9),
]
lines.append('\n<!-- ── Data flow paths ── -->')
lines.append('<g stroke="#5a9ad4" stroke-width="1.0" fill="none" opacity="0.35">')
for (i, j) in FLOW_PATHS:
    if i < len(NODE_POSITIONS) and j < len(NODE_POSITIONS):
        ax, ay = NODE_POSITIONS[i]
        bx, by = NODE_POSITIONS[j]
        lines.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}"/>')
lines.append('</g>')

# ── Circuit-board traces (orthogonal L-shaped paths)
TRACES = [
    # format: [(x1,y1),(x2,y2),(x3,y3)]  — right-angle turns
    [(0, 200), (260, 200), (260, 420)],
    [(260, 420), (380, 420), (380, 520)],
    [(0, 660), (200, 660), (200, 840), (480, 840)],
    [(1660, 200), (1700, 200), (1700, 420)],
    [(1700, 420), (1540, 420), (1540, 520)],
    [(1920, 660), (1720, 660), (1720, 950)],
    [(500, 0), (500, 120), (650, 120), (650, 240)],
    [(1420, 0), (1420, 120), (1270, 120), (1270, 240)],
    [(480, 1080), (480, 950), (650, 950), (650, 840)],
    [(1440, 1080), (1440, 950), (1270, 950), (1270, 840)],
]

def polyline_d(pts):
    return " ".join(f"{'M' if i==0 else 'L'}{x},{y}" for i,(x,y) in enumerate(pts))

lines.append('\n<!-- ── Circuit traces ── -->')
lines.append('<g stroke="#2fb8a4" stroke-width="1.2" fill="none" opacity="0.18">')
for trace in TRACES:
    d = polyline_d(trace)
    lines.append(f'<path d="{d}"/>')
    # Terminal dot
    ex, ey = trace[-1]
    lines.append(f'<circle cx="{ex}" cy="{ey}" r="3" fill="#2fb8a4" opacity="0.4"/>')
    # Junction dots at turns
    for pt_coords in trace[1:-1]:
        lines.append(f'<circle cx="{pt_coords[0]}" cy="{pt_coords[1]}" r="2" fill="#2fb8a4" opacity="0.3"/>')
lines.append('</g>')

# ── Nodes (drawn on top of edges)
lines.append('\n<!-- ── Network nodes ── -->')
for i, ((nx, ny), nr) in enumerate(zip(NODE_POSITIONS, NODE_SIZES)):
    is_center = (i == 0)
    is_major  = nr > 3.5
    
    if is_center:
        # Center shield glow
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="40" fill="url(#shieldCore)"/>')
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="22" fill="none" stroke="#4a80c0" stroke-width="0.8" opacity="0.5" filter="url(#glowSoft)"/>')
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="12" fill="none" stroke="#5a9ad4" stroke-width="1.0" opacity="0.7"/>')
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="{nr:.1f}" fill="#6aaee0" opacity="0.9" filter="url(#glow)"/>')
    elif is_major:
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="{nr*3:.1f}" fill="#3a7abf" opacity="0.08"/>')
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="{nr:.1f}" fill="#5a90cc" opacity="0.85" filter="url(#glow)"/>')
    else:
        lines.append(f'<circle cx="{nx}" cy="{ny}" r="{nr:.1f}" fill="#4a7ab8" opacity="0.7"/>')

# ── Central security shield (foreground decorative element)
lines.append('\n<!-- ── Central shield ── -->')
sx, sy, sr2 = CX, CY, 75

# Shield bezier path (pointed bottom, rounded top)
shield_path = (
    f"M {sx},{sy-sr2} "
    f"C {sx+sr2},{sy-sr2*0.65} {sx+sr2},{sy+sr2*0.15} {sx},{sy+sr2} "
    f"C {sx-sr2},{sy+sr2*0.15} {sx-sr2},{sy-sr2*0.65} {sx},{sy-sr2} Z"
)
lines.append(f'<path d="{shield_path}" fill="#3a7abf" fill-opacity="0.06" stroke="#4a8ad0" stroke-width="1.0" stroke-opacity="0.5" filter="url(#shieldGlow)"/>')
lines.append(f'<path d="{shield_path}" fill="none" stroke="#5a9ad4" stroke-width="0.6" stroke-opacity="0.7"/>')

# Inner shield detail lines
lines.append(f'<line x1="{sx}" y1="{sy-sr2*0.55}" x2="{sx}" y2="{sy+sr2*0.6}" stroke="#4a8ad0" stroke-width="0.5" stroke-opacity="0.4"/>')
lines.append(f'<line x1="{sx-sr2*0.4}" y1="{sy-sr2*0.1}" x2="{sx+sr2*0.4}" y2="{sy-sr2*0.1}" stroke="#4a8ad0" stroke-width="0.5" stroke-opacity="0.4"/>')

# ── Abstract code stream lines (right edge)
lines.append('\n<!-- ── Code stream elements ── -->')
lines.append('<g fill="#2a5a8a" opacity="0.12" font-family="monospace" font-size="9">')
code_chars = "01 AF B2 7C E1 3D 99 F0 2A 8E 14 C6".split()
for i, ch in enumerate(code_chars * 3):
    ex = random.randint(50, 250)
    ey = 80 + i * 28
    if ey > H - 50: break
    lines.append(f'<text x="{ex}" y="{ey}">{ch}</text>')
    ex2 = W - random.randint(50, 250)
    lines.append(f'<text x="{ex2}" y="{ey}">{ch}</text>')
lines.append('</g>')

# ── Atmospheric vignette overlay
lines.append('\n<!-- ── Vignette ── -->')
lines.append(f'''<radialGradient id="vignette" cx="50%" cy="50%" r="70%">
  <stop offset="0%"   stop-color="transparent"/>
  <stop offset="100%" stop-color="#030609" stop-opacity="0.75"/>
</radialGradient>
<rect width="{W}" height="{H}" fill="url(#vignette)"/>''')

lines.append('</svg>')

SVG_CONTENT = "\n".join(lines)

# Save as file for inspection
with open("bg.svg", "w", encoding="utf-8") as f:
    f.write(SVG_CONTENT)

# Encode as base64 data URI
b64 = base64.b64encode(SVG_CONTENT.encode("utf-8")).decode("ascii")
DATA_URI = f"data:image/svg+xml;base64,{b64}"

print(f"bg.svg written ({len(SVG_CONTENT)//1024}KB)")
print(f"Base64 data URI length: {len(DATA_URI)} chars")
print(f"DATA_URI prefix: {DATA_URI[:80]}...")

# Also write the data URI to a file so dashboard.py can read it
with open("bg_data_uri.txt", "w", encoding="utf-8") as f:
    f.write(DATA_URI)
print("bg_data_uri.txt written")
