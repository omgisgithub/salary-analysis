"""Download the Eurostat net earnings dataset (EARN_NT_NET) via the dissemination API.

Fetches only the slice the analysis needs (currency=EUR, earnings structure=NET,
~0.9 MB) instead of the full ~42 MB databrowser export, and rewrites it into the
same column layout the databrowser produces so etl.py works unchanged.

API reference: https://wikis.ec.europa.eu/display/EUROSTATHELP/API+-+Getting+started+with+statistics+API

Usage:
    python download_data.py            # writes net_earnings.csv
    python download_data.py out.csv    # writes to a custom path
"""

import sys

import pandas as pd

EARN_NT_NET_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/3.0/data/dataflow/"
    "ESTAT/earn_nt_net/1.0/*.*.*.*.*"
    "?c[currency]=EUR&c[estruct]=NET&format=csvdata&compress=false&labels=both"
)

# Databrowser exports each dimension as a code column followed by a label column.
# The API with labels=both instead returns single "CODE: Label" cells; this maps
# each code column to the label column name used by the databrowser export.
DIMENSION_LABEL_COLUMNS = {
    'freq': 'Time frequency',
    'currency': 'Currency',
    'estruct': 'Earnings structure',
    'ecase': 'Earnings case',
    'geo': 'Geopolitical entity (reporting)',
}


def download_net_earnings(out_path='net_earnings.csv'):
    print(f"[INFO] Downloading EARN_NT_NET (EUR, NET) from the Eurostat API...")
    df = pd.read_csv(EARN_NT_NET_URL, dtype=str)

    # Header cells arrive as "code: Label" too - keep only the code part
    df.columns = [c.split(': ', 1)[0] for c in df.columns]

    for code_col, label_col in DIMENSION_LABEL_COLUMNS.items():
        parts = df[code_col].str.split(': ', n=1, expand=True)
        df[code_col] = parts[0]
        df[label_col] = parts[1]

    df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
    df['TIME_PERIOD'] = pd.to_numeric(df['TIME_PERIOD'], errors='coerce').astype('Int64')

    out_cols = ['STRUCTURE', 'STRUCTURE_ID',
                'freq', 'Time frequency', 'currency', 'Currency',
                'estruct', 'Earnings structure', 'ecase', 'Earnings case',
                'geo', 'Geopolitical entity (reporting)',
                'TIME_PERIOD', 'OBS_VALUE', 'OBS_FLAG', 'CONF_STATUS']
    df = df[[c for c in out_cols if c in df.columns]]

    df.to_csv(out_path, index=False)
    print(f"[INFO] Saved {len(df)} rows to {out_path} "
          f"({df['geo'].nunique()} countries, "
          f"years {int(df['TIME_PERIOD'].min())}-{int(df['TIME_PERIOD'].max())})")


if __name__ == '__main__':
    download_net_earnings(sys.argv[1] if len(sys.argv) > 1 else 'net_earnings.csv')
