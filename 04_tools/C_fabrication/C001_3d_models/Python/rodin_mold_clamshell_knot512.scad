// rodin_mold_clamshell_knot512.scad
// "Better mold" OpenSCAD: real grooves via CSG subtraction of swept tubes.
// Produces a clamshell: TOP and BOTTOM halves with alignment pegs.
//
// Usage:
// 1) Put this file + "rodin_lanes_points_knot512.scad" in same folder.
// 2) Open in OpenSCAD.
// 3) Preview (F5). Render (F6). Export STL.
// 4) Switch PART = "TOP" / "BOTTOM" / "FULL" at the top.
//
// Notes:
// - For speed: lower PATH_SEGMENTS and $fn during preview.
// - For quality: increase them for final render.
//
// Author: generated for Omar

include <rodin_lanes_points_knot512.scad>;

// =========================
// User parameters (mm)
// =========================
PART = "FULL"; // "FULL", "TOP", "BOTTOM"

// Torus geometry (must match points file)
R_MAJOR = 33.40;
R_TUBE  = 9.0;

// Channel (groove) sizing
wire_d     = 1.2;   // wire diameter you plan to use
clearance  = 0.4;   // printer tolerance
groove_r   = (wire_d + clearance)/2;

// Groove smoothness
PATH_SEGMENTS = 260;  // must match point count in points file (or slightly less)
$fn = 72;             // global smoothness (increase for final)

// Clamshell alignment
peg_r = 2.0;
peg_h = 5.0;
peg_clear = 0.25;     // clearance on holes
peg_angles = [45, 135, 225, 315];
peg_rad = R_MAJOR + R_TUBE - 2.4; // keep pegs on outer "shoulder"

// Split plane
split_z = 0;

// =========================
// Helpers
// =========================
function vsub(a,b) = [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
function vlen(v)   = norm(v);
function vdot(a,b) = a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
function vcross(a,b) = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];

// Cylinder between two 3D points (robust axis-angle)
module cyl_between(p1, p2, r) {
    v = vsub(p2, p1);
    L = vlen(v);
    if (L > 1e-6) {
        // align +Z with v
        z = [0,0,1];
        axis = vcross(z, v);
        axis_len = vlen(axis);
        ang = acos( v[2] / L ) * 180 / PI;

        translate(p1)
            if (axis_len < 1e-8) {
                // v parallel to z axis
                if (v[2] >= 0)
                    cylinder(h=L, r=r, center=false);
                else
                    rotate([180,0,0]) cylinder(h=L, r=r, center=false);
            } else {
                rotate(a=ang, v=axis)
                    cylinder(h=L, r=r, center=false);
            }
    }
}

// Tube along a polyline path as union of cylinders
module tube_path(path, r) {
    for (i = [0 : len(path)-2]) {
        cyl_between(path[i], path[i+1], r);
    }
}

// Base torus (solid) via rotate_extrude
module base_torus() {
    rotate_extrude(angle=360, convexity=10)
        translate([R_MAJOR, 0, 0])
            circle(r=R_TUBE);
}

// All grooves (cutters)
module grooves() {
    union() {
        for (k = [0 : len(paths)-1]) {
            tube_path(paths[k], groove_r);
        }
    }
}

// Full grooved torus
module grooved_torus() {
    difference() {
        base_torus();
        grooves();
    }
}

// Halfspace intersection
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

// Alignment pegs (bottom)
module alignment_pegs() {
    for (a = peg_angles) {
        x = peg_rad*cos(a);
        y = peg_rad*sin(a);
        translate([x,y,split_z-0.01]) cylinder(h=peg_h, r=peg_r, center=false);
    }
}

// Alignment holes (top)
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