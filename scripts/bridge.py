"""Sydney Harbour Bridge: arch trusses, deck, pylons, approach spans and abutments."""
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from shapely.geometry import Polygon

from meshkit import add_beam, add_box, add_face, new_object

# Sydney Harbour Bridge. Heights are metres above mean sea level.
# Sources: [W] en.wikipedia.org/wiki/Sydney_Harbour_Bridge, [P] Pylon Lookout "Bridge facts" (2003),
# [R] railtram.com.au/sydney-harbour-bridge, [I] IStructE "The Sydney Harbour Bridge".
BRIDGE_SPAN = 503.0             # between bearing pins [W][P]
BRIDGE_ARCH_TOP = 134.0         # top of the arch [W][P]
BRIDGE_PANELS = 28              # arch truss panels [W][P]
BRIDGE_TRUSS_DEPTH_CROWN = 18.0  # chord centre to chord centre at mid-span [W]
BRIDGE_TRUSS_DEPTH_ENDS = 57.0   # ... and at the pylons [W]
BRIDGE_PIN_HEIGHT = 4.0         # reasoned: pins sit at the abutment-tower base just above the water
                                # (ground there is 2–4 m); gives top-chord ends ≈ 61 m, about two thirds
                                # up the pylons as in photographs
BRIDGE_CLEARANCE = 49.0         # under the deck at mid-span [W][P]
BRIDGE_DECK_DEPTH = 4.0         # reasoned: 170 ft (51.8 m) headroom to the roadway ("Railway Wonders of
                                # the World") minus 49 m clearance ≈ 3 m, plus surfacing; also makes the
                                # mid-span hanger ≈ 59 m against the published longest hanger of 58.8 m [P]
BRIDGE_APPROACH_GRADE = 1 / 40  # roadway and rail rise at 1 in 40 to a crest on the bridge [R]
BRIDGE_CREST_CURVE = 200.0      # reasoned: parabolic crest joining the two 1:40 grades (offset 1.25 m)
BRIDGE_DECK_WIDTH = 48.8        # [W]
BRIDGE_TRUSS_OFFSET = 14.5      # half the spacing of the two arch trusses
BRIDGE_PYLON_HEIGHT = 89.0      # [W][P]
BRIDGE_TOTAL_LENGTH = 1149.0    # abutment to abutment, including the approach spans [W][P]
BRIDGE_APPROACH_SPANS = 5       # steel approach spans on each side [I]
BRIDGE_PYLON_BASE = (48.0, 68.0)    # abutment tower base, along x across [P]
BRIDGE_PIER_SIZE = 9.0              # square granite approach columns
BRIDGE_PIER_OFFSET = 18.0           # columns stand either side of the axis
BRIDGE_ABUTMENT_LENGTH = 20.0


