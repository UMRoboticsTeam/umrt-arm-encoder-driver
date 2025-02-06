"""
This example attempt to retrieve the current angle from the encoder
"""
import string

COM_PORT = '/dev/ttyACM0'
DEVICE_ADDR = 0x50

import can
import time
from enum import IntEnum


class Register(IntEnum):
    APPLY_SETTINGS = 0x00
    # Allows the encoder settings to be persisted
    # Values:
    #   0x00: Save the current settings
    #   0x01: Reset to factory settings
    #   0xFF: Restart the encoder
    # Restarting is useful because it allows you to exit unlocked mode and apply saved settings

    CONTENT_MODE = 0x02
    # What content (angular info/temp) to automatically publish
    # Values:
    #   0x01: Publish the current angle, angular velocity, and number of revolutions
    #   0x02: Publish the temperature
    #   0x03: Publish the current angle, angular velocity, number of revolutions, and temperature
    # Defaults to publish both = 0x03

    RETURN_RATE = 0x03
    # What rate the encoder automatically publishes the content at
    # Values:
    #   0x00: 0.1 Hz
    #   0x01: 0.2 Hz
    #   0x02: 0.5 Hz
    #   0x03: 1 Hz
    #   0x04: 2 Hz
    #   0x05: 5 Hz
    #   0x06: 10 Hz
    #   0x07: 20 Hz
    #   0x08: 50 Hz
    #   0x09: 100 Hz
    #   0x0A: 125 Hz
    #   0x0B: 200 Hz
    #   0x0C: 1000 Hz
    #   0x0D: 2000 Hz
    #   0x0E: Single Return
    # Defaults to 10 Hz = 0x06

    BAUD_RATE = 0x04
    # What baud rate to use for the CAN bus
    # Values:
    #   0x00: 1000 K
    #   0x01: 800 K
    #   0x02: 500 K
    #   0x03: 400 K
    #   0x04: 250 K
    #   0x05: 200 K
    #   0x06: 125 K
    #   0x07: 100 K
    #   0x08: 80 K
    #   0x09: 50 K
    #   0x0A: 40 K
    #   0x0B: 20 K
    #   0x0C: 10 K
    #   0x0D: 5 K
    #   0x0E: 3 K
    # Defaults to 250 K = 0x04

    ENCODER_MODE = 0x10
    # Whether the encoder is in single-turn or multi-turn mode
    # Values:
    #   0x00: Single turn
    #   0x01: Multi turn
    # Defaults to multi-turn = 0x01

    ANG_VAL = 0x11
    # The current angle of the encoder
    # Follows the formula: Angle [°] = ANGLE_REG * 360 / 32768
    # Therefore, to set the current angle to 30°, ANGLE_REG = (30°) * 32768 / 360 = 2730 should be written

    REVOLUTIONS = 0x12
    # The current number of revolutions which have occurred
    # Signed 16-bit integer

    ANGULAR_VEL = 0x13
    # The current angular velocity
    # Formula: Angular velocity [°/s] = ANGULAR_VEL_REG * 360 / 32768 / (Angular velocity sampling time [s])
    # Signed 16-bit integer

    TEMPERATURE = 0x14
    # The current temperature
    # Follows the formula: Temperature [°C] = TEMPERATURE_REG / 100
    # 16-bit integer, presumably signed

    SPIN_DIR = 0x15
    # Whether CW or CCW is considered the positive rotation
    # Values:
    #   0x00: Clockwise when viewed from the base is positive
    #   0x01: Counterclockwise when viewed from the base is positive
    # Defaults to clockwise = 0x00

    ANGULAR_VEL_SAMPLE_PERIOD = 0x17
    # The amount of time to wait between angular velocity samples when internally calculating
    # The angular velocity is calculated by a running sum, so if the sample rate is too high the register can overflow
    # Follows the formula: Sample time [s] = SAMPLE_TIME_REG * 100 μs
    # 16-bit integer, presumably unsigned ("The minimum register value is 1" in manual)
    # Defaults to 100 ms = 1000

    READ_REGISTER = 0x27
    # The manual lists this as a register address, but I believe it is actually just a command

    DEVICE_ADDR = 0x1A
    # The address this encoder uses on the CAN bus
    # 11-bit unsigned integer
    # Defaults to 0x50

    VERSION_NUM_L = 0x2E
    # Appears to be the low word of the version number

    VERSION_NUM_H = 0x2F
    # Appears to be the high word of the version number


