import argparse

import stringmethod as sm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_file', type=str, help='A config file in JSON format', default="config.json")
    parser.add_argument('--iteration', type=int, help='Current iteration of the string method', default=1)
    parser.add_argument('--start_mode', type=str, help='starting_step (auto|steered|string|postprocessing)',
                        default="auto")
    return parser.parse_args()


def run(conf: sm.config.Config, start_mode: str = 'auto', iteration: int = 0) -> None:
    sm.logger.debug("Using config %s", conf)
    if start_mode == 'string' or start_mode == 'auto':
        r = sm.stringmd.StringIterationRunner(config=conf,
                                              iteration=None if start_mode == 'auto' else iteration,
                                              append=start_mode == 'auto')
        r.run()
        if start_mode == 'auto':
            return run(conf, start_mode='postprocessing')
    elif start_mode == 'steered':
        r = sm.steeredmd.SteeredRunner(conf)
        r.run()
        return run(conf, start_mode='string', iteration=0)
    else:
        raise NotImplementedError("Start mode {} not supported".format(start_mode))
    # TODO perform postprocessing by loading xvg files and output numpy files


if __name__ == "__main__":
    sm.logger.info("----------------Starting string of swarms simulation by delemottelab 2017-2020------------")
    args = parse_args()
    conf = sm.config.load_config(args.config_file, args.start_mode)
    run(conf)

    sm.logger.info("----------------Finished------------")
