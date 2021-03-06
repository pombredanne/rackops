import argparse
import json
import os
import sys
import configparser
import logging

from rackops.rackops import Rackops
from getpass import getpass

def setup_logging(verbosity):
    level_list = [logging.WARN, logging.INFO, logging.DEBUG]
    if len(level_list) < verbosity - 1:
        print ("Invalid verbosity")
        sys.exit(1)

    level = level_list[verbosity]
    logging.basicConfig(level=level)

def format_config(config):
    # Recursive function that converts a
    # configparser.ConfigParser object into a dict
    # Can't convert directly with dict(config)
    # since dict(config) returns the dict in the form:
    # {"section_1": "<Section1 Object>", "section_2": "<Section2 Object, ...}
    # but using dict(config["section_1"]) we can see a valid dict representation
    # of the specified section.
    # so this basically recursivelly calls dict() on every subdict
    keys = dict(config).keys()
    formatted = {}
    for k in keys:
        formatted[k.lower()] = config[k]
        if not type(config[k]) == str:
            formatted[k.lower()] = format_config(config[k])
    return formatted

def get_config(config_path):
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
    except configparser.ParsingError as e:
        print ("Invalid configuration file")
        sys.exit(1)

    return format_config(config)

def get_environment_variables():
    # Read environment variables regarding
    # whatever the config file might include
    env_vars = {}
    if os.environ.get("RACKOPS_USERNAME", None):
        env_vars["username"] = os.environ["RACKOPS_USERNAME"]

    if os.environ.get("RACKOPS_PASSWORD", None):
        env_vars["password"] = os.environ["RACKOPS_PASSWORD"]

    if os.environ.get("RACKOPS_NFS_SHARE", None):
        env_vars["nfs_share"] = os.environ["RACKOPS_NFS_SHARE"]

    if os.environ.get("RACKOPS_HTTP_SHARE", None):
        config["http_share"] = os.environ["RACKOPS_http_SHARE"]

    return env_vars

def main():
    default_config_path = os.path.join(os.environ.get("HOME", "/"), ".config", "rackops")
    if os.environ.get("XDG_CONFIG_HOME", None):
        default_config_path = os.environ["XDG_CONFIG_HOME"]
    # 1. Configuration:
    #   - If config file exists, use it
    #   - Else if environment variables exist use those
    #   - Else if command line arguments exist, use those
    #   - Else prompt the user for variables
    # 2. Initialize a Rackops object
    # 3. call rackops.run()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        help="Command which will be executed"
    )
    parser.add_argument(
        "identifier",
        help="Identifier for the machine which the command will be executed",
        default=None
    )
    parser.add_argument(
        "command_args",
        help="Arguments of the command to be executed",
        nargs='*'
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        help="Configuration file path",
        default=default_config_path
    )
    parser.add_argument(
        "-u",
        "--username",
        action="store",
        help="IPMI username",
        default=None
    )
    parser.add_argument(
        "-p",
        "--password",
        action="store_true",
        help="IPMI password",
        default=None
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force",
        default=None
    )
    parser.add_argument(
        "-w",
        "--wait",
        action="store_true",
        help="Wait",
        default=None
    )
    parser.add_argument(
        "-d",
        "--dcim",
        help="DCIM name",
        default="netbox"
    )
    parser.add_argument(
        "-r",
        "--rack",
        help="Rack name",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-a",
        "--rack-unit",
        help="Rack unit",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-s",
        "--serial",
        help="Serial name",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Sets logging to INFO for -v and DEBUG for -vv",
        action="count",
        default=0
    )
    args = parser.parse_args()

    if len([x for x in [args.serial, args.rack, args.rack_unit] if x]) > 1:
        print ("Can't use rack, rack unit and serial flags concurrently")
        sys.exit(1)

    setup_logging(args.verbose)
    config = get_config(args.config)
    env_vars = get_environment_variables()

    rackops = Rackops(args.command, args.identifier, args.rack, args.rack_unit, args.serial, args.command_args, args, config, env_vars)
    rackops.run()

if __name__ == "__main__":
    main()