def send_read_request(bus, register: Register):
    # Built from example at https://python-can.readthedocs.io/en/stable/
    msg = can.Message(arbitration_id=DEVICE_ADDR,
                      data=[0xFF, 0xAA, 0x27, register, 0x00],
                      is_extended_id=False)

    try:
        bus.send(msg)
    except can.CanError:
        print("Error sending CAN message")


def send_write_request(bus, register: Register, payload, unlock=True):
    assert (len(payload) == 2)

    # Send unlock command then message
    unlock_msg = can.Message(arbitration_id=DEVICE_ADDR,
                             data=[0xFF, 0xAA, 0x69, 0x88, 0xB5],
                             is_extended_id=False)

    msg = can.Message(arbitration_id=DEVICE_ADDR,
                      data=[0xFF, 0xAA, register, payload[0], payload[1]],
                      is_extended_id=False)

    try:
        if unlock: bus.send(unlock_msg)
        bus.send(msg)
    except can.CanError:
        print("Error sending CAN message")


def send_read_and_wait(bus, register: Register, timeout=1, retries=0):
    send_read_request(bus, register)

    for _ in range(retries + 1):
        try:
            abort_time = time.time() + timeout
            while time.time() < abort_time:
                msg = bus.recv(1)
                if msg is not None and len(msg.data) == 8:
                    if msg.data[0] == 0x55 and msg.data[1] == 0x5F:
                        return msg
        except KeyboardInterrupt:
            return None
    return None


def get_apply_settings_register(bus):
    settings_register = None
    msg = send_read_and_wait(bus, Register.APPLY_SETTINGS)
    if msg is not None:
        settings_register = list(msg.data)
    return settings_register


# Eligible modes: 'save', 'factory_reset', 'restart'
def apply_settings(bus, mode, unlock=True):
    payload = [0x00, 0x00]
    match mode:
        case 'save':
            payload[0] = 0x00
        case 'factory_reset':
            payload[0] = 0x01
        case 'restart':
            payload[0] = 0xFF
        case _:
            raise ValueError('Invalid apply settings mode provided')
    send_write_request(bus, Register.APPLY_SETTINGS, payload, unlock)


def get_content_mode(bus):
    content_mode = None
    msg = send_read_and_wait(bus, Register.CONTENT_MODE)
    if msg is not None:
        match msg.data[2]:
            case 0x01:
                content_mode = 'angles'
            case 0x02:
                content_mode = 'temperature'
            case 0x03:
                content_mode = 'both'
    return content_mode


def set_content_mode(bus, content_mode, unlock=True):
    payload = [0x00, 0x00]
    match content_mode:
        case 'angles':
            payload[0] = 0x01
        case 'temperature':
            payload[0] = 0x02
        case 'both':
            payload[0] = 0x03
        case _:
            raise ValueError('Invalid content mode provided')
    send_write_request(bus, Register.CONTENT_MODE, payload, unlock)


def get_return_rate(bus):
    return_rate = None
    msg = send_read_and_wait(bus, Register.RETURN_RATE)
    if msg is not None:
        match msg.data[2]:
            case 0x00:
                return_rate = 0.1
            case 0x01:
                return_rate = 0.2
            case 0x02:
                return_rate = 0.5
            case 0x03:
                return_rate = 1
            case 0x04:
                return_rate = 2
            case 0x05:
                return_rate = 5
            case 0x06:
                return_rate = 10
            case 0x07:
                return_rate = 20
            case 0x08:
                return_rate = 50
            case 0x09:
                return_rate = 100
            case 0x0A:
                return_rate = 125
            case 0x0B:
                return_rate = 200
            case 0x0C:
                return_rate = 1000
            case 0x0D:
                return_rate = 2000
            case 0x0E:
                return_rate = 'single_return'
    return return_rate


