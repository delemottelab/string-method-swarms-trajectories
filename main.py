import argparse

import stringmethod as sm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, help='A config file in JSON format', default="config.json")
    parser.add_argument('--start_mode', type=str, help='starting_step (auto|steered|string|postprocessing)', default="auto")
    return parser.parse_args()


if __name__ == "__main__":
    sm.logger.info("----------------Starting string of swarms simulation by delemottelab 2017-2020------------")
    args = parse_args()
    conf = sm.config.load_config(args.config_file)
    sm.logger.debug("Using config %s", conf)
    # TODO look at start-mode and depend what action to take
    # TODO handle steered MD. Look at Marko's code
    # TODO import iteration runner
    # TODO perform postprocessing by loading xvg files and output numpy files

    sm.logger.info("----------------Finished------------")


