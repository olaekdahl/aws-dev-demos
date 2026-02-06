"""Colored, structured terminal output for demos."""
import json
import sys

BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RESET = "\033[0m"


def banner(module: str, title: str):
    """Print a prominent section banner."""
    width = 60
    print(f"\n{BOLD}{CYAN}{'=' * width}")
    print(f"  {module} | {title}")
    print(f"{'=' * width}{RESET}\n")


def step(n: int, description: str):
    """Print a numbered step header."""
    print(f"\n{BOLD}{MAGENTA}[Step {n}]{RESET} {description}")
    print(f"{DIM}{'-' * 50}{RESET}")


def success(message: str):
    """Print a green success message."""
    print(f"  {GREEN}OK{RESET}  {message}")


def fail(message: str):
    """Print a red failure message."""
    print(f"  {RED}FAIL{RESET}  {message}", file=sys.stderr)


def info(message: str):
    """Print a dimmed info message."""
    print(f"  {DIM}{message}{RESET}")


def warn(message: str):
    """Print a yellow warning message."""
    print(f"  {YELLOW}WARN{RESET}  {message}")


def header(text: str):
    """Print a bold blue header."""
    print(f"\n{BOLD}{BLUE}{text}{RESET}")


def kv(key: str, value):
    """Print a key-value pair."""
    print(f"  {BOLD}{key}:{RESET} {value}")


def json_print(data, indent: int = 2):
    """Pretty-print a dict as JSON."""
    print(json.dumps(data, indent=indent, default=str))


def table(headers: list[str], rows: list[list], col_width: int = 18):
    """Print a simple ASCII table."""
    fmt = "  ".join(f"{{:<{col_width}}}" for _ in headers)
    print(f"\n{BOLD}{fmt.format(*headers)}{RESET}")
    print(f"  {'  '.join(['-' * col_width] * len(headers))}")
    for row in rows:
        cells = [str(c)[:col_width] for c in row]
        while len(cells) < len(headers):
            cells.append("")
        print(f"  {fmt.format(*cells)}")
    print()


def progress_bar(current: int, total: int, width: int = 40, label: str = ""):
    """Print an in-place progress bar."""
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = f"[{'#' * filled}{'.' * (width - filled)}] {current}/{total}"
    suffix = f" {label}" if label else ""
    print(f"\r  {bar}{suffix}", end="" if current < total else "\n", flush=True)
