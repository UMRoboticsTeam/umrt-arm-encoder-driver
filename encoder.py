import can
import sys
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

    ANGLE_VALUE = 0x11
    # The current angle of the encoder
    # Follows the formula: Angle [°] = ANGLE_REG * 360 / 32768
    # Therefore, to set the current angle to 30°, ANGLE_REG = (30°) * 32768 / 360 = 2730 should be written

    REVOLUTIONS = 0x12
    # The current number of revolutions which have occurred
    # Signed 16-bit integer

    ANGULAR_VELOCITY = 0x13
    # The current angular velocity
    # Formula: Angular velocity [°/s] = ANGULAR_VEL_REG * 360 / 32768 / (Angular velocity sampling time [s])
    # Signed 16-bit integer

    TEMPERATURE = 0x14
    # The current temperature
    # Follows the formula: Temperature [°C] = TEMPERATURE_REG / 100
    # 16-bit integer, presumably signed

    SPIN_DIRECTION = 0x15
    # Whether CW or CCW is considered the positive rotation
    # Values:
    #   0x00: Clockwise when viewed from the base is positive
    #   0x01: Counterclockwise when viewed from the base is positive
    # Defaults to clockwise = 0x00

    ANGULAR_VELOCITY_SAMPLE_PERIOD = 0x17
    # The amount of time to wait between angular velocity samples when internally calculating
    # The angular velocity is calculated by a running sum, so if the sample rate is too high the register can overflow
    # Follows the formula: Sample time [s] = SAMPLE_TIME_REG * 100 μs
    # 16-bit integer, presumably unsigned ("The minimum register value is 1" in manual)
    # Defaults to 100 ms = 1000

    READ_REGISTER = 0x27
    # The manual lists this as a register address, but I believe it is actually just a command

    DEVICE_ADDRESS = 0x1A
    # The address this encoder uses on the CAN bus
    # 11-bit unsigned integer
    # Defaults to 0x50

    VERSION_NUM_L = 0x2E
    # Appears to be the low word of the version number

    VERSION_NUM_H = 0x2F
    # Appears to be the high word of the version number


REGISTERS_WRITABLE = [
    Register.APPLY_SETTINGS,
    Register.CONTENT_MODE,
    Register.RETURN_RATE,
    Register.BAUD_RATE,
    Register.ENCODER_MODE,
    Register.ANGLE_VALUE,
    Register.REVOLUTIONS,
    Register.SPIN_DIRECTION,
    Register.ANGULAR_VELOCITY_SAMPLE_PERIOD,
    Register.DEVICE_ADDRESS,
    # Cannot set the following:
    #   ANGULAR_VELOCITY
    #   TEMPERATURE
    #   READ_REGISTER
    #   VERSION_NUM_L
    #   VERSION_NUM_H
]

REGISTERS_READABLE = [
    Register.DEVICE_ADDRESS,
    Register.BAUD_RATE,
    Register.RETURN_RATE,
    Register.CONTENT_MODE,
    Register.ENCODER_MODE,
    Register.SPIN_DIRECTION,
    Register.ANGULAR_VELOCITY_SAMPLE_PERIOD,
    Register.ANGLE_VALUE,
    Register.REVOLUTIONS,
    Register.ANGULAR_VELOCITY,
    Register.TEMPERATURE,
    Register.VERSION_NUM_L,
    Register.VERSION_NUM_H,
    # It doesn't really make sense to read these:
    #   APPLY_SETTINGS
    #   READ_REGISTER
]

REGISTER_READ_MAP = {
    Register.CONTENT_MODE: "get_content_mode",
    Register.RETURN_RATE: "get_return_rate",
    Register.BAUD_RATE: "get_baud_rate",
    Register.ENCODER_MODE: "get_encoder_mode",
    Register.ANGLE_VALUE: "get_ang_val",
    Register.REVOLUTIONS: "get_revolutions",
    Register.SPIN_DIRECTION: "get_spin_dir",
    Register.ANGULAR_VELOCITY_SAMPLE_PERIOD: "get_angular_vel_sample_period",
    Register.DEVICE_ADDRESS: "get_device_addr",
    Register.ANGULAR_VELOCITY: "get_angular_vel",
    Register.TEMPERATURE: "get_temperature",
    Register.VERSION_NUM_L: "get_version_num_l",
    Register.VERSION_NUM_H: "get_version_num_h",
}

# Unlocks settings; Must be sent before settings can be written.
MSG_UNLOCK = [0xFF, 0xAA, 0x69, 0x88, 0xB5]


def create_read_request_msg(register: Register):
    assert isinstance(register, Register), "register must be valid"
    assert register in REGISTERS_READABLE, "register must be marked as readable"
    return [0xFF, 0xAA, Register.READ_REGISTER, register, 0x00]


