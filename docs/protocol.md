# Protocol Notes

## Physical Layer

Observed bus:

```text
RS-485 / UART-like half duplex
19200 baud
8 data bits
No parity
1 stop bit
LSB first
Idle high
```

The bus was first mistaken for CAN because the bike connector has two signal wires and a ground. A CAN adapter did not decode valid CAN traffic. A logic analyzer and a USB-RS485 adapter showed stable 19200 baud UART-like packets.

## Packet Shape

Most useful packets use this form:

```text
AB <group> <byte2> <byte3> <checksum> FF
```

Poll packets seen from the controller use `AA`:

```text
AA <group> <byte2> <checksum> FF
```

The checksum appears to be an 8-bit additive checksum of the bytes before it.

Examples:

```text
AB 02 08 B5 FF
AB + 02 + 08 = B5

AB 01 00 10 BC FF
AB + 01 + 00 + 10 = BC

AA 01 01 AC FF
AA + 01 + 01 = AC
```

`FF` is the packet terminator.

## Right Handlebar Group

Right handlebar frames use group `02`.

```text
AB 02 <button_bits> <checksum> FF
```

Known bits:

| Bit | Meaning | Frame |
| --- | --- | --- |
| `0x00` | no button | `AB 02 00 AD FF` |
| `0x01` | UP | `AB 02 01 AE FF` |
| `0x02` | DOWN | `AB 02 02 AF FF` |
| `0x04` | MODE | `AB 02 04 B1 FF` |
| `0x08` | READY | `AB 02 08 B5 FF` |
| `0x10` | DRIVE | `AB 02 10 BD FF` |
| `0x20` | PARK | `AB 02 20 CD FF` |

`drive_on` sends `READY`, waits 300 ms, then sends `DRIVE`.

## Left Handlebar Group

Left handlebar frames use group `01`.

The left handlebar has more than one bit byte:

```text
AB 01 <byte2> <byte3> <checksum> FF
```

Known bits:

| Function | Frame |
| --- | --- |
| Low beam | `AB 01 02 00 AE FF` |
| High beam | `AB 01 04 00 B0 FF` |
| High beam flash/pass | `AB 01 01 00 AD FF` |
| Horn | `AB 01 00 02 AE FF` |
| Left turn signal | `AB 01 00 08 B4 FF` |
| Right turn signal | `AB 01 00 04 B0 FF` |
| Hazard | `AB 01 00 10 BC FF` |
| Regen down | `AB 01 10 00 BC FF` |
| Regen up | `AB 01 20 00 CC FF` |

## Reverse

Reverse is timing-sensitive. The controller sends:

```text
AA 01 01 AC FF
```

The left handlebar answers:

```text
AB 01 00 01 AD FF
```

When released:

```text
AB 01 00 00 AC FF
```

The script implements `reverse` as a responder, not as blind periodic transmit.

## Timing

Observed reverse capture:

```text
55 reverse responses in about 3 seconds
```

That is about 18 responses per second, or roughly one response every 55 ms.

## Notes

If a command works when captured from the original switch but does not work when transmitted manually, check:

- RS-485 `A/B` polarity.
- Common `GND`.
- Timing after poll frames.
- Whether another handlebar module is still answering at the same time.
- Whether the adapter supports fast automatic TX/RX direction control.
