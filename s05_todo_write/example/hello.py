#!/usr/bin/env python3
"""A tiny program that greets someone by name."""


def greet(name: str) -> None:
    """Print a greeting addressed to the given name.

    Args:
        name: The person to greet.
    """
    message = "Hello, " + name
    print(message)


def main() -> None:
    """Greet the default user."""
    greet("Claude")


if __name__ == "__main__":
    main()
