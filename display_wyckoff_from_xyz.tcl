# Load the Wyckoff sites in Cartesian coordinates
mol new wyckoff_sites_cartesian.xyz type xyz

# Set very small spheres for both atom types
# 24d (X)
mol selection {name X}
mol representation VDW 0.1 5.0
mol color ColorID 0  ;# Blue
mol addrep top

# 96h (Y)
mol selection {name Y}
mol representation VDW 0.1 5.0
mol color ColorID 3  ;# Green
mol addrep top

# Optional: adjust voxel display (isosurface)
mol modstyle 0 0 Isosurface 0.5 0 0 0 1 1
mol modcolor 0 0 ColorID 7 ;# Grey

# Set and display the correct unit cell
pbc set {12.97 12.97 12.97 90 90 90}
pbc box
