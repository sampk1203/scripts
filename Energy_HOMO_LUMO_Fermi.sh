#!/bin/bash

# Get the current directory
current_dir=$(dirname "$0")

# Output file
output_file="$current_dir/output.txt"

# Initialize variables to store concatenated data and average
all_data=""
all_data2=""
all=""
average=""

# Loop through all files with .log or .out extensions in the current directory
for filename in $(ls "$current_dir"/*.log "$current_dir"/*.out | sort); do
    # Check if the file exists and is a regular file
    if [ -f "$filename" ]; then
        echo "Processing file: $filename"

        # Run the awk commands to extract the values
        value1=$(awk '/SCF Done/ {print $5}' "$filename")
        value2=$(awk '/Alpha  occ. eigenvalues --/ {print $NF}' "$filename" | tail -1)
        value3=$(awk '/Alpha virt. eigenvalues --/ {print $5}' "$filename" | head -1)

        # Calculate the average of the second and third data
        average=$(awk "BEGIN {print ($value2 + $value3) / 2}")
		

        # Append extracted values and average to the all_data variable
        all_data+="$filename: $value1 "
        all_data+="$value2 "
        all_data+="$value3 "
        all_data+="$average\n"

        all_data2+="$value1 "
        all_data2+="$value2 "
        all_data2+="$value3 "
        all_data2+="$average\n"

        all="$all_data\n\n$all_data2"
    fi
done

# Write all data to the output file
echo -e "$all" > "$output_file"

echo "Data from all input files in '$current_dir' with .log or .out extension has been written to '$output_file'."
