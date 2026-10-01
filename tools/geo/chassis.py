"""Reference-driven compound shell, authored in metres in Blender world space.

Existing named chassis nodes remain independent. Shared parameterized surfaces
let damage/energy inserts follow the shell without changing runtime ownership.
Wheel engineering and rider contacts are deliberately external to these builders.
"""
import math
import bmesh
from mathutils import Matrix, Vector
from . import _lib as L
from .rider_clearance import torso_underside_height_limit, torso_outside_lateral_min, capsule_axis_interval, rider_capsules

def _box(bm, center, half, rot=None):
    """center = world position, half = (hx, hy, hz) half-extents - the deck
    table's own convention, so a panel's size can be read straight off it."""
    m = Matrix.Translation(Vector(center))
    if rot is not None:
        m = m @ rot
    L.box(bm, m, tuple(2 * h for h in half))


def _bolt(bm, center, rot=None, r=0.006, depth=0.010, segments=10):
    m = Matrix.Translation(Vector(center))
    if rot is not None:
        m = m @ rot
    L.cylinder(bm, m, r, depth, segments=segments)


def _row(p0, p1, count):
    """Evenly spaced world points from p0 to p1, inclusive."""
    a, b = Vector(p0), Vector(p1)
    if count <= 1:
        return [a.lerp(b, 0.5)]
    return [a.lerp(b, i / (count - 1)) for i in range(count)]


def _bolt_row(bm, p0, p1, count, **kw):
    for c in _row(p0, p1, count):
        _bolt(bm, c, **kw)


def _bracket(bm, center, half, bolt_r=0.0055, bolt_depth=0.009):
    """A milled standoff block plus its two retaining bolts - the visible
    construction logic that carries a shell back to the backbone, so the gap
    between them reads as a serviced assembly rather than a floating panel."""
    _box(bm, center, half)
    bx, by, bz = half
    for s in (-1, 1):
        _bolt(bm, (center[0] + bx * s * 0.55, center[1], center[2] + bz + bolt_depth * 0.4),
              r=bolt_r, depth=bolt_depth)


def _hatch_outline(bm, center_x, y, z, half_w, half_h, rot=None):
    """A proud rectangular seam standing off a flank - reads as a service
    access panel once the caller's bevel catches its edges."""
    for dz in (-half_h, half_h):
        _box(bm, (center_x, y, z + dz), (half_w, 0.004, 0.005), rot)
    for dx in (-half_w, half_w):
        _box(bm, (center_x + dx, y, z), (0.005, 0.004, half_h), rot)



def _interp(points, t):
    """Monotone cubic profiles: continuous tangents without landmark overshoot.

    Zeroing every landmark's tangent creates scalloped automotive highlights.
    Harmonic interior tangents preserve both the authored extrema and smooth
    longitudinal flow; endpoint slopes are clamped to the neighboring secant.
    """
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]
    h=[b[0]-a[0] for a,b in zip(points,points[1:])]
    d=[(b[1]-a[1])/step for a,b,step in zip(points,points[1:],h)]
    m=[d[0]]
    for i in range(1,len(points)-1):
        if d[i-1]*d[i] <= 0:
            m.append(0.0)
        else:
            w1=2*h[i]+h[i-1]
            w2=h[i]+2*h[i-1]
            m.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
    m.append(d[-1])
    for i,((a,va),(b,vb)) in enumerate(zip(points,points[1:])):
        if t <= b:
            f=(t-a)/(b-a)
            return ((2*f**3-3*f**2+1)*va+(f**3-2*f**2+f)*h[i]*m[i]
                    +(-2*f**3+3*f**2)*vb+(f**3-f**2)*h[i]*m[i+1])
    return points[-1][1]


def _reactor_center(dims):
    return dims.get("reactorCenterX", .30), dims.get("reactorCenterZ", .40)


def _rear_wheel_x(dims):
    return dims["wheelbase"] * .5


def _tail_end(dims):
    # Rear body terminates near the outer wheel envelope like the approved side/rear refs.
    return min(dims["length"] * .5 - .035,
               _rear_wheel_x(dims) + dims["wheelOuterDiameter"] * .44)


