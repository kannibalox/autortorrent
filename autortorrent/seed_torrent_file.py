import logging
import sys
import time

from pathlib import Path, PurePath
from typing import Dict, List
from xmlrpc import client

import bencode
import pyrosimple

from pyrosimple.util.metafile import Metafile, PieceFailer
from sqlalchemy import select

from autortorrent.db import File, Session, engine


FileMatchType = Dict[Path, List[File]]
logger = logging.getLogger(__name__)


def load_multi_torrent(metafile: Metafile, _limit: int = 15):
    name = metafile["info"]["name"]
    with Session(engine) as session:
        # Fill in exact matches
        first_file_info = metafile["info"]["files"][0]
        first_path = PurePath(name, *first_file_info["path"][:-1])
        exact_select_stmt = (
            select(File)
            .where(File.size == first_file_info["length"])
            .where(File.name == first_file_info["path"][-1])
            .filter(File.path.like(f"%{first_path}"))
        )
        different_base_select_stmt = (
            select(File)
            .where(File.size == first_file_info["length"])
            .where(File.name == first_file_info["path"][-1])
        )
        for filematch in session.scalars(exact_select_stmt):
            pathmatch = Path(*filematch.os_path.parts[: -len(first_file_info["path"])])
            try:
                load_against_match(metafile, pathmatch)
                return
            except OSError as exc:
                logger.error("Could not match: %s", exc)
        for filematch in session.scalars(different_base_select_stmt):
            pathmatch = Path(*filematch.os_path.parts[: -len(first_file_info["path"])])
            try:
                load_against_match(metafile, pathmatch)
                return
            except OSError as exc:
                logger.error("Could not match: %s", exc)


def closest_ancestor(matches: Dict[Path, List[File]]):
    for k, v in matches.items():
        print(k, [(f.name, f.path) for f in v])


def load_against_match(
    metafile: Metafile, match: Path, hash_check: bool = True
) -> None:
    name = metafile["info"]["name"]
    logger.debug("Attempting full load of %s against %s", name, match)
    metafile.add_fast_resume(match)
    logger.debug("Fast resume added")
    if hash_check:
        logger.debug("Hashing against %s", match)
        pf = PieceFailer(metafile, logger)
        metafile.hash_check(match, piece_callback=pf.check_piece)
    logger.debug("Matched")
    p = pyrosimple.connect().open()
    p.load.raw_verbose(
        "",
        client.Binary(bencode.encode(dict(metafile))),
        f'd.directory_base.set="{match}"',
    )
    for _ in range(4):
        time.sleep(0.1)
        try:
            p.d.hash(metafile.info_hash())
        except pyrosimple.util.rpc.HashNotFound:
            pass
        else:
            break
    if p.d.directory(metafile.info_hash()) == str(match):
        p.d.start(metafile.info_hash())


def remove_if_loaded(metafile_path: Path):
    metafile = Metafile.from_file(metafile_path)
    p = pyrosimple.connect().open()
    try:
        p.d.hash(metafile.info_hash())
    except pyrosimple.util.rpc.HashNotFound:
        pass
    else:
        logger.debug(
            "Hash %s exists, unlinking path %s", metafile.info_hash(), metafile_path
        )
        metafile_path.unlink()


def match_torrent(metafile: Metafile):
    name = metafile["info"]["name"]
    if not metafile.is_multi_file:
        with Session(engine) as session:
            stmt = (
                select(File)
                .where(File.size == metafile["info"]["length"])
                .where(File.name == name)
            )
            for match in session.scalars(stmt):
                try:
                    load_against_match(metafile, Path(match.path))
                    return
                except OSError as exc:
                    logger.error("Could not match: %s", exc)
    else:
        load_multi_torrent(metafile)


def run(metapath: Path):
    metafile = Metafile.from_file(metapath)
    metafile.check_meta()
    match_torrent(metafile)


if __name__ == "__main__":
    run(Path(sys.argv[1]))