class BridgeLayout:
    """Shared geometry of the bridge: local frame, deck profile and pier positions.

    Local coordinates: s along the axis from the midpoint between the pylon pairs (north +),
    t across (east +), z up.
    """

    def __init__(self, anchors):
        south = Vector((*anchors["bridge_south_pylons"], 0))
        north = Vector((*anchors["bridge_north_pylons"], 0))
        self.mid = (south + north) / 2
        self.u = (north - south).normalized()
        self.v = Vector((self.u.y, -self.u.x, 0))
        self.up = Vector((0, 0, 1))
        self.frame = Matrix((self.u, self.v, self.up)).transposed()
        self.half_pylon_gap = (north - south).length / 2
        self.half_span = BRIDGE_SPAN / 2
        self.end = BRIDGE_TOTAL_LENGTH / 2

    def world(self, s, t, z):
        return self.mid + self.u * s + self.v * t + self.up * z

    def deck_top(self, s):
        """Roadway level: 1:40 grades either side of a parabolic crest at mid-span."""
        crest = BRIDGE_CLEARANCE + BRIDGE_DECK_DEPTH
        half_curve = BRIDGE_CREST_CURVE / 2
        s = abs(s)
        if s <= half_curve:
            return crest - BRIDGE_APPROACH_GRADE * s * s / BRIDGE_CREST_CURVE
        return crest - BRIDGE_APPROACH_GRADE * (s - half_curve / 2)

    def lower_chord(self, s):
        """Centre line of the lower chord: bearing pin at each end, parabolic to the crown."""
        crown = BRIDGE_ARCH_TOP - 1.5 - BRIDGE_TRUSS_DEPTH_CROWN
        return BRIDGE_PIN_HEIGHT + (crown - BRIDGE_PIN_HEIGHT) * (1 - (s / self.half_span) ** 2)

    def upper_chord(self, s):
        """Centre line of the upper chord; its 3 m deep section tops out at the published arch height."""
        ends = BRIDGE_PIN_HEIGHT + BRIDGE_TRUSS_DEPTH_ENDS
        crown = BRIDGE_ARCH_TOP - 1.5
        return ends + (crown - ends) * (1 - (s / self.half_span) ** 2)

    def pier_stations(self):
        """Distances from the midpoint of the approach piers on one side (not pylon or abutment)."""
        first = self.half_pylon_gap + BRIDGE_PYLON_BASE[0] / 2
        step = (self.end - BRIDGE_ABUTMENT_LENGTH - first) / BRIDGE_APPROACH_SPANS
        return [first + step * k for k in range(1, BRIDGE_APPROACH_SPANS)]

    def footprints(self):
        """Ground footprints of everything that stands on land: pylon bases, piers, abutments."""
        boxes = []
        for sign in (-1, 1):
            boxes.append((sign * self.half_pylon_gap, 0.0, *BRIDGE_PYLON_BASE))
            for s in self.pier_stations():
                for t in (-BRIDGE_PIER_OFFSET, BRIDGE_PIER_OFFSET):
                    boxes.append((sign * s, t, BRIDGE_PIER_SIZE, BRIDGE_PIER_SIZE))
            boxes.append((sign * (self.end - BRIDGE_ABUTMENT_LENGTH / 2), 0.0,
                          BRIDGE_ABUTMENT_LENGTH, BRIDGE_DECK_WIDTH))
        polys = []
        for s, t, length, width in boxes:
            corners = [self.world(s + a * length / 2, t + b * width / 2, 0)
                       for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            polys.append(Polygon([(c.x, c.y) for c in corners]))
        return polys


def add_deck(bm, layout, stations, depth, mat_index):
    """Rectangular deck section swept along the profile. UVs: U along the bridge, V across / down."""
    half = BRIDGE_DECK_WIDTH / 2
    # section corners as (across, below roadway), walked around the section
    section = ((-half, 0.0), (half, 0.0), (half, depth), (-half, depth))
    around = [0.0, BRIDGE_DECK_WIDTH, BRIDGE_DECK_WIDTH + depth, 2 * BRIDGE_DECK_WIDTH + depth,
              2 * (BRIDGE_DECK_WIDTH + depth)]
    rings = []
    for s in stations:
        top = layout.deck_top(s)
        rings.append([bm.verts.new(layout.world(s, t, top - down)) for t, down in section])
    for k in range(len(stations) - 1):
        s0, s1 = float(stations[k]), float(stations[k + 1])
        for i in range(4):
            j = (i + 1) % 4
            # winding (i, j) gives outward normals: up for the roadway, east/west for the sides
            add_face(bm, (rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]), mat_index,
                     ((s0, around[i]), (s0, around[i + 1]), (s1, around[i + 1]), (s1, around[i])))
    add_face(bm, list(reversed(rings[0])), mat_index, [(t, d) for t, d in reversed(section)])
    add_face(bm, rings[-1], mat_index, [(t, d) for t, d in section])


