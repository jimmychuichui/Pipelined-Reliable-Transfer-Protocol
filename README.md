# PRTP - Pipelined Reliable Transfer Protocol (UDP-Based)

**PRTP** is a custom-designed reliable transfer protocol that operates over UDP. While UDP is inherently unreliable and connectionless, PRTP mimics many TCP features to ensure *reliability*, *connection orientation*, *flow control*, and *pipelining* – all with added resilience to *packet loss* and *bit errors*.

## 🌐 Protocol Overview

PRTP is designed to demonstrate how reliable transport protocols work under the hood by implementing these core features over UDP:

- **Connection-Oriented Communication**: Three-way handshake with `SYN`, `SYN-ACK`, and `ACK`.
- **Reliable Data Transfer**: Uses sequence numbers, acknowledgments, and retransmission strategies.
- **Pipelined Transfers**: Multiple packets can be sent without waiting for individual ACKs.
- **Flow Control**: Prevents overwhelming the receiver.
- **Congestion Control (Basic)**: Controls sending rate under certain conditions (optional/minimal).
- **Graceful Termination**: Connection is closed using a `FIN`, `FIN-ACK`, and `ACK` exchange.

## 📦 Packet Structure

Each PRTP packet follows a consistent format:

| Field            | Size        | Description                                 |
|------------------|-------------|---------------------------------------------|
| Packet Type      | 1 byte      | `0x1=SYN`, `0x2=ACK`, `0x4=FIN`             |
| Sequence Number  | 4 bytes     | Unique number per packet                    |
| Checksum         | 2 bytes     | For error detection                         |
| Payload          | Up to 1024 bytes | Actual message/data                        |

## 🧩 Features

- Connection Establishment (SYN, SYN-ACK, ACK)
- Ordered, reliable data transfer
- Bit error and packet loss detection & recovery
- Sliding window protocol for pipelining
- Connection Termination (FIN, FIN-ACK, ACK)

## 🚀 Getting Started

### Requirements

- Python 3.x

### Run Sender

```bash
python sender.py <receiver_ip> <port> <file_to_send>
