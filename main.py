from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import os
import socket
import json
from datetime import datetime
import threading

BASE_DIR = os.getcwd()


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        print(pr_url)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')
        elif pr_url.path == '/style.css':
            self.send_static()
        elif pr_url.path == '/logo.png':
            self.send_static()
        else:
            self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        file_path = os.path.join(BASE_DIR, self.path[1:])
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)

        if self.path == '/message':
            self.send_response(302)

            self.end_headers()

            socket_connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_connection.sendto(json.dumps(parsed_data).encode(), ('localhost', 5000))

            self.wfile.write(b'Message received, thank you!')
        else:
            self.send_error(404)


class SocketServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(('localhost', 5000))

    def receive_data(self):
        while True:
            data, _ = self.server.recvfrom(1024)
            message = json.loads(data.decode())
            self.save_message(message)

    def save_message(self, message):
        file_path = os.path.join(BASE_DIR, 'storage', 'data.json')
        try:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                with open(file_path, 'r') as file:
                    data = json.load(file)
            else:
                data = {}

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            data[timestamp] = message

            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print(f"Error occurred: {e}")

    def run_server(self):
        self.receive_data()


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    socket_server = SocketServer()
    socket_thread = threading.Thread(target=socket_server.run_server)
    socket_thread.start()

    run_http_server()
