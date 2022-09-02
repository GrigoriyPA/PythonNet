import threading
import socket


class Client:
    def __init__(self):
        self.sock = socket.socket()
        self.connected = False
        self.package_handler = None
        self.listening_to_server_thread = None

    def __listening_to_server(self):
        while self.connected:
            try:
                length = int.from_bytes(self.sock.recv(4), byteorder="little")
                data = self.sock.recv(length)
            except Exception as error:
                if self.connected:
                    print('An error while listening to the server.\nDescription:\n' + str(error) + '\n')
                break

            self.package_handler(data, self)
        self.connected = False
        self.sock.close()

    def send(self, data):
        if not self.connected:
            return False

        try:
            self.sock.send(len(data).to_bytes(4, byteorder="little"))
            self.sock.send(data)
            return True
        except Exception as error:
            print("Error while sending the package.\nDescription:\n" + str(error) + '\n')
            return False

    def connect(self, package_handler, server_ip, server_port):
        if self.connected:
            self.disconnect()

        if self.sock.connect_ex((server_ip, server_port)):
            print('Failed to connect to server:\n', 'ip: ', server_ip, '\nport: ', server_port, '\n\n', sep='')
            return False

        self.connected = True
        self.package_handler = package_handler

        self.listening_to_server_thread = threading.Thread(target=self.__listening_to_server, daemon=True)
        self.listening_to_server_thread.start()

        return True

    def disconnect(self):
        if not self.connected:
            return

        self.connected = False
        self.sock.close()
        self.listening_to_server_thread.join()


if __name__ == '__main__':
    def package_handler(data, cur_client):
        print('->', data.decode('UTF-8'))

    client = Client()
    client.connect(package_handler, '10.4.14.185', 1024)

    while client.connected:
        string = input()
        if string == "!stop":
            client.disconnect()

        client.send(string.encode())
