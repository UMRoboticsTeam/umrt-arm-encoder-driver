#!/usr/bin/env bash
set -e

CAN_DEVICE_NAME=${1:-"can1"}
USB_DEVICE=${2:-"/dev/ttyACM0"}

echo "Usage: $0 [CAN_DEVICE_NAME] [USB_DEVICE]"
echo ''
echo 'Please ensure the following package is installed:
   can-utils'
echo ""

echo 'We will do the following actions
- Create a network device at 250K baud named `'$CAN_DEVICE_NAME'` linked to `'$USB_DEVICE'`.
- Enable the network device.'

echo "Proceed? [Enter / Ctrl-C]"
read
set -x

sudo slcand -f -o -c -s5 $USB_DEVICE $CAN_DEVICE_NAME
sudo ip link set up $CAN_DEVICE_NAME
ip link show $CAN_DEVICE_NAME

set +x
echo "Now to test, view the messages on the can bus in one terminal"

echo '    $ candump '$CAN_DEVICE_NAME
echo "and send a raw message to the can bus in a separate terminal"
echo '    $ cansend '$CAN_DEVICE_NAME' '"'"'123#1233'"'"''