def set_return_rate(bus, return_rate, unlock=True):
    # Note to anyone who has to maintain these switches, regex is your friend:
    # Find: "case (0x..):\s*\r\n(\s+)return (.*)$"
    # Replace: "case $3:\r\n$2payload[0] = $1"
    payload = [0x00, 0x00]
    match return_rate:
        case 0.1:
            payload[0] = 0x00
        case 0.2:
            payload[0] = 0x01
        case 0.5:
            payload[0] = 0x02
        case 1:
            payload[0] = 0x03
        case 2:
            payload[0] = 0x04
        case 5:
            payload[0] = 0x05
        case 10:
            payload[0] = 0x06
        case 20:
            payload[0] = 0x07
        case 50:
            payload[0] = 0x08
        case 100:
            payload[0] = 0x09
        case 125:
            payload[0] = 0x0A
        case 200:
            payload[0] = 0x0B
        case 1000:
            payload[0] = 0x0C
        case 2000:
            payload[0] = 0x0D
        case 'single_return':
            payload[0] = 0x0E
        case _:
            raise ValueError('Invalid rate provided')
    send_write_request(bus, Register.RETURN_RATE, payload, unlock)


def get_baud_rate(bus):
    baud_rate = None
    msg = send_read_and_wait(bus, Register.BAUD_RATE)
    if msg is not None:
        match msg.data[2]:
            case 0x00:
                baud_rate = 1000
            case 0x01:
                baud_rate = 800
            case 0x02:
                baud_rate = 500
            case 0x03:
                baud_rate = 400
            case 0x04:
                baud_rate = 250
            case 0x05:
                baud_rate = 200
            case 0x06:
                baud_rate = 125
            case 0x07:
                baud_rate = 100
            case 0x08:
                baud_rate = 80
            case 0x09:
                baud_rate = 50
            case 0x0A:
                baud_rate = 40
            case 0x0B:
                baud_rate = 20
            case 0x0C:
                baud_rate = 10
            case 0x0D:
                baud_rate = 5
            case 0x0E:
                baud_rate = 3
    return baud_rate


def set_baud_rate(bus, baud_rate, unlock=True):
    payload = [0x00, 0x00]
    match baud_rate:
        case 1000:
            payload[0] = 0x00
        case 800:
            payload[0] = 0x01
        case 500:
            payload[0] = 0x02
        case 400:
            payload[0] = 0x03
        case 250:
            payload[0] = 0x04
        case 200:
            payload[0] = 0x05
        case 125:
            payload[0] = 0x06
        case 100:
            payload[0] = 0x07
        case 80:
            payload[0] = 0x08
        case 50:
            payload[0] = 0x09
        case 40:
            payload[0] = 0x0A
        case 20:
            payload[0] = 0x0B
        case 10:
            payload[0] = 0x0C
        case 5:
            payload[0] = 0x0D
        case 3:
            payload[0] = 0x0E
        case _:
            raise ValueError('Invalid baud rate provided')
    send_write_request(bus, Register.BAUD_RATE, payload, unlock)


def get_encoder_mode(bus):
    encoder_mode = None
    msg = send_read_and_wait(bus, Register.ENCODER_MODE)
    if msg is not None:
        match msg.data[2]:
            case 0x00:
                encoder_mode = 'single'
            case 0x01:
                encoder_mode = 'multi'
    return encoder_mode


def set_encoder_mode(bus, mode, unlock=True):
    payload = [0x00, 0x00]
    match mode:
        case 'single':
            payload[0] = 0x00
        case 'multi':
            payload[0] = 0x01
        case _:
            raise ValueError('Invalid encoder mode provided')
    send_write_request(bus, Register.ENCODER_MODE, payload, unlock)


# Returns the angle register value, to convert to degrees perform get_ang_val(bus) * 360 / 32768
def get_ang_val(bus):
    angle_register = None
    msg = send_read_and_wait(bus, Register.ANG_VAL)
    if msg is not None:
        angle_register = int.from_bytes([msg.data[2], msg.data[3]], byteorder='little', signed=False)
    return angle_register


def set_ang_val(bus, angle_register_value, unlock=True):
    if angle_register_value < 0 or angle_register_value >= 2e15: raise ValueError('Invalid angle value provided')
    payload = int.to_bytes(angle_register_value, 2, byteorder='little', signed=False)
    send_write_request(bus, Register.ANG_VAL, payload, unlock)


def get_revolutions(bus):
    num_revolutions = None
    msg = send_read_and_wait(bus, Register.REVOLUTIONS)
    if msg is not None:
        num_revolutions = int.from_bytes([msg.data[2], msg.data[3]], byteorder='little', signed=True)
    return num_revolutions


