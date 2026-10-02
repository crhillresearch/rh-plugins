from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_all_package_python_sources_compile():
    paths=sorted(p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts)
    assert paths
    for path in paths: compile(path.read_text(encoding="utf-8"),str(path),"exec")
