from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from server.apps.nm_task.schemas import NmTaskDO
from server.nm_algo.create_data import build_small_data, save_test_data
from server.nm_algo.pipeline import NameMatchingBatch, NameMatchingRealtime

small_set_expected_result = pd.DataFrame.from_records(
    [
        ["Zhe Chines Sun", 0, "Zhe Sun", 0.6667],
        ["Zhe Chines Sun", 2, "Zhe General Dutch Sun", 0.4280],
        ["Zhe Chinese General", 1, "Zhe General Chinese Sun", 0.8910],
        ["Zhe Chinese General", 2, "Zhe General Dutch Sun", 0.5175],
        ["Dirk Werner Nowitzki", 3, "Dirk Nowitzki", 0.6667],
        ["Dirk Werner Nowitzki", 4, "Dirk Dunking Deutschman", 0.2311],
        ["Cristiano Ronaldo", 6, "Cristiano Ronaldo CR7", 0.7991],
        ["Cristiano Ronaldo", 5, "Ronaldo", 0.6586],
        ["Chandler Nothing found", -1, "N/A", 0],
        [
            "Blizzard Entteretainment BV",
            10,
            "Blizzard Entertainment B.V.",
            0.5493,
        ],
        ["Blizzard Entteretainment BV", 14, "H.M. BV", 0.4122],
        ["AE Investment", 12, "Ahmet Erdem Investment", 0.2887],
        ["Also no match here", -1, "N/A", 0],
        ["H.M. BV", 14, "H.M. BV", 1.0],
        ["H.M. BV", 13, "H&M BV", 1.0],
        ["H & M BV", 14, "H.M. BV", 1.0],
        ["H & M BV", 13, "H&M BV", 1.0],
        [
            "VER VAN VRIENDEN VAN HET ALLARD PIERSON MUSEUM",
            15,
            "Vereniging van Vrienden van het Allard Pierson Museum",
            0.8132,
        ],
        [
            "Tank & Truck Cleaning Weert T.T.C. Weert",
            16,
            "TANK & TRUCK CLEANING WEERT TTC WEERT",
            0.9354,
        ],
        ["Amazon EMEA SARL", 17, "Amazon.com", 0.2357],
    ],
    columns=["nm_name", "gt_row_no", "matched_name", "score"],
)


def test_NameMatchingBatch(do_nm_batch_task_small_set: NmTaskDO) -> None:
    # prepare dataset
    Path("./localfs").mkdir(exist_ok=True)
    Path("./localfs/data/").mkdir(exist_ok=True)

    gt_df, nm_df = build_small_data()
    save_test_data(
        gt_df,
        "./localfs/data/gt-small.csv",
        nm_df,
        "./localfs/data/nm-small.csv",
    )

    nm_batch_task = NameMatchingBatch(do_nm_batch_task_small_set.id, user_id=0)
    nm_batch_task.execute()

    pd.set_option("max_columns", None)
    print(
        nm_batch_task.result,
    )
    assert_frame_equal(
        nm_batch_task.result, small_set_expected_result, check_names=False
    )


def test_NameMatchingRealtime(do_nm_rt_task_small_set: NmTaskDO) -> None:
    # prepare dataset
    Path("./localfs").mkdir(exist_ok=True)
    Path("./localfs/data/").mkdir(exist_ok=True)

    gt_df, nm_df = build_small_data()
    save_test_data(
        gt_df,
        "./localfs/data/gt-small.csv",
        nm_df,
        "./localfs/data/nm-small.csv",
    )

    nm_rt_task = NameMatchingRealtime(do_nm_rt_task_small_set.id, user_id=0)
    result = nm_rt_task.execute(["Zhe Sun", "Dirk Nowitzki", "Zimmer Hao"])

    # expected = [
    #     [
    #         (0, "Zhe Sun", 1.0),
    #         (2, "Zhe General Dutch Sun", 0.3445),
    #     ],
    #     [(17, "Xi Wang Dott BV", 0.6785)],
    #     None,
    # ]

    expected = pd.DataFrame.from_records(
        [
            ["Zhe Sun", 0, "Zhe Sun", 1.0],
            ["Zhe Sun", 2, "Zhe General Dutch Sun", 0.642],
            ["Dirk Nowitzki", 3, "Dirk Nowitzki", 1],
            ["Dirk Nowitzki", 4, "Dirk Dunking Deutschman", 0.3466],
            ["Zimmer Hao", -1, "N/A", 0],
        ],
        columns=["nm_name", "gt_row_no", "matched_name", "score"],
    )
    print(result)

    assert_frame_equal(result, expected, check_names=False)
