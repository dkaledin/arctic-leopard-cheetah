#!/usr/bin/env python3
import argparse
import re
import sys
import time

import serial


DEFAULT_PORT = "/dev/cu.usbserial-10"
DEFAULT_BAUDRATE = 19200
POLL_LEFT = bytes.fromhex("AA 01 01 AC FF")

COMMANDS = {
    "idle": bytes.fromhex("AB 02 00 AD FF"),
    "up": bytes.fromhex("AB 02 01 AE FF"),
    "down": bytes.fromhex("AB 02 02 AF FF"),
    "mode": bytes.fromhex("AB 02 04 B1 FF"),
    "ready": bytes.fromhex("AB 02 08 B5 FF"),
    "drive": bytes.fromhex("AB 02 10 BD FF"),
    "park": bytes.fromhex("AB 02 20 CD FF"),
    "low_beam": bytes.fromhex("AB 01 02 00 AE FF"),
    "high_beam": bytes.fromhex("AB 01 04 00 B0 FF"),
    "flash_high": bytes.fromhex("AB 01 01 00 AD FF"),
    "horn": bytes.fromhex("AB 01 00 02 AE FF"),
    "turn_left": bytes.fromhex("AB 01 00 08 B4 FF"),
    "turn_right": bytes.fromhex("AB 01 00 04 B0 FF"),
    "hazard": bytes.fromhex("AB 01 00 10 BC FF"),
    "regen_down": bytes.fromhex("AB 01 10 00 BC FF"),
    "regen_up": bytes.fromhex("AB 01 20 00 CC FF"),
    "reverse": bytes.fromhex("AB 01 00 01 AD FF"),
}

COMBOS = {
    "drive_on": ("ready", 0.3, "drive"),
}

RELEASE_FRAMES = {
    "reverse": bytes.fromhex("AB 01 00 00 AC FF"),
}


def hex_bytes(data):
    return " ".join(f"{b:02X}" for b in data)


def parse_hex(text):
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", text)
    if len(cleaned) % 2:
        raise argparse.ArgumentTypeError("hex string must contain whole bytes")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def frame_for_args(args):
    if args.hex:
        return parse_hex(args.hex)
    return COMMANDS[args.command]


def write_repeated(ser, frame, duration, interval):
    deadline = time.monotonic() + duration
    count = 0
    while time.monotonic() < deadline:
        ser.write(frame)
        ser.flush()
        count += 1
        time.sleep(interval)
    return count


def send_combo(ser, args):
    first, delay, second = COMBOS[args.command]
    count = 0
    first_frame = COMMANDS[first]
    second_frame = COMMANDS[second]

    print(
        f"combo={args.command} first={first}:{hex_bytes(first_frame)} "
        f"delay={delay:g}s second={second}:{hex_bytes(second_frame)}"
    )

    count += write_repeated(ser, first_frame, args.combo_pulse, args.interval)
    time.sleep(delay)
    count += write_repeated(ser, second_frame, args.duration, args.interval)
    return count


def respond_reverse(args):
    hold_until = time.monotonic() + args.duration
    stop_at = hold_until + args.release_window
    buf = bytearray()
    held_count = 0
    release_count = 0
    poll_count = 0

    held_frame = COMMANDS["reverse"]
    release_frame = RELEASE_FRAMES["reverse"]
    print(f"port={args.port} baudrate={args.baudrate}")
    print(f"poll={hex_bytes(POLL_LEFT)}")
    print(f"held_response={hex_bytes(held_frame)} for {args.duration:g}s")
    print(f"release_response={hex_bytes(release_frame)} for {args.release_window:g}s")

    if not args.yes:
        print("\nDry run only. Add --yes to actually respond on the bus.")
        return 0

    try:
        with serial.Serial(
            args.port,
            args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.005,
            write_timeout=0.05,
        ) as ser:
            ser.reset_input_buffer()
            while time.monotonic() < stop_at:
                chunk = ser.read(256)
                if chunk:
                    buf.extend(chunk)
                    while True:
                        idx = buf.find(POLL_LEFT)
                        if idx < 0:
                            if len(buf) > len(POLL_LEFT):
                                del buf[: -(len(POLL_LEFT) - 1)]
                            break

                        del buf[: idx + len(POLL_LEFT)]
                        poll_count += 1
                        if time.monotonic() < hold_until:
                            response = held_frame
                            held_count += 1
                        else:
                            response = release_frame
                            release_count += 1

                        if args.delay > 0:
                            time.sleep(args.delay)
                        ser.write(response)
                        ser.flush()
                        if args.print_responses:
                            print(
                                f"poll#{poll_count} -> {hex_bytes(response)}",
                                flush=True,
                            )
                else:
                    time.sleep(0.001)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 2

    print(
        f"done polls={poll_count} held_responses={held_count} "
        f"release_responses={release_count}"
    )
    return 0


