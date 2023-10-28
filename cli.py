import logging
import os
import sys
from argparse import ArgumentParser

from zc.lockfile import LockError, LockFile

from core.config import Config
from webstore.lotr.connector import LotRWebstoreConnector


def get_parser():
    parser = ArgumentParser()

    # Calculate the default config file path relative to the script
    script_directory = os.path.dirname(os.path.realpath(__file__))
    default_config_path = os.path.join(script_directory, "default_config.ini")

    parser.add_argument("email", help="Email address")
    parser.add_argument("--config", "-c", default=default_config_path, help="Path to the configuration file")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    Config.load_global_config(args.config)
    config = Config.get_global_config()
    logging.basicConfig(
        filename='lotr_webstore.log',
        level=config.default_log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('__main__')
    # TODO: Add lock options to config
    #  1 -> Use lock
    #  2 -> lockfile name supporting %s(email)
    #  3 -> Add lock validation
    #     * validate lockname
    #     * enfore lock if schedule is allowed
    try:
        lock = LockFile(f'webstore_{args.email}.lock')
    except LockError:
        logger.warning('Prevent the script from running multiple times. Exit')
        sys.exit(1)

    connector = LotRWebstoreConnector(
        email=args.email,
        config=config
    )
    connector.start()
    lock.close()

if __name__ == "__main__":
    main()