def create_write_request_msg(register: Register, payload: list[2]):
    assert isinstance(register, Register), "register must be valid"
    assert register in REGISTERS_WRITABLE, "register must be marked as writable"
    assert type(payload) == list, "payload must be a list"
    assert len(payload) == 2, "payload must have length 2"

    for i in range(len(payload)):
        assert type(payload[i]) == int, "payload must be integer"
        assert payload[i] >= 0, "payload must not be negative"
        assert payload[i] <= 0xFF, "payload must not be greater than 0xFF"

    return [0xFF, 0xAA, register, payload[0], payload[1]]


class Encoder:
    def __init__(self, bus: can.BusABC, arbitration_id: int):
        # Note: Strive to store the minimum amount of state required.
        self.bus = bus
        self.id = arbitration_id
        # Store sent_unlock to warn users in the console,
        # DO NOT automatically send the unlock message.
        # The user should just call .unlock() when they desire to.
        self.sent_unlock = False
        # Do not reference this state unless explicitly called out,
        # i.e. no automatically caching unless you make a function called
        # cached_read(...)
        self.settings = {i: None for i in Register}

    ##### Fundamental IO #####

    def _send(self, msg, timeout=None):
        if type(msg) == list and len(msg) <= 8:
            msg = can.Message(
                arbitration_id=self.id,
                data=msg,
                is_extended_id=False,
            )
        # TODO: Be able to toggle logging
        print(f"Sending:", hex(self.id), [hex(i)[2:] for i in list(msg.data)])
        try:
            self.bus.send(msg, timeout)
            # time.sleep(0.1)
            return True
        except can.CanError as e:
            print("Error sending CAN message")
            print(e)
            return False

    def _recv(self, timeout=None):
        msg = self.bus.recv(timeout)
        return msg

    ##### Broader scope functions #####

    def send_read_request(self, register: Register):
        return self._send(create_read_request_msg(register))

    def send_write_request(self, register: Register, payload):
        if not self.sent_unlock:
            print("Warning: Sending write request without unlocking", file=sys.stderr)
        return self._send(create_write_request_msg(register, payload))

    def send_read_and_wait(self, register: Register, timeout=1, retries=0):
        self.send_read_request(register)

        for _ in range(retries + 1):
            abort_time = time.time() + timeout
            while time.time() < abort_time:
                msg = self._recv(1)
                if (
                    msg is not None
                    and len(msg.data) == 8
                    and msg.data[0] == 0x55
                    and msg.data[1] == 0x5F
                ):
                    return msg
        return None

    def unlock(self):
        self.sent_unlock = self._send(MSG_UNLOCK)
        return self.sent_unlock

    def read_all(self, /, include=None, pause=0.1):
        for reg in REGISTERS_READABLE:
            self.settings[reg] = self.read_register(reg)

    def print_all_settings(self):
        for i in REGISTERS_READABLE[:4]:
            print(f"{i._name_:>30} : {self.settings[i]}")
        print()
        for i in REGISTERS_READABLE[4:7]:
            print(f"{i._name_:>30} : {self.settings[i]}")
        print()
        for i in REGISTERS_READABLE[7:11]:
            print(f"{i._name_:>30} : {self.settings[i]}")
        print()
        for i in REGISTERS_READABLE[11:]:
            print(f"{i._name_:>30} : {self.settings[i]}")

    def read_register(self, register: Register):
        assert register in REGISTERS_READABLE
        return getattr(self, REGISTER_READ_MAP[register])()

    def write_register_integer(self, register: Register, payload: int):
        assert payload >= 0 and payload <= 0xFFFF, "integer must fit in 16 bits"

        payload = list(int.to_bytes(address, 2, byteorder="little", signed=False))
        return self.send_write_request(Register.DEVICE_ADDRESS, payload)

    def read_register_integer(self, register: Register, signed=False):
        msg = self.send_read_and_wait(register)
        if msg is None:
            return None

        return int.from_bytes([msg.data[2], msg.data[3]], "little", signed=signed)

    ##### Register-specific Functions #####

    def get_device_addr(self):
        return self.read_register_integer(Register.DEVICE_ADDRESS)

    def set_device_addr(self, address):
        if address < 0 or address >= 2e11:
            raise ValueError("Invalid CAN address provided")
        payload = list(int.to_bytes(address, 2, byteorder="little", signed=False))

        self.send_write_request(Register.DEVICE_ADDRESS, payload)

    # TODO: Make an enum for this
    # Eligible modes: 'save', 'factory_reset', 'restart'
    def apply_settings(self, mode):
        payload = [0x00, 0x00]
        match mode:
            case "save":
                payload[0] = 0x00
            case "factory_reset":
                payload[0] = 0x01
            case "restart":
                payload[0] = 0xFF
            case _:
                raise ValueError("Invalid apply settings mode provided")
        self.send_write_request(Register.APPLY_SETTINGS, payload)

    # TODO: Make enum for content mode
    def get_content_mode(self):
        content_mode = None
        mode = self.read_register_integer(Register.CONTENT_MODE)
        if mode is not None:
            match mode:
                case 0x01:
                    content_mode = "angles"
                case 0x02:
                    content_mode = "temperature"
                case 0x03:
                    content_mode = "both"
        return content_mode

    def set_content_mode(self, content_mode):
        payload = [0x00, 0x00]
        match content_mode:
            case "angles":
                payload[0] = 0x01
            case "temperature":
                payload[0] = 0x02
            case "both":
                payload[0] = 0x03
            case _:
                raise ValueError("Invalid content mode provided")
        self.send_write_request(Register.CONTENT_MODE, payload)

    # TODO: Make enum for return rate
    def get_return_rate(self):
        rate_integer = self.read_register_integer(Register.RETURN_RATE)
        if rate_integer is None:
            return None

        return_rate = None
        match rate_integer:
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
                return_rate = "single_return"
        return return_rate

    def set_return_rate(self, return_rate):
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
            case "single_return":
                payload[0] = 0x0E
            case _:
                raise ValueError("Invalid rate provided")
        self.send_write_request(Register.RETURN_RATE, payload)

    # TODO: Make enum for baud rate
    def get_baud_rate(self):
        msg = self.read_register_integer(Register.BAUD_RATE)
        if msg is None:
            return None

        baud_rate = None
        match msg:
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

    def set_baud_rate(self, baud_rate):
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
                raise ValueError("Invalid baud rate provided")
        self.send_write_request(Register.BAUD_RATE, payload)

    # TODO: Make enum for encoder mode
    def get_encoder_mode(self):
        msg = self.read_register_integer(Register.ENCODER_MODE)
        if msg is None:
            return None

        encoder_mode = None
        match msg:
            case 0x00:
                encoder_mode = "single"
            case 0x01:
                encoder_mode = "multi"
        return encoder_mode

    def set_encoder_mode(self, mode):
        payload = [0x00, 0x00]
        match mode:
            case "single":
                payload[0] = 0x00
            case "multi":
                payload[0] = 0x01
            case _:
                raise ValueError("Invalid encoder mode provided")
        self.send_write_request(Register.ENCODER_MODE, payload)

    # TODO: Make enum for spin direction
    def get_spin_dir(self):
        spin_dir = None
        msg = self.send_read_and_wait(Register.SPIN_DIRECTION, timeout=2, retries=1)
        if msg is not None:
            match msg.data[2]:
                case 0x00:
                    spin_dir = "clockwise"
                case 0x01:
                    spin_dir = "counterclockwise"
        return spin_dir

    def set_spin_dir(self, direction):
        payload = [0x00, 0x00]
        match direction:
            case "clockwise":
                payload[0] = 0x00
            case "counterclockwise":
                payload[0] = 0x01
            case _:
                raise ValueError("Invalid spin direction provided")
        self.send_write_request(Register.SPIN_DIRECTION, payload)

    # Returns the angle register value, to convert to degrees perform get_ang_val() * 360 / 32768
    def get_ang_val(self):
        return self.read_register_integer(Register.ANGLE_VALUE)

    def set_ang_val(self, angle_register_value):
        if angle_register_value < 0 or angle_register_value >= 2e15:
            raise ValueError("Invalid angle value provided")
        payload = int.to_bytes(
            angle_register_value, 2, byteorder="little", signed=False
        )
        self.send_write_request(Register.ANGLE_VALUE, payload)

    def get_revolutions(self):
        return self.read_register_integer(Register.REVOLUTIONS, signed=True)

    def set_revolutions(self, revolutions):
        if revolutions < -2e15 or revolutions >= 2e15:
            raise ValueError("Invalid number of revolutions provided")
        payload = int.to_bytes(revolutions, 2, byteorder="little", signed=True)
        self.send_write_request(Register.REVOLUTIONS, payload)

    # Returns the angular velocity register value, to convert to degrees/s perform
    #   get_angular_vel() * 360 / 32768 / get_angular_vel_sample_period() / 10e5
    def get_angular_vel(self):
        return self.read_register_integer(Register.ANGULAR_VELOCITY, signed=True)

    # Returns in centidegrees Celsius, to convert to degrees celsius perform get_temperature() / 100
    def get_temperature(self):
        return self.read_register_integer(Register.TEMPERATURE, signed=True)

    # Returns in 10^-4 seconds, i.e. hundreds of microseconds
    def get_angular_vel_sample_period(self):
        return self.read_register_integer(Register.ANGULAR_VELOCITY_SAMPLE_PERIOD)

    def set_angular_vel_sample_period(self, sample_period):
        if sample_period < 1 or sample_period >= 2e16:
            raise ValueError("Invalid sample period provided")
        payload = int.to_bytes(sample_period, 2, byteorder="little", signed=True)
        self.send_write_request(Register.ANGULAR_VELOCITY_SAMPLE_PERIOD, payload)

    def get_version_num_l(self):
        version_num_l = None
        msg = self.send_read_and_wait(Register.VERSION_NUM_L)
        if msg is not None:
            version_num_l = list(msg.data)
        return version_num_l

    def get_version_num_h(self):
        version_num_h = None
        msg = self.send_read_and_wait(Register.VERSION_NUM_H)
        if msg is not None:
            version_num_h = list(msg.data)
        return version_num_h


