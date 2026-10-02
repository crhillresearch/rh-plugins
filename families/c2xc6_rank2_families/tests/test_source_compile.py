from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_package_python_sources_compile():
    sources = sorted(
        path
        for path in ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    assert sources
    for path in sources:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
