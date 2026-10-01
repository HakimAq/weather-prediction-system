import pandas as pd

from .config import DATA_FILE
from .cleaner import clean_data


def load_raw_data(path=DATA_FILE, verbose: bool = True) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = clean_data(df, verbose=verbose)
    return df