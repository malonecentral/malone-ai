import asyncio
import sys


def main():
    from malone.app import MaloneApp

    app = MaloneApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nMalone shutting down. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
