# receiver.py
import struct
import socket
import threading
import time
import random
from packet import create_packet, parse_packet, SYN, ACK, FIN

# Configuration
RECEIVER_IP = '127.0.0.1'
RECEIVER_PORT = 10002
SENDER_IP = '127.0.0.1'
SENDER_PORT = 10003
LOSS_PROB = 0.1  # 10% packet loss

class Receiver:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((RECEIVER_IP, RECEIVER_PORT))
        self.expected_seq = 0
        self.window_size = 5
        self.received_data = {}
        self.lock = threading.Lock()
        self.connected = False
        self.global_addr = None

    def simulate_loss(self):
        return random.random() < LOSS_PROB

    def send_packet(self, packet, addr):
        recv_seq, recv_ack, flags, window, payload = parse_packet(packet)
        if not self.simulate_loss():
            self.socket.sendto(packet, addr)
            if len(packet) >= 4:
                #print(f"Sent ACK for seq_num={recv_ack}")
                return
            else:
                print("Packet too short to unpack seq_num")
        else:
            print(f"Simulated loss of ACK for seq_num={recv_ack}")

    def handshake(self):
        while True:
            data, addr = self.socket.recvfrom(1024)
            self.global_addr = addr
            recv_seq, recv_ack, flags, window, _ = parse_packet(data)
            if flags & SYN:
                # Send SYN-ACK
                syn_ack_packet = create_packet(self.expected_seq, recv_ack, SYN | ACK, self.window_size)
                self.send_packet(syn_ack_packet, addr)
                print("Received SYN, sent SYN-ACK")
                break

        while not self.connected:
            try:
                data, addr = self.socket.recvfrom(1024)
                recv_seq, recv_ack, flags, window, _ = parse_packet(data)
                if recv_seq >= 1:
                    self.connected = True
                    # next seq should be 2
                    self.expected_seq = 2
                    print("Handshake completed")
                    return
                else:
                    print("Waiting for ACK to complete handshake")
                    self.send_packet(syn_ack_packet, addr)
            except socket.timeout:
                print("Waiting for ACK to complete handshake resend SYN-ACK")
                self.send_packet(syn_ack_packet, addr)

        
    def receive_data(self):
        # 0 and 1 are reserved for handshake
        self.expected_seq = 2
        
        while True:
            try:
                data, addr = self.socket.recvfrom(2048)
                recv_seq, recv_ack, flags, window, payload = parse_packet(data)
                
                if flags & FIN and recv_seq == self.expected_seq:
                    # return so that the next function can be called
                    return


                # In order packet received, imply everying before this packet has been received
                if recv_seq == self.expected_seq:
                    #print(f"Received expected packet seq_num={recv_seq}")
                    self.received_data[recv_seq] = payload
                    # Send ACK
                    ack_packet = create_packet(0, self.expected_seq, ACK, self.window_size)
                    self.send_packet(ack_packet, addr)
                    # Move to the next expected packet
                    self.expected_seq +=1
                # Incorrect packet received, send last correct ACK
                else:
                    #print(f"Received out-of-order packet seq_num={recv_seq}, expected={self.expected_seq}")
                    # Resend ACK for the last in-order packet
                    ack_packet = create_packet(0, self.expected_seq-1, ACK, self.window_size)
                    self.send_packet(ack_packet, addr)

            except Exception as e:
                print(f"Error: {e}")
                break
    
    def close_connection(self):
        # Send FIN ACK
        fin_packet = create_packet(0, self.expected_seq, FIN | ACK, self.window_size)
        self.send_packet(fin_packet, self.global_addr)
        print(f"Recvied FIN, Sent FIN ACK with seq_num={self.expected_seq}")
        self.expected_seq += 1

        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                recv_seq, recv_ack, flags, window, _ = parse_packet(data)
                if flags & ACK and recv_seq == self.expected_seq:
                    print("Received ACK, closing connection")
                    break
                else:
                    print(f"Not received ACK, resending FIN ACK")
                    self.send_packet(fin_packet, addr)
                
            except socket.timeout:
                print("Waiting for ACK to close connection, Resending FIN ACK")
                self.send_packet(fin_packet, addr)

    def run(self):
        self.socket.settimeout(5)
        self.handshake()
        self.receive_data()
        self.close_connection()
        print("Received all data")
        self.socket.close()

if __name__ == "__main__":
    receiver = Receiver()
    receiver.run()
