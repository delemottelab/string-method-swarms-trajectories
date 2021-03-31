import argparse

from stringmethod import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_file",
        type=str,
        help="A config file in JSON format",
        default=None,
    )
    parser.add_argument(
        "--iteration",
        type=int,
        help="Current iteration of the string method",
        default=1,
    )
    parser.add_argument(
        "--start_mode",
        type=str,
        help="starting_step (steered|string|postprocessing)",
        default="string",
    )
    return parser.parse_args()


def run(conf: config.Config, start_mode, iteration=1) -> None:
    logger.debug("Using config %s", conf)
    if start_mode == "string":
        r = stringmd.StringIterationRunner.from_config(
            config=conf, iteration=iteration, append=start_mode == "auto"
        )
        r.run()
        # return run(conf, start_mode='postprocessing')
    elif start_mode == "steered":
        r = steeredmd.SteeredRunner.from_config(config=conf)
        r.run()
    elif start_mode == "postprocessing":
        postprocessing.run(conf)
    else:
        raise ValueError("Unknown start mode {}".format(start_mode))


if __name__ == "__main__":
    try:
        logger.info(
            """
                    
                    .___     .__                         __    __         .__        ___.    
                  __| _/____ |  |   ____   _____   _____/  |__/  |_  ____ |  | _____ \_ |__  
                 / __ |/ __ \|  | _/ __ \ /     \ /  _ \   __\   __\/ __ \|  | \__  \ | __ \ 
                / /_/ \  ___/|  |_\  ___/|  Y Y  (  <_> )  |  |  | \  ___/|  |__/ __ \| \_\ \ 
                \____ |\___  >____/\___  >__|_|  /\____/|__|  |__|  \___  >____(____  /___  /
                     \/    \/          \/      \/                       \/          \/    \/ 
            
                Starting string of swarms simulation by Oliver Fleetwood and Marko Petrovic 2017-2020.
                https://github.com/delemottelab/string-method-gmxapi
                
                Version {}
            """.format(
                VERSION
            )
        )
        args = parse_args()
        args.iteration = max(args.iteration, 1)
        conf = config.load_config(args.config_file)
        logger.setLevel(conf.log_level)
        run(conf, args.start_mode, args.iteration)

        logger.info("----------------Finished------------")
    except Exception as ex:
        logger.exception(ex)
        logger.error("Script failed with message %s", str(ex))
