from __future__ import annotations
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "function.zip"
SRC = HERE / "src"

def main() -> None:
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in SRC.rglob("*"):
            if p.is_file():
                z.write(p, arcname=p.relative_to(SRC))
    print(str(OUT))

if __name__ == "__main__":
    main()
