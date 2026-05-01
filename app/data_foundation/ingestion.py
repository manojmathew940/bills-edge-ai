import argparse
import csv
import gzip
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


RAW_DATA_DIR = Path("data/raw")
MIN_SEASON = 1999
MAX_COMPRESSED_BYTES = 200 * 1024 * 1024
REQUIRED_COLUMNS = {
    "game_id",
    "play_id",
    "home_team",
    "away_team",
    "posteam",
    "defteam",
    "season",
    "week",
}
PBP_URL_TEMPLATE = (
    "https://github.com/nflverse/nflverse-data/releases/download/pbp/"
    "play_by_play_{season}.csv.gz"
)


def validate_season(season: int) -> None:
    current_year = datetime.now(timezone.utc).year
    if season < MIN_SEASON or season > current_year:
        raise ValueError(
            f"Season must be between {MIN_SEASON} and {current_year}; got {season}."
        )


def validate_required_columns(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("Source file did not contain a CSV header row.")

    missing_columns = sorted(REQUIRED_COLUMNS - set(fieldnames))
    if missing_columns:
        raise ValueError(
            "Source file is missing required columns: " + ", ".join(missing_columns)
        )


def validate_content_length(content_length: str | None) -> None:
    if content_length is None:
        return

    compressed_bytes = int(content_length)
    if compressed_bytes > MAX_COMPRESSED_BYTES:
        raise ValueError(
            "Source file is larger than the configured limit: "
            f"{compressed_bytes} bytes."
        )


def write_metadata(
    metadata_path: Path,
    *,
    source_url: str,
    season: int,
    output_path: Path,
    rows_written: int,
    source_column_count: int,
) -> None:
    metadata = {
        "source": "nflverse/nflverse-data GitHub release",
        "source_url": source_url,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "season": season,
        "team": "BUF",
        "output_path": str(output_path),
        "rows_written": rows_written,
        "source_column_count": source_column_count,
        "required_columns": sorted(REQUIRED_COLUMNS),
    }

    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")


def save_raw_bills_play_by_play(
    season: int, output_dir: Path = RAW_DATA_DIR
) -> tuple[Path, int]:
    """Download one season and save raw play rows from Bills games."""
    validate_season(season)

    source_url = PBP_URL_TEMPLATE.format(season=season)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"bills_play_by_play_{season}_raw.csv.gz"
    metadata_path = output_dir / f"bills_play_by_play_{season}_raw.metadata.json"

    rows_written = 0
    with urlopen(source_url, timeout=60) as response:
        validate_content_length(response.headers.get("Content-Length"))

        with gzip.GzipFile(fileobj=response) as compressed_source:
            text_source = io.TextIOWrapper(compressed_source)
            reader = csv.DictReader(text_source)
            validate_required_columns(reader.fieldnames)

            with NamedTemporaryFile(
                "wb", dir=output_dir, prefix=f".{output_path.stem}.", delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)

            try:
                with gzip.open(temp_path, "wt", newline="") as output_file:
                    writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames)
                    writer.writeheader()

                    for row in reader:
                        if row["home_team"] == "BUF" or row["away_team"] == "BUF":
                            writer.writerow(row)
                            rows_written += 1

                temp_path.replace(output_path)
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    write_metadata(
        metadata_path,
        source_url=source_url,
        season=season,
        output_path=output_path,
        rows_written=rows_written,
        source_column_count=len(reader.fieldnames or []),
    )

    return output_path, rows_written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download raw Buffalo Bills play-by-play data for one NFL season."
    )
    parser.add_argument("season", type=int, help="NFL season to download, such as 2023")
    args = parser.parse_args()

    try:
        output_path, rows_written = save_raw_bills_play_by_play(args.season)
    except ValueError as error:
        parser.error(str(error))

    print(f"Saved {rows_written} raw Bills play rows to {output_path}")


if __name__ == "__main__":
    main()
