"""
Main entry point for the Email MCP Server.
"""
import asyncio
import sys
import argparse
from .server import run_server


def main():
    """Main function to run the Email MCP Server."""
    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')

    args = parser.parse_args()

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("Debug mode enabled")

    print(f"Starting Email MCP Server...")

    try:
        # Run the server
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nShutting down Email MCP Server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error running Email MCP Server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
