from typing import Tuple

import pandas as pd
from pandas.core.frame import DataFrame


def build_small_data() -> Tuple[DataFrame, DataFrame]:
    """Generate test data sets
    :param gt_file_name: groundtruth dataset location
    :type gt_file_name: str
    :param nm_file_name: name matching set location
    :type nm_file_name: str
    """

    # Mock ground truth
    gt_list = [
        ("Zhe Sun", 1),
        ("Zhe General Chinese Sun", 1),
        ("Zhe General Dutch Sun", 1),
        ("Dirk Nowitzki", 2),
        ("Dirk Dunking Deutschman", 2),
        ("Ronaldo", 3),
        ("Cristiano Ronaldo CR7", 3),
        ("Jonas X", 4),
        ("John Doe", 5),
        ("Jane Doe", 6),
        ("Blizzard Entertainment B.V.", 7),
        ("Sony Entertainment", 8),
        ("Ahmet Erdem Investment", 9),
        ("H&M BV", 10),
        ("H.M. BV", 11),
        ("Vereniging van Vrienden van het Allard Pierson Museum", 12),
        ("TANK & TRUCK CLEANING WEERT TTC WEERT", 13),
        ("Amazon.com", 14),
    ]
    gt_df = pd.DataFrame(gt_list, columns=["company name", "company id"])

    # Mock names to match
    test_list = [
        ("Zhe Chines Sun", 1, 1),
        ("Zhe Chinese General", 1, 1),
        ("Dirk Werner Nowitzki", 2, 2),
        ("Cristiano Ronaldo", 3, 3),
        ("Chandler Nothing found", 4, None),
        ("Blizzard Entteretainment BV", 5, 7),
        ("AE Investment", 6, 9),
        ("Also no match here", 7, None),
        ("H.M. BV", 8, 10),
        ("H & M BV", 9, 11),
        ("VER VAN VRIENDEN VAN HET ALLARD PIERSON MUSEUM", 10, 12),
        ("Tank & Truck Cleaning Weert T.T.C. Weert", 11, 13),
        ("Amazon EMEA SARL", 12, 14),
    ]
    nm_df = pd.DataFrame(test_list, columns=["name", "seq id", "company id"])

    return gt_df, nm_df


def save_test_data(
    gt_df: DataFrame, gt_file_name: str, nm_df: DataFrame, nm_file_name: str
) -> None:
    gt_df.to_csv(gt_file_name, sep=",", header=True, index=False)
    nm_df.to_csv(nm_file_name, sep=",", header=True, index=False)