def set_revolutions(bus, revolutions, unlock=True):
    if revolutions < -2e15 or revolutions >= 2e15: raise ValueError('Invalid number of revolutions provided')
    payload = int.to_bytes(revolutions, 2, byteorder='little', signed=True)
    send_write_request(bus, Register.REVOLUTIONS, payload, unlock)


# Returns the angular velocity register value, to convert to degrees/s perform
#   get_angular_vel(bus) * 360 / 32768 / get_angular_vel_sample_period(bus) / 10e5
def get_angular_vel(bus):
    angular_velocity_register = None
    msg = send_read_and_wait(bus, Register.ANGULAR_VEL)
    if msg is not None:
        angular_velocity_register = int.from_bytes([msg.data[2], msg.data[3]], byteorder='little', signed=True)
    return angular_velocity_register


# Angular velocity is not eligible to be set


# Returns in centidegrees Celsius, to convert to degrees celsius perform get_temperature(bus) / 100
def get_temperature(bus):
    temperature_register = None
    msg = send_read_and_wait(bus, Register.TEMPERATURE)
    if msg is not None:
        temperature_register = int.from_bytes([msg.data[2], msg.data[3]], byteorder='little', signed=True)
    return temperature_register


# Temperature is not eligible to be set


def get_spin_dir(bus):
    spin_dir = None
    msg = send_read_and_wait(bus, Register.SPIN_DIR)
    if msg is not None:
        match msg.data[2]:
            case 0x00:
                spin_dir = 'clockwise'
            case 0x01:
                spin_dir = 'counterclockwise'
    return spin_dir


def set_spin_dir(bus, direction, unlock=True):
    payload = [0x00, 0x00]
    match direction:
        case 'clockwise':
            payload[0] = 0x00
        case 'counterclockwise':
            payload[0] = 0x01
        case _:
            raise ValueError('Invalid spin direction provided')
    send_write_request(bus, Register.SPIN_DIR, payload, unlock)


# Returns in 10^-4 seconds, i.e. hundreds of microseconds
def get_angular_vel_sample_period(bus):
    angular_vel_sample_register = None
    msg = send_read_and_wait(bus, Register.ANGULAR_VEL_SAMPLE_PERIOD)
    if msg is not None:
        angular_vel_sample_register = int.from_bytes([msg.data[2], msg.data[3]], byteorder='little', signed=False)
    return angular_vel_sample_register


def set_angular_vel_sample_period(bus, sample_period, unlock=True):
    if sample_period < 1 or sample_period >= 2e16: raise ValueError('Invalid sample period provided')
    payload = int.to_bytes(sample_period, 2, byteorder='little', signed=True)
    send_write_request(bus, Register.ANGULAR_VEL_SAMPLE_PERIOD, payload, unlock)


# No idea what this returns
def get_read_register(bus):
    read_register = None
    msg = send_read_and_wait(bus, Register.READ_REGISTER)
    if msg is not None:
        read_register = list(msg.data)
    return read_register


# Not confident in what READ_REGISTER does, so not allowing writing


def get_device_addr(bus):
    device_address = None
    msg = send_read_and_wait(bus, Register.DEVICE_ADDR)
    if msg is not None:
        device_address = int.from_bytes([msg.data[2], msg.data[3]], byteorder='little', signed=False)
    return device_address


def set_device_addr(bus, address, unlock=True):
    if address < 0 or address >= 2e11: raise ValueError('Invalid CAN address provided')
    payload = int.to_bytes(address, 2, byteorder='little', signed=False)
    send_write_request(bus, Register.DEVICE_ADDR, payload, unlock)


def get_version_num_l(bus):
    version_num_l = None
    msg = send_read_and_wait(bus, Register.VERSION_NUM_L)
    if msg is not None:
        version_num_l = list(msg.data)
    return version_num_l


def get_version_num_h(bus):
    version_num_h = None
    msg = send_read_and_wait(bus, Register.VERSION_NUM_H)
    if msg is not None:
        version_num_h = list(msg.data)
    return version_num_h


# Version number is not eligible to be set


def connect_read_and_wait(register: Register, timeout=1, retries=0):
    # Built from example at https://python-can.readthedocs.io/en/v4.2.2/listeners.html
    with can.Bus(interface='slcan', channel=COM_PORT, bitrate=250000) as bus:
        response = None
        msg = send_read_and_wait(bus, register, timeout, retries)
        if msg is not None:
            response = list(msg.data)
        return response


