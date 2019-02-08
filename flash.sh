gdb-multiarch -q $1 <<EOF
set target-async on
set confirm off
set mem inaccessible-by-default off
tar ext /dev/blackmagic_debug
mon version
mon swdp_scan
mon swdp_scan
mon swdp_scan
att 1
load
run
EOF
