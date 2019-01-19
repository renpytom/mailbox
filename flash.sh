gdb-multiarch -q $1 <<EOF
set target-async on
set confirm off
set mem inaccessible-by-default off
tar ext /dev/ttyACM2
mon version
mon swdp_scan
att 1
load
run
EOF
