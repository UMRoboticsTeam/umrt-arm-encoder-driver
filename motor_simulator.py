import can
import time

COMMAND_ENABLE_MOTOR = 0xF3
COMMAND_MOTOR_SPEED = 0xF6


def create_message(motor_id: int, data: List[int]) -> can.Message:
    checksum = motor_id + sum(data)
    checksum_modFF = checksum % 0x100
    # print(f"{checksum = :x}")
    # print(f"{checksum_modFF = :x}")
    data_with_checksum = data + [checksum_modFF]
    print("Sending:", " ".join([f"{i:02x}" for i in data_with_checksum]))
    return can.Message(arbitration_id=motor_id, data=data_with_checksum, is_extended_id=False)


def create_enable_motor_message(motor_id: int, enable: bool) -> can.Message:
    data = [COMMAND_ENABLE_MOTOR, int(enable)]
    return create_message(motor_id, data)


def create_stop_motor_message(motor_id: int, acc: int) -> can.Message:
    return create_set_motor_speed_message(motor_id, False, 0, acc)


def create_set_motor_speed_message(motor_id: int, clockwise: bool, speed: int, acc: int) -> can.Message:
    byte2 = (int(clockwise) << 7) | (speed & 0xF00 >> 8)
    byte3 = speed & 0xFF
    byte4 = acc
    print(f"{byte2=:x}")
    print(f"{byte3=:x}")
    print(f"{byte4=:x}")
    data = [COMMAND_MOTOR_SPEED, byte2, byte3, byte4]
    return create_message(motor_id, data)


# The purpose of this program is to mimick a motor
# and respond as if it were one.
# It should read the CAN messages and ignore irelevent ones (they might about the encoders)
# and respond as the manual says, or test the motor to see what it does.
# The program should read from the CAN bus and send to the same CAN bus, so that
# we can test it with a real motor to compare.
def main(interface, channel, bitrate):
    motor_id = 3

    # Get the address
    with can.Bus(interface=interface, channel=channel, bitrate=bitrate) as bus:
        bus.send(create_stop_motor_message(motor_id, 2))

        while True:
            print(bus.recv(10000))


if __name__ == "__main__":
    # Define bus connection here:
    interface = "socketcan"
    channel = "can1"
    bitrate = 500_000

    main(interface, channel, bitrate)
