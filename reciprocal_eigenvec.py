import os
import re
import numpy as np
import argparse
import matplotlib.pyplot as plt

def extract_kpoints_from_file(filename):
    k_points = []
    weights = []
    indices = []

    kpoint_pattern = re.compile(r'k\(\s*(\d+)\)\s*=\s*\(\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\),\s*wk\s*=\s*([-\d.]+)')
    
    in_kpoints_section = False
    
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line == "":
                if in_kpoints_section:
                    break
                continue

            if "cart. coord. in units 2pi/alat" in line:
                in_kpoints_section = True
                continue

            if in_kpoints_section:
                match = kpoint_pattern.match(line)
                if match:
                    index = int(match.group(1))
                    x = float(match.group(2))
                    y = float(match.group(3))
                    z = float(match.group(4))
                    weight = float(match.group(5))
                    
                    indices.append(index)
                    k_points.append([x, y, z])
                    weights.append(weight)

    return indices, k_points, weights

def plot_eigenvectors_2d(eigenvectors, output_file):
    num_bands, num_eigenvectors = eigenvectors.shape
    x = np.arange(num_eigenvectors)
    
    plt.figure(figsize=(10, 6))
    
    for band_idx in range(num_bands):
        plt.plot(x, np.abs(eigenvectors[band_idx, :]), label=f'Band {band_idx + 1}')
    
    plt.title('Eigenvectors in Real Space')
    plt.xlabel('Index')
    plt.ylabel('Magnitude')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

def plot_eigenvectors_argand(eigenvectors, output_file):
    num_bands, num_eigenvectors = eigenvectors.shape
    
    for band_idx in range(num_bands):
        plt.figure(figsize=(8, 8))
        plt.scatter(eigenvectors[band_idx].real, eigenvectors[band_idx].imag, c='blue', label=f'Band {band_idx + 1}')
        plt.title(f'Eigenvectors in Argand Plane (Band {band_idx + 1})')
        plt.xlabel('Real Part')
        plt.ylabel('Imaginary Part')
        plt.axhline(0, color='black', linewidth=0.5)
        plt.axvline(0, color='black', linewidth=0.5)
        plt.grid(True)
        plt.legend()
        plt.savefig(output_file.replace('.png', f'_argand_band_{band_idx + 1}.png'))
        plt.close()

