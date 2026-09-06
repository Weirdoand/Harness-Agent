"""A simple "Hello, World!" program demonstrating a main guard."""


def greet(name: str = "World") -> str:
    """Return a friendly greeting for the given name.

    Args:
        name: The person (or thing) to greet.

    Returns:
        A greeting string addressed to ``name``.
    """
    return f"Hello, {name}!"


def main() -> None:
    """Entry point: print the default greeting to stdout."""
    print(greet())


if __name__ == "__main__":
    main()
