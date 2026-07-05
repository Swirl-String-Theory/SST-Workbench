// rodin_mold_clamshell_knot512_6lanes_minor60_sink.scad
// True-groove clamshell mold for a *6-lane* (5,12) Rodin wiring guide.
//
// Lanes:
//   Group A (3-phase): 0°,120°,240° minor-angle offsets
//   Group B (mirrored 3-phase): 60°,180°,300° minor-angle offsets (interleaved)
// This yields *six physically separate groove lanes* (no stacking).
//
// "Mirrored" here means you can wind Group B in the opposite direction / polarity,
// but the grooves are deliberately interleaved so they do not collide.
//
// Files required in same folder:
//   - rodin_lanes_points_knot512_6lanes_minor60_sink.scad
//
// Render/export:
//   - Set PART = "TOP" or "BOTTOM" or "FULL"
//   - F6 (Render) then Export STL

include <rodin_lanes_points_knot512_6lanes_minor60_sink.scad>;

// =========================
// User parameters (mm)
// =========================
PART = "FULL"; // "FULL", "TOP", "BOTTOM"

// Base torus (must match points file geometry)
R_MAJOR = 33.40;
R_TUBE  = 9.0;

// Groove sizing (edit after picking wire)
wire_d     = 1.2;
clearance  = 0.4;
groove_r   = (wire_d + clearance)/2;

// Smoothness / performance
$fn = 64; // 36 for quick preview; 96+ for final

// Clamshell alignment
peg_r = 2.0;
peg_h = 5.0;
peg_clear = 0.25;
peg_angles = [45, 135, 225, 315];
peg_rad = R_MAJOR + R_TUBE - 2.4;

// Split plane
split_z = 0;

// =========================
// Helpers
// =========================
function vsub(a,b) = [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
function vlen(v)   = norm(v);
function vcross(a,b) = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];

module cyl_between(p1, p2, r) {
    v = vsub(p2, p1);
    L = vlen(v);
    if (L > 1e-6) {
        z = [0,0,1];
        axis = vcross(z, v);
        axis_len = vlen(axis);
        ang = acos( v[2] / L ) * 180 / PI;

        translate(p1)
            if (axis_len < 1e-8) {
                if (v[2] >= 0) cylinder(h=L, r=r, center=false);
                else rotate([180,0,0]) cylinder(h=L, r=r, center=false);
            } else {
                rotate(a=ang, v=axis) cylinder(h=L, r=r, center=false);
            }
    }
}

module tube_path(path, r) {
    for (i = [0 : len(path)-2]) cyl_between(path[i], path[i+1], r);
}

module base_torus() {
    rotate_extrude(angle=360, convexity=10)
        translate([R_MAJOR, 0, 0])
            circle(r=R_TUBE);
}

module grooves() {
    union() {
        for (k = [0 : len(paths)-1]) tube_path(paths[k], groove_r);
    }
}

module grooved_torus() {
    difference() {
        base_torus();
        grooves();
    }
}

module halfspace_top() {
    intersection() {
        children();
        translate([-200,-200,split_z]) cube([400,400,400], center=false); // z>=0
    }
}
module halfspace_bottom() {
    intersection() {
        children();
        translate([-200,-200,-400]) cube([400,400,split_z+400], center=false); // z<=0
    }
}

module alignment_pegs() {
    for (a = peg_angles) {
        x = peg_rad*cos(a);
        y = peg_rad*sin(a);
        translate([x,y,split_z-0.01]) cylinder(h=peg_h, r=peg_r, center=false);
    }
}
module alignment_holes() {
    for (a = peg_angles) {
        x = peg_rad*cos(a);
        y = peg_rad*sin(a);
        translate([x,y,split_z-0.02]) cylinder(h=peg_h+0.5, r=peg_r+peg_clear, center=false);
    }
}

// =========================
// Output selector
// =========================
if (PART == "FULL") {
    grooved_torus();
}
else if (PART == "BOTTOM") {
    union() {
        halfspace_bottom() grooved_torus();
        alignment_pegs();
    }
}
else if (PART == "TOP") {
    difference() {
        halfspace_top() grooved_torus();
        alignment_holes();
    }
}