def skin(bm, surface, nu=40, nv=20, thickness=0.008, inward=(0,-1,0)):
    """Closed sampled compound patch, with real backing and capped perimeter.

    Surface axes are semantic longitudinal/profile coordinates; faces are kept
    separate at the shell boundary so the existing bevel can catch the edge.
    Recalculate winding after mirroring instead of relying on negative scale.
    """
    # Wheel topology is untouched. Curved shell grids use a 64% sampling tier
    # to reserve the runtime triangle budget for the preserved wheel hardware.
    nu, nv = max(2, round(nu * .64)), max(2, round(nv * .64))
    offset = Vector(inward).normalized()*thickness
    layers=[]
    for layer in range(2):
        grid=[]
        for i in range(nu+1):
            row=[]
            for j in range(nv+1):
                row.append(bm.verts.new(Vector(surface(i/nu,j/nv))+offset*layer))
            grid.append(row)
        layers.append(grid)
    for g in layers:
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((g[i][j],g[i+1][j],g[i+1][j+1],g[i][j+1]))
    a,b=layers
    for i in range(nu):
        for j in (0,nv):
            bm.faces.new((a[i][j],a[i+1][j],b[i+1][j],b[i][j]))
    for j in range(nv):
        for i in (0,nu):
            bm.faces.new((a[i][j],a[i][j+1],b[i][j+1],b[i][j]))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    return bm


def nose_surface(dims, side, u, v):
    """Deep wedge behind front wheel, crowned across both profile directions."""
    z=.125+.815*v
    cx=-dims['wheelbase']/2
    r=dims['wheelOuterDiameter']/2+.012
    # The real wheel circle sets the front termination, not its lateral width.
    arch=cx+math.sqrt(max(.0001,r*r-(z-.46)**2))+.006-.12*(1-v)**.65
    rear=_interp([(0,-.030),(.32,-.080),(.65,-.160),(.82,-.350),(1,-.740)],v)
    x=arch+(rear-arch)*u
    # Deliberate broad shoulder behind the wheel, tapering into the waist.
    shoulder=_interp([(-1.50,.255),(-1.18,.300),(-.88,.360),
                      (-.55,.342),(-.18,.305),(.08,.300)],x)
    y=shoulder+.004*math.sin(math.pi*u)*math.sin(math.pi*v)
    return (x,side*y,z)


def mid_surface(dims,side,u,v):
    """Front shell continuation stopping at the reactor's swept circular opening."""
    z=.145+.658*v
    front=nose_surface(dims,side,1,(z-.125)/.815)[0]+.004
    rx, rz = _reactor_center(dims)
    rear=rx-math.sqrt(max(.0004,.238**2-(z-rz)**2))
    x=front+(rear-front)*u
    # Deep compound waist: tuck beneath the rider's thighs, then flare into
    # the coaming above them. The forward seam matches the nose exactly.
    rail_u=max(0,min(1,(x+.285)/.820))
    rail_y=coaming_surface(dims,side,rail_u,1)[1]*side
    waist=_interp([(.145,.184),(.39,.204),(.53,.132),(.68,.132),(.745,.139),(.803,rail_y)],z)
    nose_y=abs(nose_surface(dims,side,1,(z-.125)/.815)[1])
    blend=min(1,max(0,(x-front)/max(.006,-.082-front)))
    blend=blend*blend*(3-2*blend)
    y=nose_y+(waist-nose_y)*blend
    return (x,side*y,z)


def tail_floor(x, dims=None):
    end = _tail_end(dims) if dims is not None else 1.485
    u=(x-.495)/max(.001,end-.495)
    return _interp([(0,.748),(.15,.792),(.38,.882),(.70,.958),(1,.918)],u)


def tail_outer(x, dims=None):
    end = _tail_end(dims) if dims is not None else 1.485
    u=(x-.495)/max(.001,end-.495)
    return _interp([(0,.180),(.35,.260),(.62,.320),(.82,.300),(1,.220)],u)


def rear_surface(dims,side,u,v):
    """Fixed shoulder meets the independently hinged canopy at a 4 mm seam."""
    x=.535+(_tail_end(dims)-.535)*u
    lower=_interp([(0,.57),(.24,.69),(.58,.85),(1,.905)],u)
    upper=tail_floor(x,dims)-.004
    z=lower+(upper-lower)*v
    outer=.285+.025*math.sin(math.pi*u)
    y=outer+(tail_outer(x,dims)-outer)*v**4
    return (x,side*y,z)


def sill_surface(dims,side,u,v):
    x0, x1 = -.740, _rear_wheel_x(dims) - .100
    x=x0+(x1-x0)*u
    z=.130+.055*u**5+.020*(1-u)**6+.033*v+.008*math.sin(math.pi*u)
    return x,side*(.170+.012*math.sin(math.pi*u)+.011*v),z


