import numpy as np
import matplotlib.pyplot as plt

def DOS_extraction(input_filename_list, x_values_file):
    # Check if input filenames and x_values_file are provided
    if not input_filename_list or not x_values_file:
        print('Usage: output_data = DOS_extraction(input_filename_list, x_values_file)')
        return
    
    # Check if x_values_file exists
    try:
        x_values = np.loadtxt(x_values_file) * 27.2114
    except OSError:
        print(f'Error: X values file {x_values_file} does not exist.')
        return
    
    # Read input filenames
    try:
        with open(input_filename_list, 'r') as f:
            input_filenames = f.read().splitlines()
    except OSError:
        print(f'Error: Unable to open input filename list {input_filename_list}.')
        return
    
    # Determine the number of subplots and rows needed
    num_subplots = len(input_filenames)
    num_rows = (num_subplots + 2) // 3  # 3 columns per row
    
    # Set up figure size
    screen_size = plt.get_current_fig_manager().canvas.get_width_height()
    fig_width = screen_size[0] // 3  # Each subplot should occupy a third of the screen width
    fig_height = screen_size[1] // (4 * num_rows)  # Each subplot should occupy a quarter of the screen height
    
    # Initialize output_data list to store x, y, and filename
    output_data = []
    
    # Set figure size
    fig, axes = plt.subplots(num_rows, 3, figsize=(fig_width / 100, fig_height / 100))
    axes = axes.flatten()  # Flatten axes to make it easier to index
    
    # Iterate over input filenames and process each file
    for k, input_filename in enumerate(input_filenames):
        # Check if file exists
        try:
            data = np.loadtxt(input_filename, skiprows=2, max_rows=1000)
        except OSError:
            print(f'Error: Input file {input_filename} does not exist or cannot be opened.')
            continue
        
        # Transpose the data array to split it into two separate arrays
        x, y = data[:, 0], data[:, 1]
        
        # Get the x value from the x_values_file
        x_value = x_values[k]
        
        # Find the corresponding y value
        y_value = y[np.where(x >= x_value)[0][0]]
        
        # Store x, y, and filename in output_data
        output_data.append((x_value, y_value, input_filename))
        
        # Plot x and y values with drop lines and point
        ax = axes[k]
        ax.plot(x, y)
        ax.axvline(x=x_value, color='r', linestyle='--')
        ax.axhline(y=y_value, color='r', linestyle='--')
        ax.plot(x_value, y_value, 'ro')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title(f'Plot of {input_filename}', fontsize=10)
    
    # Adjust layout
    plt.tight_layout()
    plt.show()
    
    return output_data

# Usage example
# output_data = DOS_extraction('input_file_list.txt', 'x_values_file.txt')