class State:
    def __init__(self):
        self.version_num_h = None
        self.version_num_l = None
        self.apply_settings_register = None
        self.read_register = None
        self.temperature = None
        self.revolutions = None
        self.angular_vel = None
        self.ang_val = None
        self.angular_vel_sample_period = None
        self.spin_dir = None
        self.content_mode = None
        self.encoder_mode = None
        self.return_rate = None
        self.baud_rate = None
        self.device_addr = None

    def get_all(self, bus):
        self.device_addr = get_device_addr(bus)
        self.baud_rate = get_baud_rate(bus)
        self.return_rate = get_return_rate(bus)
        self.encoder_mode = get_encoder_mode(bus)
        self.content_mode = get_content_mode(bus)
        self.spin_dir = get_spin_dir(bus)
        self.angular_vel_sample_period = get_angular_vel_sample_period(bus)
        self.ang_val = get_ang_val(bus)
        self.angular_vel = get_angular_vel(bus)
        self.revolutions = get_revolutions(bus)
        self.temperature = get_temperature(bus)
        self.read_register = get_read_register(bus)
        self.apply_settings_register = get_apply_settings_register(bus)
        self.version_num_l = get_version_num_l(bus)
        self.version_num_h = get_version_num_h(bus)

    def print_all(self):
        # Padding for each text block
        padding_0 = 15
        padding_1 = 31
        padding_2 = 25
        padding_3 = 29

        print(f"{'device address:':<{padding_0}} {hex(self.device_addr) if self.device_addr is not None else 'error'}")
        print(f"{'baud rate:':<{padding_0}} {f"{self.baud_rate} K" if self.baud_rate is not None else 'error'}")
        print(f"{'publish rate:':<{padding_0}} {f"{self.return_rate} Hz" if self.return_rate is not None else 'error'}")
        print(
            f"{'encoder mode:':<{padding_0}} {f"{self.encoder_mode}-turn" if self.encoder_mode is not None else 'error'}")
        print(f"{'content mode:':<{padding_0}} {f"{self.content_mode}" if self.content_mode is not None else 'error'}")
        print(f"{'spin direction:':<{padding_0}} {f"{self.spin_dir}" if self.spin_dir is not None else 'error'}")
        print()
        print(
            f"{'angular velocity sample period:':<{padding_1}} {f"{self.angular_vel_sample_period / 10} ms" if self.angular_vel_sample_period is not None else 'error'}")
        print()
        print(
            f"{'current angle:':<{padding_2}} {f"{self.ang_val * 360 / 32768}°" if self.ang_val is not None else 'error'}")
        print(
            f"{'current angular velocity:':<{padding_2}} {f"{self.angular_vel * 360 / 32768 / self.angular_vel_sample_period / 10e4}°/s" if self.angular_vel is not None and self.angular_vel_sample_period is not None else 'error'}")
        print(
            f"{'current revolutions:':<{padding_2}} {f"{self.revolutions}" if self.revolutions is not None else 'error'}")
        print(
            f"{'current temperature:':<{padding_2}} {f"{self.temperature / 100} °C" if self.temperature is not None else 'error'}")
        print()
        print(
            f"{'read register:':<{padding_3}} {f"{'[{}]'.format(', '.join(f'0x{x:02x}' for x in self.read_register))}" if self.read_register is not None else 'error'}")
        print(
            f"{'apply settings register:':<{padding_3}} {f"{'[{}]'.format(', '.join(f'0x{x:02x}' for x in self.apply_settings_register))}" if self.apply_settings_register is not None else 'error'}")
        print(
            f"{'version number low register:':<{padding_3}} {f"{'[{}]'.format(', '.join(f'0x{x:02x}' for x in self.version_num_l))}" if self.version_num_l is not None else 'error'}")
        print(
            f"{'version number high register:':<{padding_3}} {f"{'[{}]'.format(', '.join(f'0x{x:02x}' for x in self.version_num_h))}" if self.version_num_h is not None else 'error'}")


def print_all_info():
    with can.Bus(interface='slcan', channel=COM_PORT, bitrate=250000) as bus:
        state = State()
        state.get_all(bus)
        state.print_all()


