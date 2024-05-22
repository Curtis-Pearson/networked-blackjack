import errno
import socket
import threading
import queue
import time
from Encryption import Cipher


""" Client Related Stuff """


class Client:
    # Create a Client OBJECT
    def __init__(self, host="127.0.0.1", port=50001):
        self.HOST = host
        self.PORT = port
        # Buffers responsible for storing Incoming and Outgoing messages
        self.InputBuffer = queue.Queue()
        self.OutputBuffer = queue.Queue()
        # Booleans for loops
        self.Running = True
        self.Writing = True
        self.Reading = True
        self.Processing = True
        # Connection information
        self.Conn = None
        # Threads used to run read/write asynchronously
        self.ReadThread = threading.Thread(target=self.read)
        self.WriteThread = threading.Thread(target=self.write)

    # Write THREAD function
    def write(self):
        print("Writing Thread Started")
        while self.Writing:
            # Client has stopped and all messages have been sent
            if not self.Running and self.OutputBuffer.empty():
                self.Writing = False
            # Messages still remain in the Output BUFFER to send
            if not self.OutputBuffer.empty():
                # Encrypt data
                data = Cipher.cipher(self.OutputBuffer.get(), True)
                self.Conn.sendall(data.encode("utf-8"))
                # Ensures messages are sent to the Server incase the Socket is closed
                time.sleep(0.1)

    # Read THREAD function
    def read(self):
        print("Reading Thread Started")
        # Create the Client Socket Interface to connect to the Server Socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.Conn:
            self.Conn.connect((self.HOST, self.PORT))
            # Prevent blocking
            self.Conn.setblocking(False)

            while self.Reading:
                if not self.Running:
                    self.Reading = False
                    break

                # Socket has activity
                try:
                    # Receive data from Server
                    data = self.Conn.recv(1024)
                    if data:
                        # Decrypt data
                        message = Cipher.cipher(data.decode("utf-8"), False)
                        # Add it to the Input BUFFER
                        self.InputBuffer.put(message)

                # Socket is inactive
                except socket.error as e:
                    err = e.args[0]
                    # Either repeated inactivity or actions would cause blocking
                    if err in [errno.EAGAIN, errno.EWOULDBLOCK]:
                        time.sleep(0.1)
                    # Socket has closed
                    else:
                        self.Running = False
                        self.Conn.shutdown(socket.SHUT_RDWR)

    # Main function
    # Start the Read and Write THREADS
    def process(self):
        # Run whilst Client SCRIPT is still running
        try:
            self.ReadThread.start()
            self.WriteThread.start()

            # Main loop
            while self.Running:
                # Receive messages from Server
                message = self.get_message()

                # Message exists means Server is still alive
                if message:

                    # Split the message into separate messages
                    messages = message.split("||")
                    for msg in messages:

                        # "OUTPUT" means Server sent Message for the Client to Output without requesting for a Response
                        if msg.startswith("OUTPUT"):
                            print(msg[7:])

                        # "INPUT" means Server requests an Input from the Client based on the contents of the Message
                        elif msg.startswith("INPUT"):
                            response = input(msg[6:])
                            if response.lower() == "quit":
                                self.push_message(response)
                                self.Running = False
                            else:
                                self.push_message(response)
        # Client SCRIPT was forcefully closed
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt: Shutting down!")
        # Stop the Client THREADS
        finally:
            self.quit()

    # Get messages from the Input BUFFER
    def get_message(self):
        # BUFFER has data
        if not self.InputBuffer.empty():
            return self.InputBuffer.get()
        else:
            return None

    # Put message in the Output BUFFER
    def push_message(self, message):
        self.OutputBuffer.put(message)

    # Stop the main loop and both THREADS
    def quit(self):
        self.Running = False
        self.ReadThread.join()
        self.WriteThread.join()


# Entry to the SCRIPT
if __name__ == "__main__":
    client = Client()
    client.process()
