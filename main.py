import argparse

from stringmethod import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, help='A config file in JSON format', default="config.json")
    parser.add_argument('--iteration', type=int, help='Current iteration of the string method', default=1)
    parser.add_argument('--start_mode', type=str, help='starting_step (auto|steered|string|postprocessing)',
                        default="auto")
    return parser.parse_args()


def run(conf: config.Config, start_mode, iteration) -> None:
    logger.debug("Using config %s", conf)
    if start_mode == 'string' or start_mode == 'auto':
        r = stringmd.StringIterationRunner(config=conf,
                                           iteration=iteration,
                                           append=start_mode == 'auto')
        r.run()
        if start_mode == 'auto':
            return run(conf, start_mode='postprocessing')
    elif start_mode == 'steered':
        r = steeredmd.SteeredRunner(conf)
        r.run()
        return run(conf, start_mode='string', iteration=0)
    else:
        raise NotImplementedError("Start mode {} not supported".format(start_mode))
    # TODO perform postprocessing by loading xvg files and output numpy files


if __name__ == "__main__":
    logger.info("----------------Starting string of swarms simulation by delemottelab 2017-2020------------")
    args = parse_args()
    conf = config.load_config(args.config_file)
    logger.setLevel(conf.log_level)
    run(conf, args.start_mode, args.iteration)

    logger.info("----------------Finished------------")
