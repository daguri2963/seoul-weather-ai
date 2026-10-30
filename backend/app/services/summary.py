from statistics import mean


def summarize(rows: list[dict]) -> dict:
    ordered = sorted(rows, key=lambda row: row["date"])
    if not ordered:
        return {"period": None, "count": 0, "unit": "°C", "metrics": {"average": None, "max": None, "min": None}, "trend": "자료 없음", "recent_change_c": None}
    values = [float(row["value"]) for row in ordered]
    window = min(7, len(values) // 2)
    change = round(mean(values[-window:]) - mean(values[-2 * window:-window]), 2) if window else None
    trend = "자료 부족" if change is None else ("상승" if change > 0.5 else "하락" if change < -0.5 else "보합")
    return {
        "period": f'{ordered[0]["date"]} ~ {ordered[-1]["date"]}',
        "count": len(values), "unit": "°C",
        "metrics": {"average": round(mean(values), 2), "max": max(values), "min": min(values)},
        "trend": trend, "recent_change_c": change,
    }
