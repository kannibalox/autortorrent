import logging
import os
import sys

from pathlib import Path
from typing import Iterable

import pyrosimple
import pyrosimple.config

from sqlalchemy import delete

from autortorrent.db import Base, ClientItem, File, Session, engine


logger = logging.getLogger(__name__)


def scan_client(client_url: str):
    client_engine = pyrosimple.connect(client_url)
    attrs = ["hash", "path", "alias", "size"]
    attr_dicts = []

    logging.basicConfig(level=logging.DEBUG)
    for item in client_engine.items(
        "default",
        [
            "d.directory",
            "d.is_multi_file",
            "d.custom=memo_alias",
            "d.complete",
            "d.name",
            "d.hash",
            "d.size_bytes",
        ],
    ):
        attr_dicts.append({n: getattr(item, n) for n in attrs})
    for attr in attr_dicts:
        yield ClientItem(client_url=client_url, **attr)


def insert_client_paths(client_url, iterator: Iterable):
    with Session(engine) as session:
        stmt = delete(ClientItem).where(ClientItem.client_url == client_url)
        session.execute(stmt)
        session.add_all(iterator)
        session.commit()


def scan_root(root: Path):
    return recurse_path(root)


def recurse_path(path: Path):
    for p in os.scandir(path):
        if p.is_dir():
            try:
                yield from recurse_path(Path(p))
            except OSError as e:
                logger.error(e)
        elif p.is_file():
            size = p.stat().st_size
            yield File(name=p.name, path=str(Path(p).parent), size=size)


def insert_paths(root: Path, iterator: Iterable):
    with Session(engine) as session:
        session.execute(delete(File).where(File.path.like(f"{root}%")))
        session.add_all(iterator)
        session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    target = sys.argv[1]
    if Path(target).is_dir():
        insert_paths(Path(target), scan_root(Path(target)))
    else:
        for c in pyrosimple.config.multi_connection_lookup(target):
            insert_client_paths(c, scan_client(c))
