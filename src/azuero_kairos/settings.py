"""Project settings for the Azuero Kairós scaffold."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ProjectSettings:
    """Filesystem settings used by future reproducible scripts."""

    environment: str = "development"
    aoi_config_dir: Path = PROJECT_ROOT / "configs"
    output_dir: Path = PROJECT_ROOT / "outputs"
    official_dates_config: Path = PROJECT_ROOT / "configs" / "dates_official.yaml"


def load_settings() -> ProjectSettings:
    """Load settings from environment variables with repository defaults."""

    return ProjectSettings(
        environment=os.getenv("AZUERO_KAIROS_ENV", "development"),
        aoi_config_dir=Path(os.getenv("AOI_CONFIG_DIR", PROJECT_ROOT / "configs")),
        output_dir=Path(os.getenv("OUTPUT_DIR", PROJECT_ROOT / "outputs")),
        official_dates_config=Path(
            os.getenv(
                "OFFICIAL_DATES_CONFIG",
                PROJECT_ROOT / "configs" / "dates_official.yaml",
            )
        ),
    )
