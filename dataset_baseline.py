import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET_RELATIVE_PATH = "data/geohazard_news_final_20261101T150501Z.csv"
DATASET_PATH = ROOT / DATASET_RELATIVE_PATH
PRIMARY_DATASET_PATH = DATASET_PATH
DATASET_SHA256 = "be4fffc3cc7a72b008154e9663153b6bb96545f21420a3aded37209490a3eb06"
DATASET_ROWS = 787
DATASET_COLUMNS = 51
FINALIZED_AT = "2026-11-01T15:05:01Z"


def file_sha256(path=DATASET_PATH):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_dataset(path=DATASET_PATH):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset final tidak ditemukan: {path}")

    digest = file_sha256(path)
    if digest != DATASET_SHA256:
        raise ValueError(
            f"Hash dataset final tidak cocok: {digest} != {DATASET_SHA256}"
        )

    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError("Dataset final kosong") from exc
        row_count = sum(1 for _ in reader)

    if len(header) != DATASET_COLUMNS:
        raise ValueError(
            f"Jumlah kolom tidak cocok: {len(header)} != {DATASET_COLUMNS}"
        )
    if row_count != DATASET_ROWS:
        raise ValueError(
            f"Jumlah baris tidak cocok: {row_count} != {DATASET_ROWS}"
        )

    return {
        "path": str(path),
        "sha256": digest,
        "rows": row_count,
        "columns": len(header),
        "finalized_at": FINALIZED_AT,
    }


if __name__ == "__main__":
    print(verify_dataset())