def build_bridge(layout, terrain, col, mats):
    world = layout.world
    half = layout.half_span
    lower, upper = layout.lower_chord, layout.upper_chord
    lower_chord_half_depth = 2.25

    def ground(s, t):
        p = world(s, t, 0)
        return float(terrain.sample([p.x], [p.y])[0])

    bm = bmesh.new()
    steel, granite, deck = 0, 1, 2
    panel = BRIDGE_SPAN / BRIDGE_PANELS
    stations = [-half + i * panel for i in range(BRIDGE_PANELS + 1)]
    hangers = []
    for t in (-BRIDGE_TRUSS_OFFSET, BRIDGE_TRUSS_OFFSET):
        for i in range(BRIDGE_PANELS):
            s0, s1 = stations[i], stations[i + 1]
            add_beam(bm, world(s0, t, lower(s0)), world(s1, t, lower(s1)), 3.0, 4.5, steel)
            add_beam(bm, world(s0, t, upper(s0)), world(s1, t, upper(s1)), 2.5, 3.0, steel)
            diag_from, diag_to = (s0, s1) if (i < BRIDGE_PANELS // 2) else (s1, s0)
            add_beam(bm, world(diag_from, t, lower(diag_from)), world(diag_to, t, upper(diag_to)), 1.4, 1.4, steel)
        for s in stations:
            add_beam(bm, world(s, t, lower(s)), world(s, t, upper(s)), 1.6, 1.6, steel)
            hanger = lower(s) - lower_chord_half_depth - layout.deck_top(s)
            if hanger > 2:
                add_beam(bm, world(s, t, layout.deck_top(s)), world(s, t, lower(s)), 0.9, 0.9, steel)
                hangers.append(hanger)
    for s in stations[2:-2]:
        add_beam(bm, world(s, -BRIDGE_TRUSS_OFFSET, upper(s)), world(s, BRIDGE_TRUSS_OFFSET, upper(s)), 1.2, 1.2, steel)
    print(f"bridge hangers {min(hangers):.1f}–{max(hangers):.1f} m (published 7.3–58.8 m), "
          f"top-chord ends {upper(half) + 1.5:.1f} m")

    # Deck: one continuous loft along the roadway profile (separate boxes would step at the joints)
    deck_depth = BRIDGE_DECK_DEPTH
    add_deck(bm, layout, np.linspace(-layout.end, layout.end, 116), deck_depth, deck)

    girder_depth = 7.0
    for sign in (-1, 1):
        # Abutment tower: solid granite from the ground up to the underside of the deck
        s_pylon = sign * layout.half_pylon_gap
        tower_top = layout.deck_top(s_pylon) - deck_depth
        add_box(bm, world(s_pylon, 0, tower_top / 2), (*BRIDGE_PYLON_BASE, tower_top), layout.frame, granite)
        for t in (-25.0, 25.0):
            add_box(bm, world(s_pylon, t, BRIDGE_PYLON_HEIGHT / 2), (26.0, 18.0, BRIDGE_PYLON_HEIGHT),
                    layout.frame, granite)

        # Approach spans: deck trusses under each deck edge, carried on paired granite columns
        s_from, s_to = sign * layout.half_pylon_gap, sign * layout.end
        for t in (-BRIDGE_PIER_OFFSET, BRIDGE_PIER_OFFSET):
            add_beam(bm, world(s_from, t, layout.deck_top(s_from) - deck_depth - girder_depth / 2),
                     world(s_to, t, layout.deck_top(s_to) - deck_depth - girder_depth / 2),
                     2.0, girder_depth, steel)
        for s in layout.pier_stations():
            s *= sign
            top = layout.deck_top(s) - deck_depth - girder_depth
            for t in (-BRIDGE_PIER_OFFSET, BRIDGE_PIER_OFFSET):
                base = max(ground(s, t), 0.0) - 1.0
                add_box(bm, world(s, t, (base + top) / 2),
                        (BRIDGE_PIER_SIZE, BRIDGE_PIER_SIZE, top - base), layout.frame, granite)

        # Abutment: solid granite block from the deck end down into the ground
        s_abut = sign * (layout.end - BRIDGE_ABUTMENT_LENGTH / 2)
        top = layout.deck_top(s_abut) - deck_depth
        base = min(ground(s_abut, t) for t in (-BRIDGE_DECK_WIDTH / 2, 0, BRIDGE_DECK_WIDTH / 2)) - 1.0
        add_box(bm, world(s_abut, 0, (base + top) / 2),
                (BRIDGE_ABUTMENT_LENGTH, BRIDGE_DECK_WIDTH, top - base), layout.frame, granite)
        print(f"bridge {'north' if sign > 0 else 'south'}: deck at pylon {layout.deck_top(s_pylon):.1f} m, "
              f"at abutment {layout.deck_top(s_to):.1f} m, ground {base + 1:.1f} m")
    print(f"bridge: deck crest {layout.deck_top(0):.1f} m, clearance {layout.deck_top(0) - deck_depth:.1f} m")
    print(f"bridge: pylon centre gap {2 * layout.half_pylon_gap:.1f} m, arch span {BRIDGE_SPAN} m")
    return new_object("HarbourBridge", bm, [mats["steel"], mats["granite"], mats["deck"]], col)
