This is an rtorrent-only file reseeder in the same vein as
[autotorrent2](https://github.com/JohnDoee/autotorrent2), which I
would highly recommend using even if you use rtorrent. Unfortunately
autotorrent2 needs some optimization before I'm ready to use it, so
this is just a small project to hopefully only be used intermediately,
until autotorrent2 can be optimized.

# Installation

```bash
pip install https://github.com/kannibalox/autortorrent.git
```

# Configuration

In `~/.config/pyrosimple/config`, set the following config values:

```
[AUTORTORRENT]
db_url = "postgresql+psycopg://username:password@localhost/autortorrent" # Any sqlalchemy url: https://docs.sqlalchemy.org/en/20/core/engines.html
```

# Usage

## Scanning

Scan a path: `art2 scan <path>`

## Scanning

Scan a rtorrent instance: `art2 scan <instance alias or url>`

## Loading a torrent

```bash
art2 load <path>.torrent
```
