from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from controller.calculator_controller import CalculatorController


class Router(BaseHTTPRequestHandler):
    def do_GET(self):
        controller = CalculatorController()
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_components = parse_qs(parsed_path.query)

        if path == "/":
            self.handle_root_path()
        elif path == "/add":
            self.handle_addition(query_components, controller)
        elif path == "/multiply":
            self.handle_multiplication(query_components, controller)
        else:
            self.send_error(404, "File Not Found: {}".format(self.path))

    def handle_root_path(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Welcome to the Python Calculator API!")

    def handle_addition(self, query_components, controller):
        try:
            a, b = int(query_components["a"][0]), int(query_components["b"][0])
            result = controller.add(a, b)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(str(result), "utf8"))
        except (ValueError, KeyError):
            self.send_error(400, "Bad Request: Invalid parameters for addition.")

    def handle_multiplication(self, query_components, controller):
        try:
            a, b = int(query_components["a"][0]), int(query_components["b"][0])
            result = controller.multiply(a, b)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(str(result), "utf8"))
        except (ValueError, KeyError):
            self.send_error(400, "Bad Request: Invalid parameters for multiplication.")
