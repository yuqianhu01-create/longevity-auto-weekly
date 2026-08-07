"""Deprecated helper.

The current GitHub Pages entrypoint is docs/index.html. Its UI labels are
stored there with ASCII-safe Unicode escapes so Windows console encoding cannot
corrupt Chinese copy. This script intentionally does not rewrite the frontend.
"""


def main() -> None:
    print("Frontend copy is managed in docs/index.html; nothing to refresh.")


if __name__ == "__main__":
    main()
