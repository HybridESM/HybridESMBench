"""Make ESMValTool metadata.yml files HybridESMBench-compatible."""

from pathlib import Path


def main() -> None:
    """Make ESMValTool metadata.yml files HybridESMBench-compatible."""
    all_metadata_files = Path(__file__).parent.rglob("metadata.yml")
    for metadata_file in all_metadata_files:
        print(f"Reading {metadata_file}")
        metadata = metadata_file.read_text(encoding="utf-8")
        first_file_path = Path(metadata.split("\n")[0].replace("? ", ""))
        if not first_file_path.is_absolute():
            print("   -> Skipping (already converted)")
            continue
        root = f"{first_file_path.parents[1]}/"
        new_metadata = metadata.replace(root, "")
        metadata_file.write_text(new_metadata, encoding="utf-8")
        print("   -> Converted")


if __name__ == "__main__":
    main()
