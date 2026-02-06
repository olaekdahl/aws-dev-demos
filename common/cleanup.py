"""Track created resources for automatic cleanup."""
import json
import pathlib

STATE_DIR = pathlib.Path.home() / ".aws-dev-demos-state"


def _state_file(module: str) -> pathlib.Path:
    STATE_DIR.mkdir(exist_ok=True)
    return STATE_DIR / f"{module}.json"


def track_resource(module: str, resource_type: str, identifier: str, **metadata):
    """Record a resource so cleanup can find it later."""
    path = _state_file(module)
    state = json.loads(path.read_text()) if path.exists() else []
    state.append({"type": resource_type, "id": identifier, **metadata})
    path.write_text(json.dumps(state, indent=2))


def get_tracked_resources(module: str) -> list[dict]:
    """Return all tracked resources for a module."""
    path = _state_file(module)
    return json.loads(path.read_text()) if path.exists() else []


def clear_tracked(module: str):
    """Remove the tracking file for a module."""
    path = _state_file(module)
    if path.exists():
        path.unlink()
