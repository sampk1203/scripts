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

---
