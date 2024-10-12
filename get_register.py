"""
This example attempt to retrieve the current angle from the encoder
"""

COM_PORT='COM5'

import can
import time

def send_read_request(bus):
    # Built from example at https://python-can.readthedocs.io/en/stable/
    msg = can.Message(arbitration_id=0x50,
                      data=[0x55, 0x55, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff],
                      is_extended_id=False)

    try:
        bus.send(msg)
        print(f"Message sent on {bus.channel_info}")
    except can.CanError:
        print("Error sending CAN message")

def main():
    # Built from example at https://python-can.readthedocs.io/en/v4.2.2/listeners.html
    with can.Bus(interface='slcan', channel=COM_PORT, bitrate=250000) as bus:
        print_listener = can.Printer()
        can.Notifier(bus, [print_listener])

        send_read_request(bus)

        time.sleep(0.5)


if __name__ == "__main__":
    main()
