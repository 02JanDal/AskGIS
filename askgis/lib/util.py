import re

TO_SNAKE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake_case(name: str) -> str:
    return TO_SNAKE_PATTERN.sub("_", name).lower()
