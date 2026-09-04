Triple gear package generated from the uploaded STL source.

Files
- triple_gear_from_uploaded_source_centered.stl : watertight assembly, centered at origin
- triple_gear_from_uploaded_source_centered.obj : same geometry as OBJ
- triple_gear_from_uploaded_source_centered.glb : same geometry as GLB
- triple_gear_part_1/2/3.(stl|obj|glb) : the three linked gear bodies as separate meshes, preserving assembly placement
- import_triple_gear_into_blender.py : Blender helper script to import STL and separate loose parts
- triple_gear_from_uploaded_source_metadata.json : mesh statistics

Notes
- Source mesh: triple_gear_solid_with_mark.stl
- Source is watertight: True
- Assembly consists of 3 connected watertight bodies.
- Overall extents are approximately 69.912 x 74.119 x 45.402 in the STL's native units.
- In most slicers/STL workflows these units are interpreted as millimeters.
- I did not remove the maker's mark/logo from this package.
- The axle and baseplate shown in the photos were not reconstructed from the images alone.