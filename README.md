# Arctic Leopard Cheetah RS-485 Controls

Small Python tools and protocol notes for talking to the handlebar control bus on an Arctic Leopard Cheetah electric motorcycle.

This project is based on reverse engineering of the left and right handlebar switch packets. The bus is **not classic CAN**. The tested control line behaves like **half-duplex RS-485 / UART at 19200 baud, 8N1, LSB first**.

## Описание на русском

Этот репозиторий содержит скрипты и описание протокола пультов электромотоцикла **Arctic Leopard Cheetah**. Мы выяснили, что на исследованном разъёме идёт не CAN-шина, а RS-485/UART-подобный обмен на `19200 8N1`. Скрипт позволяет через USB-RS485 адаптер отправлять команды пультов: `READY`, `DRIVE`, `PARK`, переключение режимов, поворотники, свет, сигнал, рекуперацию и задний ход.

Проект может быть полезен тем, кто ищет: Arctic Leopard Cheetah CAN, протокол пульта Arctic Leopard, RS-485 пульт электромотоцикла, reverse engineering электромотоцикла, управление контроллером через UART/RS485.

The main script is:

```bash
python3 rs485_send.py <command> --yes
```

By default the script uses:

```text
port:     /dev/cu.usbserial-10
baudrate: 19200
format:   8 data bits, no parity, 1 stop bit
```

## Demo Videos

These short clips show the prototype connected to the motorcycle through a USB-RS485 adapter and switching drive modes from the script:

- [Drive mode demo 1](media/drive-mode-demo-1.mov)
- [Drive mode demo 2](media/drive-mode-demo-2.mov)

## Safety

These commands can affect a real motorcycle.

- Test with the rear wheel off the ground.
- Do not test `drive_on`, `drive`, or `reverse` near people, vehicles, walls, or tools.
- Keep a physical way to cut power.
- Use this only on hardware you own and understand.
- The protocol was reverse engineered from one bike. Your model or firmware may differ.

## Hardware

Use a USB to RS-485 adapter. The adapter tested here appears on macOS as:

```text
/dev/cu.usbserial-10
VID:PID 1a86:7523
```

Adapter used during debugging: <https://ozon.ru/t/iNot3Bo>

That VID/PID is commonly used by CH340/CH341 USB serial chips. Other USB-RS485 adapters should work if they expose a normal serial port.

Recommended parts:

- USB-RS485 adapter with automatic TX/RX direction control.
- CH340/CH341, FT232, CP210x, or similar USB serial chip.
- RS-485 transceiver on the adapter, usually MAX485, SP3485, CH343 RS485 board, or equivalent.
- Three wires to the bike bus: `A`, `B`, and `GND`.

Do **not** connect the motorcycle battery `+` line to the USB-RS485 adapter. Use only signal pair plus ground.

If commands do nothing, swap `A` and `B`.

## Install

macOS:

```bash
python3 -m pip install -r requirements.txt
```

If your Python environment does not have pip:

```bash
python3 -m ensurepip --upgrade
python3 -m pip install pyserial
```

## Quick Start

Dry run, does not transmit:

```bash
python3 rs485_send.py up
```

Actually transmit:

```bash
python3 rs485_send.py up --yes
```

Use a different serial port:

```bash
python3 rs485_send.py up --port /dev/cu.usbserial-110 --yes
```

Turn on drive mode using the tested sequence:

```bash
python3 rs485_send.py drive_on --yes
```

Hold reverse for 3 seconds. This command works as a bus responder: it waits for the left handlebar poll and answers in the correct timing window.

```bash
python3 rs485_send.py reverse --duration 3 --print-responses --yes
```

## Commands

Right handlebar / drive mode:

| Script command | Frame |
| --- | --- |
| `idle` | `AB 02 00 AD FF` |
| `up` | `AB 02 01 AE FF` |
| `down` | `AB 02 02 AF FF` |
| `mode` | `AB 02 04 B1 FF` |
| `ready` | `AB 02 08 B5 FF` |
| `drive` | `AB 02 10 BD FF` |
| `park` | `AB 02 20 CD FF` |

Left handlebar:

| Script command | Frame |
| --- | --- |
| `low_beam` | `AB 01 02 00 AE FF` |
| `high_beam` | `AB 01 04 00 B0 FF` |
| `flash_high` | `AB 01 01 00 AD FF` |
| `horn` | `AB 01 00 02 AE FF` |
| `turn_left` | `AB 01 00 08 B4 FF` |
| `turn_right` | `AB 01 00 04 B0 FF` |
| `hazard` | `AB 01 00 10 BC FF` |
| `regen_down` | `AB 01 10 00 BC FF` |
| `regen_up` | `AB 01 20 00 CC FF` |
| `reverse` | responder mode, see below |

Reverse is different. It is not just a blind transmit frame. The controller polls the left handlebar:

```text
AA 01 01 AC FF
```

The script answers while reverse is held:

```text
AB 01 00 01 AD FF
```

Then it answers with release:

```text
AB 01 00 00 AC FF
```

## Custom Frame

You can send an arbitrary frame:

```bash
python3 rs485_send.py --hex "AB 02 04 B1 FF" --yes
```

## Project Status

This is a practical reverse-engineering project. It is not an official Arctic Leopard tool. Pull requests with tested captures, safer hardware notes, and support for other bike revisions are welcome.