def test_write_settings(interface, channel, bitrate):
    with can.Bus(interface=interface, channel=channel, bitrate=bitrate) as bus:
        enc = Encoder(bus, 0x51)
        # Check that we are currently in clockwise
        print("Begin settings write test:")
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, must be clockwise")

        print()

        print("Attempting to write without unlocking, should still be clockwise")
        enc.send_write_request(Register.SPIN_DIRECTION, [0x01, 0x00])
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected clockwise")

        print()

        print("Unlocking and writing counterclockwise, should now be counterclockwise")
        enc.unlock()
        enc.send_write_request(Register.SPIN_DIRECTION, [0x01, 0x00])
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected counterclockwise")

        print()

        print("Restarting without saving, should now be clockwise")
        enc.send_write_request(Register.APPLY_SETTINGS, [0xFF, 0x00])
        time.sleep(2)
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected clockwise")

        print()

        print(
            "Attempting to write without unlocking again after restart, should still be clockwise"
        )
        enc.send_write_request(Register.SPIN_DIRECTION, [0x01, 0x00])
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected clockwise")

        print()

        print(
            "Double-unlocking, writing, saving, and restarting, should now be counterclockwise"
        )
        enc.unlock()
        enc.unlock()
        enc.send_write_request(Register.SPIN_DIRECTION, [0x01, 0x00])
        enc.send_write_request(Register.APPLY_SETTINGS, [0x00, 0x00])
        enc.send_write_request(Register.APPLY_SETTINGS, [0xFF, 0x00])
        time.sleep(2)
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected counterclockwise")

        print()

        print(
            "Attempting to write clockwise without unlocking after restart, should still be counterclockwise"
        )
        enc.send_write_request(Register.SPIN_DIRECTION, [0x00, 0x00])
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected counterclockwise")

        print()

        print(
            "Unlocking, writing clockwise, and writing counterclockwise without restarting"
        )
        enc.unlock()
        enc.send_write_request(Register.SPIN_DIRECTION, [0x00, 0x00])
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected clockwise")
        enc.send_write_request(Register.SPIN_DIRECTION, [0x01, 0x00])
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected counterclockwise")

        print()

        print("Saving counterclockwise, and restarting twice")
        enc.send_write_request(Register.APPLY_SETTINGS, [0x00, 0x00])
        enc.send_write_request(Register.APPLY_SETTINGS, [0xFF, 0x00])
        time.sleep(2)
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected counterclockwise")
        enc.send_write_request(Register.APPLY_SETTINGS, [0xFF, 0x00])
        time.sleep(2)
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected counterclockwise")

        print()

        print("Unlocking, resetting to clockwise and restarting")
        enc.unlock()
        enc.send_write_request(Register.SPIN_DIRECTION, [0x00, 0x00])
        enc.send_write_request(Register.APPLY_SETTINGS, [0x00, 0x00])
        enc.send_write_request(Register.APPLY_SETTINGS, [0xFF, 0x00])
        time.sleep(2)
        print(f"{'spin direction:':<} {enc.get_spin_dir()}, expected clockwise")

        # TODO: Should test factory resetting, feels dangerous though...


def main(interface, channel, bitrate):
    # Get the address
    with can.Bus(interface=interface, channel=channel, bitrate=bitrate) as bus:
        enc = Encoder(bus, 0x51)
        enc.read_all()
        enc.print_all_settings()


if __name__ == "__main__":
    # Define bus connection here:
    interface = "socketcan"
    channel = "can1"
    bitrate = 250_000

    # test_write_settings(interface, channel, bitrate)
    main(interface, channel, bitrate)
