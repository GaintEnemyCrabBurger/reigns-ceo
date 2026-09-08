# -*- coding: utf-8 -*-
"""Local-only server for the story control room."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
CARDS_PATH = ROOT / "cards.csv"
BASELINE_PATH = ROOT / "cards-independent.csv"
BACKUP_DIR = ROOT / ".story-backups"
FIELDS = [
    "thematic", "card", "id", "bearer", "conditions", "lockturn", "weight",
    "question", "override_yes", "answer_yes", "yes_cash", "yes_team",
    "yes_market", "yes_capital", "yes_custom", "override_no", "answer_no",
    "no_cash", "no_team", "no_market", "no_capital", "no_custom",
]


def file_version(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_cards(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path.name} 的表头不是约定的 22 列")
        cards = []
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"{path.name} 第 {row_number} 行列数不匹配")
            card = {field: (row.get(field) or "").strip() for field in FIELDS}
            if card["id"]:
                cards.append(card)
        return cards


def validate_cards(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ValueError("牌库必须是非空数组")

    cards: list[dict[str, str]] = []
    ids: set[str] = set()
    names: set[str] = set()
    for index, raw_card in enumerate(value, start=1):
        if not isinstance(raw_card, dict):
            raise ValueError(f"第 {index} 张卡不是对象")
        card = {field: str(raw_card.get(field, "")).strip() for field in FIELDS}
        if not card["id"]:
            raise ValueError(f"第 {index} 张卡缺少 ID")
        if card["id"] in ids:
            raise ValueError(f"ID 重复：{card['id']}")
        if card["card"] and card["card"] in names:
            raise ValueError(f"引用名重复：{card['card']}")
        ids.add(card["id"])
        if card["card"]:
            names.add(card["card"])
        cards.append(card)

    for card in cards:
        for field in ("yes_custom", "no_custom"):
            for token in re.split(r"\s+and\s+", card[field]):
                token = token.strip()
                if token.startswith(">_") and token[2:] not in names:
                    raise ValueError(
                        f"{card['card'] or card['id']}.{field} 跳转目标不存在：{token[2:]}"
                    )
    return cards


def serialize_cards(cards: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=FIELDS,
        delimiter=";",
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(cards)
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def write_cards(cards: list[dict[str, str]]) -> tuple[str, str]:
    BACKUP_DIR.mkdir(exist_ok=True)
    old_version = file_version(CARDS_PATH)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_name = f"cards-{stamp}-{old_version[:8]}.csv"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(CARDS_PATH, backup_path)

    payload = serialize_cards(cards)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix="cards-", suffix=".tmp", dir=ROOT
    )
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, CARDS_PATH)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return file_version(CARDS_PATH), backup_name


class StoryHandler(SimpleHTTPRequestHandler):
    server_version = "StoryControl/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json(200, {"ok": True})
            return
        if path == "/api/story":
            try:
                cards = read_cards(CARDS_PATH)
                baseline = read_cards(BASELINE_PATH) if BASELINE_PATH.exists() else []
                self.send_json(
                    200,
                    {
                        "cards": cards,
                        "baseline": baseline,
                        "version": file_version(CARDS_PATH),
                        "source": CARDS_PATH.name,
                        "baselineSource": BASELINE_PATH.name if baseline else None,
                        "modifiedAt": datetime.fromtimestamp(
                            CARDS_PATH.stat().st_mtime
                        ).isoformat(timespec="seconds"),
                    },
                )
            except (OSError, ValueError) as error:
                self.send_json(500, {"error": str(error)})
            return
        super().do_GET()

    def do_PUT(self) -> None:
        if urlparse(self.path).path != "/api/cards":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 5_000_000:
                raise ValueError("请求体为空或超过 5 MB")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            expected_version = str(payload.get("expectedVersion") or "")
            current_version = file_version(CARDS_PATH)
            if expected_version and expected_version != current_version:
                self.send_json(
                    409,
                    {
                        "error": "cards.csv 已被其他程序修改，请重新载入后再保存。",
                        "currentVersion": current_version,
                    },
                )
                return
            cards = validate_cards(payload.get("cards"))
            version, backup = write_cards(cards)
            build = subprocess.run(
                [sys.executable, str(ROOT / "build.py")],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            build_output = (build.stdout + "\n" + build.stderr).strip()
            if build.returncode:
                shutil.copy2(BACKUP_DIR / backup, CARDS_PATH)
                subprocess.run(
                    [sys.executable, str(ROOT / "build.py")],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.send_json(
                    400,
                    {
                        "error": "构建校验未通过，cards.csv 已恢复。\n" + build_output[-1600:],
                        "buildOutput": build_output,
                    },
                )
                return
            self.send_json(
                200,
                {
                    "ok": True,
                    "version": version,
                    "backup": backup,
                    "cards": len(cards),
                    "buildOutput": build_output,
                    "modifiedAt": datetime.fromtimestamp(
                        CARDS_PATH.stat().st_mtime
                    ).isoformat(timespec="seconds"),
                },
            )
        except (json.JSONDecodeError, UnicodeDecodeError, OSError, ValueError) as error:
            self.send_json(400, {"error": str(error)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local story control room")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    host = "127.0.0.1"
    server = ThreadingHTTPServer((host, args.port), StoryHandler)
    print(f"Story control room: http://{host}:{args.port}/story-control.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
