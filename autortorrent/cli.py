import argparse
import logging
import sys

from pathlib import Path

import pyrosimple


logger = logging.getLogger(__name__)


def scan(args):
    from autortorrent.db import Base, engine, insert_client_paths, insert_paths
    from autortorrent.scan import scan_client, scan_root

    Base.metadata.create_all(engine)
    for target in args.target:
        if Path(target).is_dir():
            insert_paths(Path(target), scan_root(Path(target)))
        else:
            for c in pyrosimple.config.multi_connection_lookup(target):
                insert_client_paths(c, scan_client(c))


def load(args):
    from autortorrent.seed_torrent_file import remove_if_loaded, run

    for target in args.target:
        target_path = Path(target)
        if target_path.is_file():
            try:
                run(target_path)
                if args.remove:
                    remove_if_loaded(target_path)
            except Exception as err:
                logger.error("Error loading file %s: %s", target_path, err)
                raise


def run():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    logging.basicConfig(level=logging.DEBUG)

    parser_scan = subparsers.add_parser("scan")
    parser_scan.add_argument("target", nargs="+")
    parser_scan.set_defaults(func=scan)

    parser_load = subparsers.add_parser("load")
    parser_load.add_argument("target", nargs="+")
    parser_load.add_argument("--remove", action="store_true")
    parser_load.set_defaults(func=load)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    run()
