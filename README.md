# 📡 PRTP - Pipelined Reliable Transfer Protocol over UDP

PRTP is a custom implementation of a reliable, pipelined transport protocol built on top of UDP. It replicates essential TCP features such as connection establishment (3-way handshake), reliable and ordered delivery, pipelining with a sliding window, flow/congestion control, fairness, and graceful connection teardown — all while simulating packet loss and bit corruption scenarios.


## 🛠 Features

- ✅ Connection-Oriented (SYN, SYN-ACK, ACK)
- 📦 Reliable Data Transfer (ACK-based, retransmission)
- 🚀 Pipelined Transfer (sliding window)
- 🧠 Flow Control & Congestion Handling (adaptive window size)
- ⚖️ Fairness (window-based congestion control per session)
- 🔁 Graceful Connection Termination (FIN, FIN-ACK, ACK)
- 💥 Simulated Packet Loss (10% configurable)


## 📁 File Structure

├── sender.py # Sender: manages connection, sliding window, retransmission <br />
├── receiver.py # Receiver: handles connection setup, ACKs, data assembly <br />
├── packet.py # Packet utility: packet creation/parsing with headers<br />
├── README.md # This file<br />



## 📦 Packet Format

Each PRTP packet contains:

| Field            | Size          | Description                                  |
|------------------|---------------|----------------------------------------------|
| Packet Type      | 1 byte        | Flags: `SYN=0x1`, `ACK=0x2`, `FIN=0x4`        |
| Sequence Number  | 4 bytes       | Cumulative sequence number                   |
| Checksum         | 2 bytes       | Error detection for header and payload       |
| Window Size      | 2 bytes       | Receiver's advertised window size            |
| Payload          | ≤ 1024 bytes  | Data (optional, max 1024 bytes)              |



## 🚀 Getting Started

### Prerequisites

- Python 3.6+
- No external libraries required (uses `socket`, `struct`, `threading`, `random`)

## ▶️ Running the Protocol

### Step 1: Start the Receiver

In one terminal, run:

```
python receiver.py
```
This will:

- Bind to 127.0.0.1:10002

- Wait for a SYN to start the handshake

- Receive pipelined data with simulated loss

- Send ACKs and handle FIN gracefully

### Step 2: Start the Sender
In another terminal:

```
python sender.py
```

This will:

- Initiate the handshake with a SYN

- Send test data (or a file if you uncomment the file loading section)

- Dynamically adjust window size based on ACKs/losses

- Perform graceful teardown with FIN

## ⚙️ Configuration
Inside sender.py and receiver.py, you can customize:

```
LOSS_PROB = 0.1  # Simulated 10% packet loss
WINDOW_SIZE = 2  # Initial sliding window size
MSS = 1024       # Maximum Segment Size in bytes
TIMEOUT = 0.5    # ACK wait timeout in seconds
```
## 📄 Example Output
You’ll see logs like:

```
Sent SYN
Received SYN-ACK, sent ACK
#Start of window
base: 0, next_seq_num: 0
#End of window, sent 2 packets
Received all ACKs in window, increase window size to 4
...
Recvied FIN, Sent FIN ACK with seq_num=202
Received ACK, closing connection
```
## 🧪 Simulating File Transfer
To send a real file:

Uncomment the following in sender.py:

```
with open("filename.ext", "rb") as f:
    data = f.read()
```

Then run sender.py to transmit the file contents over the custom PRTP.

## ⚖️ Fairness & Congestion Control

PRTP incorporates a basic fairness and congestion control mechanism inspired by TCP’s congestion avoidance techniques. It ensures that no single connection can dominate the available bandwidth, making it suitable for environments with multiple concurrent PRTP sessions.

### How Fairness Is Achieved

- 📈 **Exponential growth** of the sliding window on successful transmissions (mimics TCP slow start).
- 📉 **Multiplicative decrease** when packet loss or timeout is detected (similar to TCP congestion avoidance).
- 📊 **Window-based flow control** dynamically adjusts sending rate to adapt to network feedback.
- 🚦 **Session-aware congestion response**, ensuring aggressive connections are throttled naturally.

These strategies help PRTP maintain fair bandwidth allocation between multiple concurrent senders.

### ✅ Fairness Evaluation

To verify PRTP’s fairness, we ran an experiment between two geographically separate machines:

- **Setup**:
  - Sender/Receiver 1 runs on a laptop connected to a dorm network (bandwidth-limited to ~30 Mbps).
  - Sender/Receiver 2 runs on a remote virtual machine in Seattle.
  - The bottleneck bandwidth is intentionally capped to test bandwidth sharing under contention.

- **Observation**:
  - From 0 to ~60 seconds: Only Sender 1 is active, transmitting ~7,500 packets/sec.
  - After 60 seconds: Sender 2 starts, and both senders stabilize to roughly ~3,500 packets/sec each.

- **Conclusion**:
  - The total bandwidth is evenly shared between the two sessions.
  - PRTP dynamically adjusted window sizes and sending rates to accommodate both flows.
  - This demonstrates that PRTP achieves **fairness** under realistic network constraints.

![image](https://github.com/user-attachments/assets/1fea34a1-4544-4e26-a97f-135bc099f146)





## 📄 License
This project is open-sourced under the MIT License.

## 🤝 Contribution
Pull requests, issue reports, and enhancements are welcome! If you build on top of PRTP, feel free to fork and share your extensions.

Built for educational purposes to simulate TCP-like behavior using UDP.
