from typing import Dict, Any


def parse_mdp(mdp_file: str) -> Dict[str, Any]:
    """
    Reads an MDP file and puts the parameters and their values into a dictionary
    :param mdp_file:
    :return:
    """
    res = dict()
    with open(mdp_file) as fp:
        for line in fp.readlines():
            line = line.split(";")[0]  # Remove comments
            if "=" not in line:
                continue  # empty line or comment
            line = line.replace(" ", "").replace("\t", "")
            [key, value] = line.split("=", 1)
            try:
                value = float(value)
            except ValueError:
                # Not a float
                pass
            res[key] = value
    return res
