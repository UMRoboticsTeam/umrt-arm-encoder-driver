import encoder
import sys
import argparse
import can


def get_cli_args():
    parser = argparse.ArgumentParser(
        add_help=True,
        prog="cli.py",
        description="""
        Update Description
        """,
    )
    parser.add_argument("--id", action="store", type=int, default=80, help="ID to send messages to.")
    parser.add_argument("-c", "--channel", action="store", type=str, default="/dev/ttyACM0", help="Device to communicate")
    parser.add_argument("-i", "--interface", action="store", type=str, default="slcan", help="CAN interface to use")
    parser.add_argument("-b", "--baud", action="store", type=int, default=250, help="Frequency to communicate with the encoder. (default: 250)")
    parser.add_argument("--change-spin-direction", action="store", type=str, default=None, help="")
    parser.add_argument("--upload-config", action="store", type=argparse.FileType("r"), help="Upload the confiuration from the file into the connected encoder.")
    args = parser.parse_args()
    return args


print(sys.argv)
args = get_cli_args()
print(args)
with can.Bus(interface=args.interface, channel=args.channel, bitrate=args.baud * 1000) as bus:
    enc = encoder.Encoder(bus, args.id)

    # enc.unlock()
    # enc.set_baud_rate(250)
    # enc.apply_settings("save")
    # print("success!")
    if args.change_spin_direction != None and False:
        enc.unlock()
        enc.set_spin_dir()
    else:
        print("no command prided!")
        exit(1)
    # enc.read_all()
    # enc.print_all_settings()
