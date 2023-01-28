from pathlib import Path

from lib.util import read_file


def project_root() -> Path:
    """Find the project root directory by locating pyproject.toml."""
    current_file = Path(__file__)
    for parent_directory in current_file.parents:
        if (parent_directory / "pyproject.toml").is_file():
            return parent_directory
    raise FileNotFoundError("Could not find project root containing pyproject.toml")


def get_version():
    try:
        # Probably this is the pyproject.toml of a development install
        path_to_pyproject_toml = project_root() / "pyproject.toml"
    except FileNotFoundError:
        # Probably not a development install
        path_to_pyproject_toml = None

    if path_to_pyproject_toml is not None:
        content = read_file(path_to_pyproject_toml)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("version = "):
                version = line.replace("version = ", "").replace("\"", "")
                return version
    return "0.0.0"
