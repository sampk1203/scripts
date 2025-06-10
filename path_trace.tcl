# Cell dimensions
set a 12.9827
set b 12.9827
set c 12.9827

# Get total number of frames
set nframes [molinfo top get numframes]

# Select all atoms of type 1
set atoms [atomselect top "type 1"]
set indices [$atoms get index]
$atoms delete

# Loop over all atom indices of type 1
foreach targetIndex $indices {
    set outfile [open "Li10_frac_coords_atom${targetIndex}.xyz" w]
    puts $outfile "# Frame  x_frac  y_frac  z_frac"

    for {set i 0} {$i < $nframes} {incr i} {
        set target [atomselect top "index $targetIndex" frame $i]

        if {[$target num] > 0} {
            set coord [$target get {x y z}]
            set x [lindex $coord 0 0]
            set y [lindex $coord 0 1]
            set z [lindex $coord 0 2]

            set fx [expr {double($x) / $a}]
            set fy [expr {double($y) / $b}]
            set fz [expr {double($z) / $c}]

            puts $outfile "$i $fx $fy $fz"
        } else {
            puts $outfile "$i NaN NaN NaN"
        }

        $target delete
    }

    close $outfile
    puts "Wrote fractional trajectory to Li_frac_coords_atom${targetIndex}.xyz"
}

