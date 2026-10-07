from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import zlib
from pathlib import Path

import agency_backend as agency
import club_backend as club
import wallet_cache_backend as shared

VERSION=1

SOURCES={
    "shared": Path(shared.DB),
    "agency": Path(agency.DB),
    "club": Path(club.DB),
}

def _ensure_schemas():
    c=shared.db(); c.close()
    c=agency.db(); agency.init(c); agency.ensure_v2(c); agency.ensure_activity_v28(c); c.close()
    c=club.db(); c.close()

def _wallet_tables(path: Path):
    if not path.exists():
        return []
    c=sqlite3.connect(path); c.row_factory=sqlite3.Row
    tables=[r["name"] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    out=[]
    for table in tables:
        cols=[r["name"] for r in c.execute(f'PRAGMA table_info("{table}")').fetchall()]
        if "wallet" in cols:
            out.append(table)
    c.close()
    return out

def _dump_db(path: Path,wallet: str):
    if not path.exists():
        return {}
    c=sqlite3.connect(path); c.row_factory=sqlite3.Row
    data={}
    for table in _wallet_tables(path):
        rows=[dict(r) for r in c.execute(f'SELECT * FROM "{table}" WHERE lower(wallet)=?',(wallet.lower(),)).fetchall()]
        if rows:
            data[table]=rows
    c.close()
    return data

def dump_wallet(wallet: str):
    wallet=(wallet or "").strip().lower()
    if not wallet:
        return None
    _ensure_schemas()
    payload={
        "version":VERSION,
        "wallet":wallet,
        "sources":{name:_dump_db(path,wallet) for name,path in SOURCES.items()},
    }
    raw=json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    compressed=zlib.compress(raw,9)
    encoded=base64.b64encode(compressed).decode("ascii")
    return {
        "value":encoded,
        "signature":hashlib.sha256(compressed).hexdigest()[:16],
        "bytes":len(compressed),
        "rows":sum(len(rows) for src in payload["sources"].values() for rows in src.values()),
    }

def _insert_rows(path: Path,tables: dict,wallet: str):
    if not tables:
        return 0
    c=sqlite3.connect(path); c.row_factory=sqlite3.Row
    restored=0
    try:
        for table,rows in tables.items():
            if not rows:
                continue
            exists=c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
            if not exists:
                continue
            cols=[r["name"] for r in c.execute(f'PRAGMA table_info("{table}")').fetchall()]
            if "wallet" not in cols:
                continue
            for row in rows:
                clean={k:v for k,v in row.items() if k in cols}
                if str(clean.get("wallet") or "").lower()!=wallet.lower():
                    continue
                names=list(clean)
                if not names:
                    continue
                placeholders=",".join("?" for _ in names)
                quoted=",".join(f'"{x}"' for x in names)
                c.execute(f'INSERT OR REPLACE INTO "{table}" ({quoted}) VALUES ({placeholders})',[clean[x] for x in names])
                restored+=1
        c.commit()
    finally:
        c.close()
    return restored

def restore_wallet(encoded: str,expected_wallet: str|None=None):
    if not encoded:
        return {"restored":0,"wallet":None}
    try:
        raw=zlib.decompress(base64.b64decode(encoded.encode("ascii")))
        payload=json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Browser backup could not be decoded: {e}")
    if int(payload.get("version") or 0)!=VERSION:
        raise RuntimeError("Browser backup version is not supported")
    wallet=str(payload.get("wallet") or "").strip().lower()
    if not wallet:
        raise RuntimeError("Browser backup has no wallet")
    if expected_wallet and wallet!=expected_wallet.strip().lower():
        raise RuntimeError("Browser backup belongs to a different wallet")
    _ensure_schemas()
    total=0
    for name,path in SOURCES.items():
        total+=_insert_rows(path,(payload.get("sources") or {}).get(name) or {},wallet)
    return {"restored":total,"wallet":wallet}

def local_wallet_rows(wallet: str):
    wallet=(wallet or "").strip().lower()
    if not wallet:
        return 0
    _ensure_schemas()
    total=0
    for path in SOURCES.values():
        if not path.exists():
            continue
        c=sqlite3.connect(path); c.row_factory=sqlite3.Row
        try:
            for table in _wallet_tables(path):
                total+=int(c.execute(f'SELECT COUNT(*) n FROM "{table}" WHERE lower(wallet)=?',(wallet,)).fetchone()["n"])
        finally:
            c.close()
    return total
