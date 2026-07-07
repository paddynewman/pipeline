import os

from .web import run


def main():
    host = os.getenv("PIPELINE_HOST", "0.0.0.0")
    port = int(os.getenv("PIPELINE_PORT", "8080"))
    debug = os.getenv("PIPELINE_DEBUG", "false").lower() == "true"
    run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
