

import argparse
from pymatgen.core import Structure
from pymatgen.io.cif import CifWriter

def generate_supercell(input_cif, output_cif, scale_matrix):
    """
    Generates a supercell from a CIF file.

    Parameters:
        input_cif (str): Path to input CIF file.
        output_cif (str): Path to save the generated supercell CIF.
        scale_matrix (list of list of int): 3x3 scaling matrix for supercell.
    """
    # Load the structure from CIF
    structure = Structure.from_file(input_cif)
    
    # Create the supercell
    structure.make_supercell(scale_matrix)
    
    # Write to output CIF
    writer = CifWriter(structure)
    writer.write_file(output_cif)
    print(f"Supercell written to {output_cif}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a supercell from a CIF file using pymatgen.",
        epilog="Example: python generate_supercell.py input.cif output.cif 2 2 2"
    )
    parser.add_argument("input_cif", type=str, help="Path to the input CIF file")
    parser.add_argument("output_cif", type=str, help="Path to save the output supercell CIF file")
    parser.add_argument(
        "scale", type=int, nargs=3,
        help="Scaling factors along a, b, c axes (e.g., 2 2 2 for doubling each axis)"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Convert the scale factors into a diagonal 3x3 matrix
    scale_matrix = [[args.scale[0], 0, 0],
                    [0, args.scale[1], 0],
                    [0, 0, args.scale[2]]]
    
    generate_supercell(args.input_cif, args.output_cif, scale_matrix)
