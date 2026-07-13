from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_source_visible_non_open_source_boundary_is_explicit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    legal_status = (ROOT / "docs" / "LEGAL_STATUS.md").read_text(encoding="utf-8")

    assert "[Legal Status](docs/LEGAL_STATUS.md)" in readme
    assert "no project-level open-source license" in readme
    assert "no additional" in readme
    assert "beyond the GitHub Terms, applicable law" in readme
    assert "is **not** offered as an open-source project" in legal_status
    assert "grants no **additional** copyright" in legal_status
    assert "The absence of a root license is deliberate" in legal_status

    root_license_stems = ("copying", "licence", "license", "unlicense")

    def is_license_like(path: Path) -> bool:
        name = path.name.casefold()
        if name == "licenses" and path.is_dir():
            return True
        return any(
            name == stem
            or name.startswith(f"{stem}.")
            or name.startswith(f"{stem}-")
            or name.startswith(f"{stem}_")
            for stem in root_license_stems
        )

    present = sorted(
        path.name
        for path in ROOT.iterdir()
        if is_license_like(path)
    )
    assert present == [], (
        "a root license was added without updating the explicit legal-status "
        f"boundary: {present}"
    )
