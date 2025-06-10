# Scripts

A collection of scripts in various programming languages for different purposes.

---

## Scripts

### 1. `mccabethiele.py`

- **Requirements:** PyQt5, numpy, matplotlib
  
- **Usage:** `python mccabethiele.py`
  
- **Description:**
  
  Performs McCabe-Thiele method analysis based on user inputs through a graphical interface.
  
- **Note:**
  
  Results may be inaccurate under extreme or edge-case input conditions. Use with caution.

### 2. `reciprocal_eigenvec.py`

- **Requirements:**  numpy, matplotlib
  
- **Usage:** `python reciprocal_eigenvec.py input_directory nscf_output_file`
  
- **Description:**

   Extracts eigenvectors from the output directory of a Quantum ESPRESSO calculation, with an option to plot them. The eigenvectors are represented in reciprocal space.

### 3. `DOS from file.sh`
    
- **Description:**

   Computes DOS for all gaussian output files in current directory using Gaussum.

### 4. `Energy_HOLO_LUMO_Fermi.sh`

  
- **Description:**

   Extracts SCF energy, HOMO and LUMO energies from all gaussian output files in the same directory.

### 5. `cif2lmpdat.py`

  
- **Description:**

   Uses `ase` to convert cif files to lmpdat files for usage in LAMMPS

### 6. `DOS@energy.py`

- **Requirements:**  numpy, matplotlib
  
- **Usage:** `python DOS@energy.py <arg1> <arg2>`
  
- **Description:**

   Extracts the DOS at a given value of energy.
  
   The first argument is a text file with the DOS filenames(extracted using Gausssum)
  
   The second argument is a text file with the corresponding values of energies where the DOS is to be found.

### 7. `voxel2density.py`&`density2free_energy.py`&`energy2energy_diff.py`

- **Requirements:**  numpy, matplotlib, pandas, csv
  
- **Usage:**

             python voxel2density.py voxel_file.dx
  
             python density2free_energy.py density_fractional.csv
  
             python energy2energy_diff density_with_free_energy.csv -n1 x1,y1,z1 -n2 x2,y2,z2
  
- **Description:**

   voxel2density.py - Converts a voxel file from VMD to a csv file with fractional coordinates of the cell with atom density.
  
   density2free_energy.py - Estimates the free energy at each point in the grid.
  
   energy2energy_diff.py - Calculates the free energy difference between any 2 given points using interpolation.

### 8. `get_diff.py`

  
- **Description:**

   Fits the MSD data to get diffusion coefficient between 2 given time stamps
### 9. `match_position_to_wyckoff.py`

- **Requirements:** numpy, pandas, matplotlib, scipy, pymatgen
  
- **Usage:** `python match_position_to_wyckoff.py csv_file xyz_dir (--window/--tol/--show-raw/--raw-only)`
  
- **Description:**
  
  Matches the position of all xyz trajectory files from a given input directory to the respective positional free energies, plots them.Smoothing window (--window),tolerance for matching (--tol),and type of plot(--show-raw / --raw-only) can be specified.
  
- **Note:**
  
  Specify the space group and the initial starting positions to generate all wyckoff positions.

### 10. `pathtrace.tcl`

- **Requirements:** VMD
  
- **Usage:** `use in tkconsole`
  
- **Description:**
  
  Writes the xyz file for every frame of the trajectory in the given file, for the given type of atom. Cell parameters and atom type need to be specified in the code before use.
  
