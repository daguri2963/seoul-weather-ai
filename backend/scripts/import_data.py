"""Import the source repository's 2024 daily official maximum temperatures."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import get_db


def main():
    source = Path(__file__).resolve().parents[2] / "data" / "temperature_daily_2024.csv"
    rows = list(csv.DictReader(source.open(encoding="utf-8-sig", newline="")))
    if len(rows) < 100:
        raise ValueError("At least 100 source points are required")
    collection = get_db().collection("data")
    count = 0
    for row in rows:
        if not row["daily_max_official_c"]:
            continue
        ref = collection.document(row["date"])
        if ref.get().exists:
            continue
        ref.set({"date": row["date"], "value": float(row["daily_max_official_c"]), "memo": "기상청 서울(108) 2024 공식 일최고기온"})
        count += 1
    print(f"Imported {count} of {len(rows)} rows. Existing dates were skipped.")


if __name__ == "__main__":
    main()
