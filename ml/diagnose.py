import pandas as pd

CSV = "data/raw/TIA-WEATHER-DATA-2015-01-01-TO-2025-06-30.csv"

df = pd.read_csv(CSV)

print("=" * 60)
print("COLUMNS")
print("=" * 60)
print(list(df.columns))
print()

print("=" * 60)
print("DESCRIBE")
print("=" * 60)
print(df.describe(include="all").T)
print()

print("=" * 60)
print("DATE RANGE")
print("=" * 60)
df["datetime"] = pd.to_datetime(df["datetime"])
print("Min:", df["datetime"].min())
print("Max:", df["datetime"].max())
print("Rows:", len(df))
print()

print("=" * 60)
print("ROWS PER YEAR")
print("=" * 60)
print(df.groupby(df["datetime"].dt.year).size())
print()

print("=" * 60)
print("ROWS PER MONTH (recent years)")
print("=" * 60)
df["ym"] = df["datetime"].dt.to_period("M")
print(df.groupby("ym").size().tail(24))
print()

print("=" * 60)
print("SAMPLE ROWS (first 5)")
print("=" * 60)
print(df.head())
print()

print("=" * 60)
print("SAMPLE ROWS (last 5)")
print("=" * 60)
print(df.tail())