def send_frame(args):
    if args.command == "reverse" and not args.hex:
        return respond_reverse(args)

    if args.command in COMBOS and not args.hex:
        print(f"port={args.port} baudrate={args.baudrate}")
        frame = None
        first, delay, second = COMBOS[args.command]
        print(
            f"combo={args.command} first={first}:{hex_bytes(COMMANDS[first])} "
            f"delay={delay:g}s second={second}:{hex_bytes(COMMANDS[second])}"
        )
    else:
        frame = frame_for_args(args)
        print(f"port={args.port} baudrate={args.baudrate} frame={hex_bytes(frame)}")
    print(f"interval={args.interval:g}s duration={args.duration:g}s")

    if not args.yes:
        print("\nDry run only. Add --yes to actually transmit.")
        return 0

    deadline = time.monotonic() + args.duration
    count = 0
    try:
        with serial.Serial(
            args.port,
            args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.02,
            write_timeout=0.5,
        ) as ser:
            ser.reset_input_buffer()

            for _ in range(args.pre_idle):
                ser.write(COMMANDS["idle"])
                ser.flush()
                time.sleep(args.interval)

            if args.command in COMBOS and not args.hex:
                count += send_combo(ser, args)
            else:
                while time.monotonic() < deadline:
                    ser.write(frame)
                    ser.flush()
                    count += 1
                    time.sleep(args.interval)

            release_frame = RELEASE_FRAMES.get(args.command)
            if release_frame and not args.hex:
                ser.write(release_frame)
                ser.flush()
                count += 1
                print(f"release={hex_bytes(release_frame)}")

            for _ in range(args.post_idle):
                ser.write(COMMANDS["idle"])
                ser.flush()
                count += 1
                time.sleep(args.interval)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 2

    print(f"sent_frames={count}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Send raw 19200 8N1 command frames through a USB-RS485 adapter."
    )
    parser.add_argument(
        "command",
        choices=sorted({*COMMANDS, *COMBOS}),
        nargs="?",
        default="idle",
        help="named command to send",
    )
    parser.add_argument("--hex", help="custom frame bytes, e.g. 'AB 02 01 AE FF'")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--interval", type=float, default=0.05)
    parser.add_argument(
        "--combo-pulse",
        type=float,
        default=0.2,
        help="how long to send the first frame in combo commands",
    )
    parser.add_argument(
        "--release-window",
        type=float,
        default=1.0,
        help="for reverse: how long to answer with release after hold duration",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="for reverse: optional delay before response, seconds",
    )
    parser.add_argument(
        "--print-responses",
        action="store_true",
        help="for reverse: print each poll response",
    )
    parser.add_argument("--pre-idle", type=int, default=2)
    parser.add_argument("--post-idle", type=int, default=2)
    parser.add_argument("--yes", action="store_true", help="actually transmit")
    args = parser.parse_args()

    if args.duration is None:
        args.duration = 3.0 if args.command == "reverse" and not args.hex else 0.5
    if args.duration <= 0:
        parser.error("--duration must be positive")
    if args.interval <= 0:
        parser.error("--interval must be positive")
    if args.release_window < 0:
        parser.error("--release-window must not be negative")
    if args.delay < 0:
        parser.error("--delay must not be negative")

    return send_frame(args)


if __name__ == "__main__":
    raise SystemExit(main())
