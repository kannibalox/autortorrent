from pathlib import Path
from typing import Iterable
from pyrosimple.config import settings

from sqlalchemy import BigInteger, String, create_engine, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


engine = create_engine(
    settings.AUTORTORRENT.db_url,
    echo=True
)


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String())
    name: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(BigInteger())

    @property
    def os_path(self):
        return Path(self.path, self.name)


class ClientItem(Base):
    __tablename__ = "client_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_url: Mapped[str] = mapped_column(String())
    hash: Mapped[str] = mapped_column(String(40))
    path: Mapped[str] = mapped_column(String())
    alias: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(BigInteger())


def insert_paths(root: Path, iterator: Iterable) -> None:
    with Session(engine) as session:
        stmt = delete(File).where(File.path.like(f"{root}%"))
        session.execute(stmt)
        session.add_all(iterator)
        session.commit()


def insert_client_paths(client_url: str, iterator: Iterable) -> None:
    with Session(engine) as session:
        stmt = delete(ClientItem).where(ClientItem.client_url == client_url)
        session.execute(stmt)
        session.add_all(iterator)
        session.commit()
