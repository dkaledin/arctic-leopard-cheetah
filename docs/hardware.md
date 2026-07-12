# Hardware Notes

## Tested Adapter

The tested USB-RS485 adapter enumerated on macOS as:

```text
/dev/cu.usbserial-10
USB Serial
Vendor ID: 0x1a86
Product ID: 0x7523
```

This is a common WCH CH340/CH341-style USB serial adapter.

## What to Buy

Any USB-RS485 adapter should be a reasonable starting point if it supports:

- 19200 baud.
- 8N1 serial format.
- Half-duplex RS-485.
- Automatic transmit/receive direction control.

Common chips and boards:

- CH340 / CH341 USB serial adapters.
- FT232 USB serial adapters.
- CP2102 / CP210x USB serial adapters.
- MAX485, SP3485, or similar RS-485 transceiver boards.

## Wiring

Typical USB-RS485 adapter terminals:

```text
A  -> one bus signal wire
B  -> the other bus signal wire
GND -> bike control ground / signal ground
```

Do not connect battery positive to the USB-RS485 adapter.

If no bytes are received or commands do not work, swap `A` and `B`.

## Logic Analyzer

A cheap Saleae-compatible 24 MHz 8-channel logic analyzer was useful during reverse engineering.

Useful settings:

```text
Sample rate: 4 MHz or 8 MHz
Channels: D4, D6
Decoder: UART
Baud: 19200
8 data bits
No parity
1 stop bit
LSB first
Idle high
```

The logic analyzer is not needed to use `rs485_send.py`; it is only useful for discovering new commands.
