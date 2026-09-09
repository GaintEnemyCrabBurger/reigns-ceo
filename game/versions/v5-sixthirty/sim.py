"""沿用 sim.py --smart 入口；直接模拟浏览器使用的同一份 JavaScript。"""
import shutil
import subprocess
import sys
from pathlib import Path

node = shutil.which('node')
if not node:
    raise SystemExit('需要 Node.js；模拟与浏览器共用 logic.js，不另写一套近似规则。')
raise SystemExit(subprocess.call([node, str(Path(__file__).with_name('simulate.js')), *sys.argv[1:]]))
