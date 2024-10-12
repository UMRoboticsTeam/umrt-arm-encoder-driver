
"""
Shows how to receive messages via polling.
"""

import can
from can.bus import BusState


def dump_all():
    """Receives all messages and prints them to the console until Ctrl+C is pressed."""

    # this uses the default configuration (for example from environment variables, or a
    # config file) see https://python-can.readthedocs.io/en/stable/configuration.html
    with can.Bus(interface='slcan', channel='COM5', bitrate=250000) as bus:
        # set to read-only, only supported on some interfaces
        try:
            bus.state = BusState.PASSIVE
        except NotImplementedError:
            pass

        try:
            while True:
                msg = bus.recv(1)
                if msg is not None and len(msg.data) >= 2:
                    if msg.data[0] == 0x55 and msg.data[1] == 0x55:
                        print(msg)

        except KeyboardInterrupt:
            pass  # exit normally

def dump_delta():
    """Receives all messages and prints the difference from the last to the console until Ctrl+C is pressed."""

    # this uses the default configuration (for example from environment variables, or a
    # config file) see https://python-can.readthedocs.io/en/stable/configuration.html
    with can.Bus(interface='slcan', channel='COM5', bitrate=250000) as bus:
        # set to read-only, only supported on some interfaces
        try:
            bus.state = BusState.PASSIVE
        except NotImplementedError:
            pass

        try:
            last_msg = bytearray([0x55, 0x55, 0x3c, 0x00, 0x00, 0x00, 0xf2, 0xff])
            while True:
                msg = bus.recv(1)
                if msg is not None and len(msg.data) == 8:
                    if msg.data[0] == 0x55 and msg.data[1] == 0x55:
                        output_msg = []
                        for i in range(2, 4):
                            output_msg.append(msg.data[i] - last_msg[i])
                        last_msg = msg.data
                        print(output_msg)

        except KeyboardInterrupt:
            pass  # exit normally

def dump_just_angle():
    """Receives all messages and prints the angle portion of each message to the console until Ctrl+C is pressed."""

    # this uses the default configuration (for example from environment variables, or a
    # config file) see https://python-can.readthedocs.io/en/stable/configuration.html
    with can.Bus(interface='slcan', channel='COM5', bitrate=250000) as bus:
        # set to read-only, only supported on some interfaces
        try:
            bus.state = BusState.PASSIVE
        except NotImplementedError:
            pass

        try:
            last_msg = bytearray([0x55, 0x55, 0x3c, 0x00, 0x00, 0x00, 0xf2, 0xff])
            while True:
                msg = bus.recv(1)
                if msg is not None and len(msg.data) == 8:
                    if msg.data[0] == 0x55 and msg.data[1] == 0x55:
                        # From translated manual:
                        # Take the encoder reply "55 55 aa bb cc dd ee ff" data as an example to calculate
                        # Angle calculation method: Angle register value = (0xbb << 8) | 0xaa
                        #                           Angle (°) = Angle register value * 360 / 32768
                        angle_register = msg.data[3] << 8 | msg.data[2]
                        angle = angle_register * 360 / 32768

                        # From translated manual:
                        # Angular velocity (°/s) = angular velocity register value * 360 / 32768
                        #                          / angular velocity sampling time (s)
                        # Note: The above angular velocity sampling time is calculated in seconds, the default is 0.1s
                        #
                        # The manual does not state how to calculate the angular velocity register value, but since
                        # the angle register uses 'aa bb', and the number of revolutions uses 'ee ff', the angular
                        # velocity presumably comes from 'cc dd'
                        angular_velocity_register = msg.data[5] << 8 | msg.data[4]
                        angular_velocity = angular_velocity_register * 360 / 32768 / 0.1

                        # From translated manual:
                        # Number of revolutions = (0xff << 8) | 0xee
                        number_of_rotations = int.from_bytes([msg.data[6], msg.data[7]], byteorder='little', signed=True)

                        print(f"{angle_register:<5} = {angle:<15}°\t\t"
                              f"{angular_velocity_register:<5} = {angular_velocity:.2f} °/s\t\t"
                              f"{number_of_rotations} rotations")

        except KeyboardInterrupt:
            pass  # exit normally


if __name__ == "__main__":
    dump_just_angle()