def saddle_surface(u,v):
    cross=2*v-1
    x=-.105+.480*u
    width=_interp([(0,.046),(.45,.057),(1,.053)],u)
    z=_interp([(0,.495),(.31,.492),(.60,.617),(1,.695)],u)
    y=width*cross
    limit=torso_underside_height_limit(x,y,margin=.018)
    if limit is not None:
        z=min(z,limit-.004)
    return x,y,z+.003*cross*cross


def _keel(bm,x0,x1,z0,z1,width):
    def shape(u,v):
        x=x0+(x1-x0)*u
        y=(2*v-1)*width*(.70+.30*math.sin(math.pi*u))
        z=z0+(z1-z0)*math.sin(math.pi*u)+.022*(2*v-1)**2
        return x,y,z
    skin(bm,shape,48,16,thickness=.018,inward=(0,0,-1))


def build_body_core(dims):
    bm=L.new_bm()
    # Real tub around the forward support, ending ahead of the reactor.
    _keel(bm,-.50,.05,.30,.465,.115)
    # Reactor cradle is below its rotating envelope, not a box through the core.
    _keel(bm,-.16,.59,.143,.161,.12)
    return bm


def build_body_spine(dims):
    bm=L.new_bm()
    # Low recessed chest/rider channel; twin edge rails leave the rider inserted.
    for side in (-1,1):
        def shape(u,v,side=side):
            x=-.45+1.02*u
            z=_interp([(0,.61),(.15,.49),(.35,.545),(.55,.64),(.8,.70),(1,.735)],u)
            inner=_interp([(0,.062),(.4,.061),(.75,.074),(1,.096)],u)
            outer=_interp([(0,.111),(.4,.099),(.75,.112),(1,.145)],u)
            y=side*(inner+(outer-inner)*v)
            for capsule in rider_capsules()[:2]:
                interval=capsule_axis_interval(capsule,2,(x,y,0),margin=.018)
                if interval is not None:
                    z=min(z,interval[0]-.012)
            return x,y,z+.009*math.sin(math.pi*v)
        skin(bm,shape,56,10,.012,(0,0,-1))
    # Graphite rider-channel liner above the existing metal mounting substrate.
    def liner(u,v):
        x,y,z=saddle_surface(u,.035+.93*v)
        return x,y,z+.0035
    skin(bm,liner,40,12,.003,(0,0,-1))
    return bm


def build_belly(dims):
    bm=L.new_bm()
    _keel(bm,-.60,.61,.129,.156,.165)
    return bm


def build_underbody(dims):
    bm=L.new_bm()
    _keel(bm,-.62,.61,.110,.128,.147)
    # Three purposeful shallow diffuser channels, not a forest of fins.
    for y in (-.09,0,.09):
        def fin(u,v,y=y):
            return .38+.22*u,y+.004*(2*v-1),.111+.020*u
        skin(bm,fin,12,2,.006,(0,0,-1))
    return bm


def nose_shell(dims,side):
    bm=L.new_bm()
    skin(bm,lambda u,v:nose_surface(dims,side,u,v),44,44,.008,(0,-side,0))
    # Inner wheel-well bridges tire-side clearance to the broad fairing face.
    def wheelwell(u,v):
        x,outer,z=nose_surface(dims,side,0,u)
        inner=dims.get("frontWheelSectionWidth",dims["wheelSectionWidth"])/2+.018
        for capsule in rider_capsules()[2:]:
            interval=capsule_axis_interval(capsule,1,(x,0,z),margin=.018)
            if interval:
                inner=max(inner,max(abs(q) for q in interval))
        return x+.006*math.sin(math.pi*v),side*(inner+(abs(outer)-inner)*v),z
    skin(bm,wheelwell,40,12,.004,(1,0,0))
    # Partial upper wheel well rolls from side shoulder across the tire crown.
    def fender(u,v):
        a=math.radians(24+132*u)
        r=dims['wheelOuterDiameter']/2+.024+.008*math.sin(math.pi*v)
        half=dims.get("frontWheelSectionWidth",dims["wheelSectionWidth"])/2
        y0=half+.016
        return (-dims['wheelbase']/2+r*math.cos(a),side*(y0+(.350-y0)*v),
                dims['wheelOuterDiameter']/2+r*math.sin(a))
    skin(bm,fender,48,18,.008,(0,-side,0))
    # Close the crown across the front wheel/hood, then peel apart into the
    # rider channel. The outer edge uses the same wedge termination exactly.
    def crown(u,v):
        along=.55+.45*u
        x,outer,z=nose_surface(dims,side,1,along)
        inner=.125*(1-u)**2
        # Recess the hood around the rider rather than spanning the torso.
        for capsule in rider_capsules()[:2]:
            interval=capsule_axis_interval(capsule,1,(x,0,z),margin=.018)
            if interval:
                inner=max(inner,max(abs(q) for q in interval))
        y=side*(inner+(abs(outer)-inner)*v)
        return x,y,z+.012*math.sin(math.pi*v)
    skin(bm,crown,34,18,.009,(0,0,-1))
    # Broad faceted front cowl visible in the exact handlebar/front reference.
    # Two mirrored halves meet on centerline; the tire remains physically clear.
    def front_cowl(u,v):
        z=.735+.245*u
        width=.350-.065*u
        y=side*(.006+width*v)
        offset=_interp([(0,.415),(.52,.315),(1,.120)],u)
        x=-dims['wheelbase']/2+offset+.012*(1-v)
        return x,y,z
    skin(bm,front_cowl,30,18,.009,(1,0,0))
    return bm


