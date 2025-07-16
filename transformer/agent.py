import datetime
from typing import Any, Dict, List

import pandas as pd


class Agent:

    COLUMNS = [
        "symbol:ticker",
        "name",
        "currency",
        "Exchange:exchange",
        "Primary Exchange:primary_exchange",
        "Contract Type:contract_type",
        "Country/Region:country",
        "Closing Price:closing_price",
        "Conid:conid",
        "ISIN:isin",
        "ASSETID:assetid",
    ]

    def __init__(self, data: List[Dict[str, Any]]):
        self.data = list(data.values())

    def transform(self, table: str = "ext4_tickers") -> pd.DataFrame:
        """Return a cleaned DataFrame for *table* with a single timestamp column."""
        mapping = self.COLUMNS
        rows = [self._parse_row(r, mapping) for r in self.data]
        rows = [r for r in rows if r]
        if not rows:
            cols = [spec.split(":")[-1] for spec in mapping] + ["timestamp_created_utc"]
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame.from_records(rows)
        df["timestamp_created_utc"] = self._now_utc()
        return df

    @staticmethod
    def _now_utc() -> datetime.datetime:
        return datetime.datetime.utcnow()

    @staticmethod
    def _clean_value(value: Any) -> Any:
        if value in ("n\\a", "n/a", "", None):
            return None

        txt = str(value)
        sanitized = txt.translate(str.maketrans("", "", "E.,-+%"))
        if sanitized.isdigit():
            if "." in txt:
                if "E" in txt:
                    txt = txt.split("E")[0]
                for ch in ",+%":
                    txt = txt.replace(ch, "")
                return round(float(txt), 3)
            return float(sanitized)
        return value

    @classmethod
    def _parse_row(cls, row: Dict[str, Any], mapping: List[str]) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {}
        for spec in mapping:
            src, *dest = spec.split(":")
            dest = dest[0] if dest else src

            if src not in row:
                continue

            if dest == "ticker":
                parsed[dest] = row[src]
            else:
                parsed[dest] = cls._clean_value(row[src])
        return parsed
