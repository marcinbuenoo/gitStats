"""Generate static SVG cards for a GitHub profile README."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from api.main import general_card_svg, get_github_stats, languages_card_svg


def main() -> None:
    username = os.getenv("GITHUB_USERNAME")
    if not username:
        raise RuntimeError("GITHUB_USERNAME must be set")

    output_dir = Path(os.getenv("OUTPUT_DIR", "assets"))
    output_dir.mkdir(parents=True, exist_ok=True)
    stats = asyncio.run(get_github_stats(username))

    (output_dir / "github-stats.svg").write_text(
        general_card_svg(stats, "dark"), encoding="utf-8"
    )
    (output_dir / "github-languages.svg").write_text(
        languages_card_svg(stats, "dark"), encoding="utf-8"
    )


if __name__ == "__main__":
    main()