import json
import random
from collections import Counter
from typing import Annotated

import pandas as pd
import typer
import yaml
from rich import print
from rich.progress import track


def parse_hero_data(hero_data: dict, talent_mapping: list[dict]) -> pd.DataFrame:
    print("Parsing info to DataFrame ...")
    try:
        list_of_attrs = hero_data["attr"]["values"]
        attributes = {attr["id"]: attr["value"] for attr in list_of_attrs}

        list_of_tal_vals = hero_data.get("talents")

    except KeyError as exec:
        raise ValueError(
            "The data provided is not in the expected format from the Optolith."
        ) from exec

    talents = pd.DataFrame.from_records(talent_mapping)
    talents = talents.loc[:, ["id", "name", "check1", "check2", "check3"]]
    talents = talents.set_index("id")

    talents.loc["modifier"] = pd.Series(list_of_tal_vals)

    return talents.reindex()


def simulate_rolls(talent_data: pd.DataFrame, n_tries: int = 10_000):
    result_records = []
    for _, row in track(talent_data.iterrows(), description="Simmulating Talents ..."):
        results = []

        for _ in range(n_tries):
            attr_1, attr_2, attr_3 = random.sample(range(1, 21), 3)
            diffs = [
                row.loc["check1"] - attr_1,
                row.loc["check2"] - attr_2,
                row.loc["check3"] - attr_3,
            ]

            diffs = [min(diff, 0) for diff in diffs]
            needed_tp = row.loc["modifier"] - sum(diffs)
            results.append(max(-1, needed_tp))

        res_counter = Counter(results)
        result_dict = {
            row.loc["name"]: {res: freq / n_tries for res, freq in res_counter.items()}
        }
        result_records.append(result_dict)
    return result_records


def main(
    hero_data: Annotated[
        typer.FileText,
        typer.Argument(
            help="The Path to the .json file of the hero from the optholith generation tool."
        ),
    ],
    talent_mapping: Annotated[
        typer.FileText,
        typer.Option(
            help="A file mapping the talents to attributes.",
            default="../data/talent_mapping.yaml",
        ),
    ],
    n_tries: Annotated[
        int,
        typer.Option(
            default=10_000, help="The number of rolls to simulate per talent."
        ),
    ],
):
    print("Reading files ...")
    hero_data = json.loads(hero_data.read())
    talent_mapping = yaml.load(talent_mapping)

    talents = parse_hero_data(hero_data, talent_mapping)

    simulate_rolls(talents, n_tries)
    # TODO: display results


if __name__ == "__main__":
    typer.run(main)