def coaming_surface(dims,side,u,v):
    """Crowned, tapered lip enclosing the recessed rider channel."""
    x=-.285+.820*u
    z=_interp([(0,.807),(.44,.800),(.68,.826),(1,.874)],u)
    inner=_interp([(0,.139),(.40,.105),(.70,.079),(1,.052)],u)
    outer=_interp([(0,.291),(.40,.220),(.70,.170),(1,.102)],u)
    return x,side*(inner+(outer-inner)*v),z-.015*(1-v)+.020*math.sin(math.pi*v)


def mid_shell(dims,side):
    bm=L.new_bm()
    skin(bm,lambda u,v:mid_surface(dims,side,u,v),24,40,.004,(0,-side,0))
    # Upper arch frames the reactor, connecting to rear shoulders without burial.
    def brow(u,v):
        a=math.radians(25+132*u)
        r=.238+.037*v
        return .30+r*math.cos(a),side*(.304+.008*math.sin(math.pi*v)),.40+r*math.sin(a)
    skin(bm,brow,48,10,.010,(0,-side,0))
    # Raised continuous coaming surrounds, rather than fills, the rider channel.
    skin(bm,lambda u,v:coaming_surface(dims,side,u,v),48,14,.007,(0,0,-1))
    # Recessed fixed liner closes the visible opening under the deployable tail.
    # It flows out of the coaming and stays lateral to the rider's thigh capsule.
    def tail_root(u,v):
        x=.37+.18*u
        top=_interp([(0,.797),(.70,.833),(1,.848)],u)
        lower=_interp([(0,.775),(.55,.780),(1,.789)],u)
        y=.294+.004*math.sin(math.pi*u)-.004*v
        return x,side*y,lower+(top-lower)*v
    skin(bm,tail_root,16,10,.006,(0,-side,0))
    return bm


def rear_shell(dims,side):
    bm=L.new_bm()
    skin(bm,lambda u,v:rear_surface(dims,side,u,v),40,18,.009,(0,-side,0))
    # Outer rear fender follows the wheel crown instead of ending at the axle.
    def rear_fender(u,v):
        a=math.radians(28+124*u)
        r=dims['wheelOuterDiameter']/2+.026+.007*math.sin(math.pi*v)
        half=dims.get("rearWheelSectionWidth",dims["wheelSectionWidth"])/2
        y0=half+.016
        return (_rear_wheel_x(dims)+r*math.cos(a),side*(y0+(.365-y0)*v),
                dims['wheelOuterDiameter']/2+r*math.sin(a))
    skin(bm,rear_fender,48,18,.008,(0,-side,0))
    # A tapered lower haunch makes the rear wheel part of the body volume.
    # Keep its face and backing outside the protected tire/gyro envelopes.
    def lower_haunch(u,v):
        z=.165+.430*v
        front=.540+.010*math.sin(math.pi*v)
        back=_interp([(0,.765),(.45,.666),(1,.614)],v)
        x=front+(back-front)*u
        y=.335+.016*math.sin(math.pi*u)*math.sin(math.pi*v)
        return x,side*y,z
    skin(bm,lower_haunch,14,24,.008,(0,-side,0))
    return bm


def armor(dims,side):
    bm=L.new_bm()
    # Carbon sill connects the masses with a subtle rear upsweep.
    skin(bm,lambda u,v:sill_surface(dims,side,u,v),64,8,.009,(0,-side,0))
    return bm
