# sender.py
import struct
import socket
import threading
import time
import random
from packet import create_packet, parse_packet, SYN, ACK, FIN

# Configuration
SENDER_IP = '127.0.0.1'
SENDER_PORT = 10003
RECEIVER_IP = '127.0.0.1'
RECEIVER_PORT = 10002
LOSS_PROB = 0.1 # 10% packet loss
TIMEOUT = 0.5  # seconds
MAX_SEQ_NUM = 2**32

# Sliding Window Parameters
WINDOW_SIZE = 2  # Initial window size
MSS = 1024  # Maximum Segment Size

class Sender:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((SENDER_IP, SENDER_PORT))
        self.socket.settimeout(TIMEOUT)
        self.lock = threading.Lock()
        
        # Connection variables
        self.seq_num = 0
        self.ack_num = 0
        self.connected = False
        
        # Sliding window
        self.base = 0 # Base of the window
        self.next_seq_num = 0
        self.window_size = WINDOW_SIZE
        self.cwnd = 1  # Congestion window
        self.ssthresh = 16  # Slow start threshold
        self.duplicate_ack_count = 0
        
        # Buffer for sent but not yet acknowledged packets
        self.buffer = {}
        
        # Event to stop the sender
        self.stop_event = threading.Event()

    def simulate_loss(self):
        return random.random() < LOSS_PROB

    def send_packet(self, packet):
        if not self.simulate_loss():
            self.socket.sendto(packet, (RECEIVER_IP, RECEIVER_PORT))
            #print(f"Sent packet with seq_num={struct.unpack('!I', packet[:4])[0]}")
        else:
            print(f"Simulated loss of packet with seq_num={struct.unpack('!I', packet[:4])[0]}")

    def handshake(self):
        # Send SYN
        syn_packet = create_packet(self.base, 0, SYN, self.window_size)
        self.send_packet(syn_packet)
        print("Sent SYN")
        
        #build the ack packet
        ack_packet = create_packet(1, 0, ACK, self.window_size)

        while not self.connected:
            try:
                data, addr = self.socket.recvfrom(1024)
                recv_seq, recv_ack, flags, window, _ = parse_packet(data)
                #if flags & SYN and flags & ACK:
                if flags == SYN | ACK:
                    # Send ACK
                    self.send_packet(ack_packet)
                    print("Received SYN-ACK, sent ACK")
                    self.connected = True
                    print("Handshake completed")
            except socket.timeout:
                print("Handshake timeout, resending SYN")
                self.send_packet(syn_packet)

    def send_data(self, data):
        total_packets = (len(data) + MSS -1) // MSS
        packets = [data[i*MSS:(i+1)*MSS] for i in range(total_packets)]
        num_packets = len(packets)
        last_ack_num = 1
        
        while self.base < num_packets:
            self.lock.acquire()
            # Send packets in the window, must at least send one packet
            print("#Start of window")
            packet_send_in_windows = 0
            print(f"base: {self.base}, next_seq_num: {self.next_seq_num}")
            #while self.next_seq_num <= self.base + max(self.cwnd, self.window_size) and self.next_seq_num < num_packets:
            # send winodws size number of packets at a time
            # will send 5 packets at the beginning
            for i in range(self.base, min(self.base + self.window_size, num_packets)):
                packet_data = packets[i]
                packet = create_packet(i+2, 0, 0, self.window_size, packet_data)
                self.buffer[i] = (packet, time.time())
                self.send_packet(packet)
                #self.next_seq_num += 1
                packet_send_in_windows += 1
            print(f"#End of window, sent {packet_send_in_windows} packets")
            self.lock.release()
            
            # wait for acks for the packets sent in the window
            # ack num for the first data packet is 2
            # self_base is 0, so the first packet is 2
            success_windows = True
            try:
                # expected windows sieze number of acks

                for i in range(packet_send_in_windows):

                    data_recv, addr = self.socket.recvfrom(1024)
                    recv_seq, recv_ack, flags, window, _ = parse_packet(data_recv)

                    if flags & ACK:
                        self.lock.acquire()
                        last_ack_num = recv_ack
                        # Correct ack received
                        if recv_ack == self.base+2:
                            # everying before the ack has been correctly received
                            #print(f"Received correct ACK for seq_num={recv_ack}")
                            # bump the base to the next ack since everything before it has been acked
                            self.base+=1
                            self.duplicate_ack_count = 0
                        # Incorrect ack received
                        else:
                            #print(f"Received incorect ACK, server comfirm the last correct ack num is {recv_ack}")
                            self.base = recv_ack-2
                            success_windows = False
                        self.lock.release()
            except socket.timeout:
                self.lock.acquire()
                print("Timeout occurred, decrease the windows size and retransmitting all packets in window")
                self.window_size = max(2, (int)(self.window_size/2))
                self.lock.release()

        
            #if every packet in the window has been acked, increase the window size
            if success_windows:
                self.window_size= min(self.window_size**2, (int)(655350/MSS))
                print(f"Received all ACKs in window, increase window size to {self.window_size}")
            else:
                self.window_size = max(2, (int)(self.window_size/2))
                print(f"Lost packet occured in the window, decrease window size to {self.window_size}")

    def teardown(self):
        # Send FIN
        fin_packet = create_packet(self.base+2, 0, FIN, self.window_size)
        self.send_packet(fin_packet)
        #self.socket.sendto(fin_packet, (RECEIVER_IP, RECEIVER_PORT))
        print(f"Sent FIN with seq_num={self.base+2}")
        
        fin_send_time = time.time()
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                recv_seq, recv_ack, flags, window, _ = parse_packet(data)
                #print(f"Received ACK for FIN, ack_num={recv_ack}, condiction: {self.base+3}")
                if flags == FIN|ACK and recv_ack == self.base+2:
                    print("Received FIN ACK, sending ACK to close connection")
                    break
            except socket.timeout:
                print("FIN timeout, resending FIN")
                self.send_packet(fin_packet)

        self.socket.settimeout(5)
        # Send ACK for FIN ACK
        ack_packet = create_packet(self.base+3, 0, ACK, self.window_size)
        self.send_packet(ack_packet)

        timeout_count = 0
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                recv_seq, recv_ack, flags, window, _ = parse_packet(data)
                if flags == ACK and recv_ack == self.base+3:
                    print("Received ACK for FIN ACK, closing connection")
                    break
                else:
                    print("Waiting for ACK to close connection, Resending ACK")
                    self.send_packet(ack_packet)
            except socket.timeout:
                if timeout_count == 5:
                    print("Timeout limit reached, closing connection")
                    break
                timeout_count += 1
                print("timeout, resending ACK")
                self.send_packet(ack_packet)
            except Exception as e:
                print(f"Remote host closed the connection")
                break        
    

        
    def run(self, data):
        # Handshake first
        self.handshake()
        # After receiving ACK for SYN-ACK, send data
        self.send_data(data)
        # After sending all data, teardown the connection by sending FIN
        self.teardown()
        # Stop the sender
        self.socket.close()

if __name__ == "__main__":
    sender = Sender()
    # Example data to send
    data = b'This is a test message to demonstrate a custom reliable transport protocol implementation over UDP.' * 100

    #load a file
    # with open("tor-browser-windows-x86_64-portable-14.0.2.exe", "rb") as f:
    #     data = f.read()
    
    sender.run(data)
