import argparse

from .server import run_server


def main():
    parser = argparse.ArgumentParser(description="Pipeline automation server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to listen on (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to listen on (default: 8080)"
    )
    parser.add_argument(
        "--data", default="./data", help="Data directory (default: ./data)"
    )
    args = parser.parse_args()
    run_server(args.host, args.port, args.data)


if __name__ == "__main__":
    main()