def test_write_settings():
    with can.Bus(interface='slcan', channel=COM_PORT, bitrate=250000) as bus:
        unlock_msg = can.Message(arbitration_id=DEVICE_ADDR,
                                 data=[0xFF, 0xAA, 0x69, 0x88, 0xB5],
                                 is_extended_id=False)

        # Check that we are currently in clockwise
        print("Begin settings write test:")
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, must be clockwise")

        print()

        print("Attempting to write without unlocking, should still be clockwise")
        send_write_request(bus, Register.SPIN_DIR, [0x01, 0x00], unlock=False)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected clockwise")

        print()

        print("Unlocking and writing counterclockwise, should now be counterclockwise")
        bus.send(unlock_msg)
        send_write_request(bus, Register.SPIN_DIR, [0x01, 0x00], unlock=False)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected counterclockwise")

        print()

        print("Restarting without saving, should now be clockwise")
        send_write_request(bus, Register.APPLY_SETTINGS, [0xFF, 0x00], unlock=False)
        time.sleep(1)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected clockwise")

        print()

        print("Attempting to write without unlocking again after restart, should still be clockwise")
        send_write_request(bus, Register.SPIN_DIR, [0x01, 0x00], unlock=False)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected clockwise")

        print()

        print("Double-unlocking, writing, saving, and restarting, should now be counterclockwise")
        bus.send(unlock_msg)
        bus.send(unlock_msg)
        send_write_request(bus, Register.SPIN_DIR, [0x01, 0x00], unlock=False)
        send_write_request(bus, Register.APPLY_SETTINGS, [0x00, 0x00], unlock=False)
        send_write_request(bus, Register.APPLY_SETTINGS, [0xFF, 0x00], unlock=False)
        time.sleep(1)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected counterclockwise")

        print()

        print("Attempting to write clockwise without unlocking after restart, should still be counterclockwise")
        send_write_request(bus, Register.SPIN_DIR, [0x00, 0x00], unlock=False)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected counterclockwise")

        print()

        print("Unlocking, writing clockwise, and writing counterclockwise without restarting")
        bus.send(unlock_msg)
        send_write_request(bus, Register.SPIN_DIR, [0x00, 0x00], unlock=False)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected clockwise")
        send_write_request(bus, Register.SPIN_DIR, [0x01, 0x00], unlock=False)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected counterclockwise")

        print()

        print("Saving counterclockwise, and restarting twice")
        send_write_request(bus, Register.APPLY_SETTINGS, [0x00, 0x00], unlock=False)
        send_write_request(bus, Register.APPLY_SETTINGS, [0xFF, 0x00], unlock=False)
        time.sleep(1)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected counterclockwise")
        send_write_request(bus, Register.APPLY_SETTINGS, [0xFF, 0x00], unlock=False)
        time.sleep(1)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected counterclockwise")

        print()

        print("Unlocking, resetting to clockwise and restarting")
        bus.send(unlock_msg)
        send_write_request(bus, Register.SPIN_DIR, [0x00, 0x00], unlock=False)
        send_write_request(bus, Register.APPLY_SETTINGS, [0x00, 0x00], unlock=False)
        send_write_request(bus, Register.APPLY_SETTINGS, [0xFF, 0x00], unlock=False)
        time.sleep(1)
        print(f"{'spin direction:':<} {get_spin_dir(bus)}, expected clockwise")

        # TODO: Should test factory resetting, feels dangerous though...


def test():
    global DEVICE_ADDR

    DEVICE_ADDR = 0x50
    with can.Bus(interface='slcan', channel=COM_PORT, bitrate=250000) as bus:
        print(get_device_addr(bus))
        set_device_addr(bus, 0x51)
        DEVICE_ADDR = 0x51
        print(get_device_addr(bus))
        apply_settings(bus, 'save', False)
        apply_settings(bus, 'restart', False)
    time.sleep(1)

    print_all_info()
    print()
    time.sleep(10)
    print_all_info()
    print()
    with can.Bus(interface='slcan', channel=COM_PORT, bitrate=250000) as bus:
        print(get_device_addr(bus))
        # apply_settings(bus, 'save', True)
        get_apply_settings_register(bus)
        apply_settings(bus, 'restart', True)
        get_apply_settings_register(bus)
        time.sleep(1)
        print(get_device_addr(bus))
        time.sleep(1)
    # test_write_settings()


if __name__ == "__main__":
    # print(connect_read_and_wait(Register.CONTENT_MODE))
    # print_all_info()
    # # print(connect_read_and_wait(Register.SPIN_DIR))
    test()
