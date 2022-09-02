import threading
import socket


class Server:
    def __init__(self):
        self.sock = socket.socket()
        self.launched = False
        self.package_handler = None
        self.clients = dict()
        self.client_connection_thread = None

    def __listening_to_client(self, connection, address):
        while self.launched and address in self.clients:
            try:
                length = int.from_bytes(connection.recv(4), byteorder="little")
                data = connection.recv(length)
            except Exception as error:
                if self.launched and type(error) != ConnectionResetError:
                    print('An error while listening to the client.\nDescription:\n' + str(error) + '\n')
                break

            self.package_handler(address, data, self)
        connection.close()
        self.clients.pop(address, 0)

    def __client_connection(self):
        while self.launched:
            try:
                connection, address = self.sock.accept()
            except Exception as error:
                if self.launched:
                    print('An error while client connection.\nDescription:\n' + str(error) + '\n')
                break

            if address in self.clients:
                continue

            self.clients[address] = {'connection': connection, 'thread': None}
            client_thread = threading.Thread(target=self.__listening_to_client, args=(connection, address), daemon=True)
            client_thread.start()
            self.clients[address]['thread'] = client_thread

    def send(self, address, data):
        if not self.launched or address not in self.clients:
            return False

        try:
            self.clients[address]['connection'].send(len(data).to_bytes(4, byteorder="little"))
            self.clients[address]['connection'].send(data)
            return True
        except Exception as error:
            if type(error) != ConnectionResetError:
                print('An error while sending the package.\nDescription:\n' + str(error) + '\n')

            self.clients[address]['connection'].close()
            self.clients.pop(address, 0)
            return False

    def send_all(self, data):
        if not self.launched:
            return 0

        count = 0
        for address in self.clients:
            count += self.send(address, data)

        return count

    def run(self, package_handler, port=1024, listen_count=1):
        if self.launched:
            return

        self.launched = True
        self.package_handler = package_handler
        self.sock.bind(('', port))
        self.sock.listen(listen_count)

        self.client_connection_thread = threading.Thread(target=self.__client_connection, daemon=True)
        self.client_connection_thread.start()

    def stop(self):
        if not self.launched:
            return

        self.launched = False
        self.sock.close()
        self.client_connection_thread.join()
        for address in list(self.clients.keys()):
            self.clients[address]['connection'].close()
            self.clients[address]['thread'].join()
        self.clients.clear()


if __name__ == '__main__':
    def package_handler(cur_address, data, cur_server):
        for address in list(cur_server.clients.keys()):
            cur_server.send(address, data.upper())

    server = Server()
    server.run(package_handler)

    while server.launched:
        string = input()
        if string == "!stop":
            server.stop()

        server.send_all(string.encode())
