"""Print raw serial bytes as hexadecimal; stop with Ctrl+C."""

import argparse
import time


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="COM4")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=3)
    args = parser.parse_args(argv)
    import serial

    try:
        with serial.Serial(args.port, args.baudrate, timeout=args.timeout) as connection:
            connection.setDTR(False)
            connection.setRTS(False)
            print(f"Opened {args.port} at {args.baudrate} baud. Press Ctrl+C to stop.")
            while True:
                waiting = connection.in_waiting
                if waiting:
                    print(connection.read(waiting).hex(" "))
                time.sleep(1)
    except KeyboardInterrupt:
        print("Serial monitor stopped.")
    except serial.SerialException as error:
        parser.exit(1, f"Serial connection failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