def process_wfc_files(data_directory, text_output_directory, image_output_directory, k_points, weights, compute_images):
    files = [f for f in os.listdir(data_directory) if f.startswith('wfc') and f.endswith('.dat')]

    for filename in files:
        file_path = os.path.join(data_directory, filename)
        
        with open(file_path, 'rb') as f:
            f.seek(4)  # Skip initial 4 bytes
            ik = np.fromfile(f, dtype='int32', count=1)[0]
            xk = np.fromfile(f, dtype='float64', count=3)
            ispin = np.fromfile(f, dtype='int32', count=1)[0]
            gamma_only = bool(np.fromfile(f, dtype='int32', count=1)[0])
            scalef = np.fromfile(f, dtype='float64', count=1)[0]
            f.seek(8, 1)
            ngw = np.fromfile(f, dtype='int32', count=1)[0]
            igwx = np.fromfile(f, dtype='int32', count=1)[0]
            npol = np.fromfile(f, dtype='int32', count=1)[0]
            nbnd = np.fromfile(f, dtype='int32', count=1)[0]
            f.seek(8, 1)
            b1 = np.fromfile(f, dtype='float64', count=3)
            b2 = np.fromfile(f, dtype='float64', count=3)
            b3 = np.fromfile(f, dtype='float64', count=3)
            f.seek(8, 1)
            mill = np.fromfile(f, dtype='int32', count=3*igwx).reshape((igwx, 3))
            evc = np.zeros((nbnd, npol * igwx), dtype="complex128")
            f.seek(8, 1)
            for i in range(nbnd):
                evc[i, :] = np.fromfile(f, dtype='complex128', count=npol * igwx)
                f.seek(8, 1)

        # Save eigenvectors to text file
        output_file_txt = os.path.join(text_output_directory, f"{filename}_k{ik}_eigenvectors.txt")
        with open(output_file_txt, 'w') as out_file:
            out_file.write(f"{'='*60}\n")
            out_file.write(f"{'File:':<20}{filename}\n")
            out_file.write(f"{'K-point index:':<20}{ik}\n")
            out_file.write(f"{'K-point coordinates:':<20}({k_points[ik-1][0]:>10.7f}, {k_points[ik-1][1]:>10.7f}, {k_points[ik-1][2]:>10.7f})\n")
            out_file.write(f"{'K-point weight:':<20}{weights[ik-1]:>10.7f}\n")
            out_file.write(f"{'Spin index:':<20}{ispin}\n")
            out_file.write(f"{'Gamma only:':<20}{gamma_only}\n")
            out_file.write(f"{'Scaling factor:':<20}{scalef}\n")
            out_file.write(f"{'Number of G vectors:':<20}{ngw}\n")
            out_file.write(f"{'G vector indexing:':<20}{igwx}\n")
            out_file.write(f"{'Number of polarization directions:':<20}{npol}\n")
            out_file.write(f"{'Number of bands:':<20}{nbnd}\n")
            out_file.write(f"{'B-vectors:':<20}{b1}, {b2}, {b3}\n")
            out_file.write(f"{'='*60}\n\n")

            out_file.write(f"{'Miller indices':^60}\n\n")
            out_file.write(f"{'Index1':^20}{'Index2':^20}{'Index3':^20}\n")
            out_file.write(f"{'-'*60}\n")
            for miller in mill:
                out_file.write(f"{miller[0]:^20}{miller[1]:^20}{miller[2]:^20}\n")
            out_file.write(f"{'='*60}\n\n")

            out_file.write(f"{'Eigenvectors':^60}\n")
            out_file.write(f"{'-'*60}\n")
            for band_idx in range(nbnd):
                out_file.write(f"{'Band':<20}{band_idx + 1}\n\n")
                for eig_idx in range(npol * igwx):
                    out_file.write(f"{evc[band_idx, eig_idx].real:+.7e} {evc[band_idx, eig_idx].imag:+.7e}i\n")
                out_file.write(f"\n{'-'*60}\n")
            out_file.write(f"{'='*60}\n")

        # Save eigenvector plots if required
        if compute_images:
            output_file_img = os.path.join(image_output_directory, f"{filename}_k{ik}_eigenvectors.png")
            plot_eigenvectors_2d(evc, output_file_img)
            plot_eigenvectors_argand(evc, output_file_img)

            print(f"Eigenvectors for {filename} (k-point index {ik}) have been written to: {output_file_txt}")
            print(f"Plots for {filename} (k-point index {ik}) have been saved to: {output_file_img}")
        else:
            print(f"Eigenvectors for {filename} (k-point index {ik}) have been written to: {output_file_txt}")

def main():
    parser = argparse.ArgumentParser(description='Process wfc#k.dat files to extract eigenvectors and include k-point weights.')
    parser.add_argument('input_directory', type=str, help='Path to the directory containing wfc#k.dat files')
    parser.add_argument('nscf_output_file', type=str, help='Path to the nscf.out file containing k-point information')
    args = parser.parse_args()
    
    parent_directory = os.path.join(os.getcwd(), 'ReciprocalLattice')
    text_output_directory = os.path.join(parent_directory, 'ReciprocalLatticeText')
    image_output_directory = os.path.join(parent_directory, 'ReciprocalLatticeImages')
    
    os.makedirs(text_output_directory, exist_ok=True)
    os.makedirs(image_output_directory, exist_ok=True)

    indices, k_points, weights = extract_kpoints_from_file(args.nscf_output_file)

    while True:
        print("Choose an option:")
        print("1. Compute and store only text files")
        print("2. Compute and store text files and images")
        print("3. Exit")

        choice = input("Enter your choice (1/2/3): ")

        if choice == '1':
            process_wfc_files(args.input_directory, text_output_directory, None, k_points, weights, False)
        elif choice == '2':
            process_wfc_files(args.input_directory, text_output_directory, image_output_directory, k_points, weights, True)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()

