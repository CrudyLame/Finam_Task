import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime, timedelta


class DataProcessor:
    """Utilities for processing dialogue data"""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None

    def load_and_clean_data(self) -> pd.DataFrame:
        """Load and clean the CSV data"""
        self.df = pd.read_csv(self.csv_path, delimiter=";", quotechar='"')

        # Remove unnecessary column
        if "Столбец1" in self.df.columns:
            self.df = self.df.drop("Столбец1", axis=1)

        # Convert timestamp to datetime
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])

        # Convert block_type to category for better performance
        self.df["block_type"] = self.df["block_type"].astype("category")

        # Sort by user_id and timestamp
        self.df = self.df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

        return self.df

    def get_basic_stats(self) -> Dict:
        """Get basic statistics about the dataset"""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_and_clean_data() first.")

        stats = {
            "total_events": len(self.df),
            "unique_users": self.df["user_id"].nunique(),
            "date_range": {
                "start": self.df["timestamp"].min(),
                "end": self.df["timestamp"].max(),
            },
            "block_types": self.df["block_type"].value_counts().to_dict(),
            "unique_departments": self.df["nnDepartment"].nunique(),
        }

        return stats

    def clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if pd.isna(text):
            return ""

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", str(text).strip())

        # Remove quotes around text
        text = re.sub(r'^"(.*)"$', r"\1", text)

        return text
