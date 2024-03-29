#!/bin/sh

# wlNoiseFloor.sh
# Returns wlNoiseFloor, in dBm
# Arguments: targed interface

# Check number of arguments
if [ $# -ne 1 ]; then
	/bin/echo "Usage: wlNoiseFloor.sh interface"
	/bin/echo "Missing targeted interface, exiting."
	exit 1
fi

# Extract noise floor. Note, all associated stations have the same value, so just grab the first one
# Use tail, not head (i.e. last line, not first), as head exits immediately, breaks the pipe to cut!
noise=$(/usr/bin/iwinfo "$1" assoclist | grep -Eo "\(SNR [-0-9]+\)" | grep -Eo "[-0-9]+" | head -n 1)

# Return snmp result
/bin/echo "$noise"
