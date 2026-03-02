#!/usr/bin/env bash
set -e

CAN_DEVICE_NAME=${1:-"can1"}

echo "Usage: $0 [CAN_DEVICE_NAME]"
echo 'Please ensure the following package is installed:
   can-utils'

echo 'We will do the following actions:
- Delete the network named `'$CAN_DEVICE_NAME'`.'

echo 'Note: You will have to unplug and replug in the USB device to create a new CAN device.'

echo "Proceed? [Enter / Ctrl-C]"
read

set -x
sudo ip link delete $CAN_DEVICE_NAME
