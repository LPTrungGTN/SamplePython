from http.server import HTTPServer
from router.routes import Router
import argparse


def run(server_class=HTTPServer, handler_class=Router, addr="localhost", port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Specify the host to run the HTTP server on. Default is localhost.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Specify the port to run the HTTP server on. Default is 8000.",
    )
    args = parser.parse_args()
    run(addr=args.host, port=args.port)
