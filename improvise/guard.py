"""Self-protection: Improvise backs itself up and recovers from bad updates.

- backup()            zip of everything that is yours: experience memory, skills,
                      teams, knowledge, settings (~/.improvise, without big outputs).
                      Taken automatically once a day, the last 14 are kept.
- restore(zip)        put a backup back (the current state is backed up first).
- selftest()          fast built-in check that the program works (no model needed).
- update()            safe self-update of the program from GitHub:
                      backup -> remember the working version -> pull -> selftest ->
                      if anything fails, return to the last working version.
- workspace history   every file the AI overwrites in its workspace keeps its old
                      version in workspace/.history (see coding.py).
"""

from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

KEEP = 14
SKIP_DIRS = {"backups", "output"}


def _home() -> Path:
    from .config import load
    return load().home


def backup_dir() -> Path:
    d = _home() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def backup(label: str = "manual") -> Path:
    home = _home()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = backup_dir() / f"improvise_{stamp}_{label}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in home.rglob("*"):
            rel = f.relative_to(home)
            if f.is_file() and rel.parts[0] not in SKIP_DIRS:
                z.write(f, rel.as_posix())
    _prune()
    return out


def _prune() -> None:
    files = sorted(backup_dir().glob("improvise_*.zip"))
    for f in files[:-KEEP]:
        f.unlink(missing_ok=True)


def list_backups() -> list[Path]:
    return sorted(backup_dir().glob("improvise_*.zip"))


def auto_backup() -> Path | None:
    """Once a day, cheap to call on every start."""
    today = dt.datetime.now().strftime("%Y%m%d")
    if any(f.name.startswith(f"improvise_{today}") for f in list_backups()):
        return None
    home = _home()
    if not any(p for p in home.iterdir() if p.name not in SKIP_DIRS):
        return None
    return backup("auto")


def restore(zip_path: str | Path) -> Path:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)
    safety = backup("before-restore")
    from . import memory as memory_mod
    if memory_mod._default is not None:  # release the database file (Windows locks open files)
        memory_mod._default.close()
        memory_mod._default = None
    home = _home()
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            target = (home / name).resolve()
            if home.resolve() not in target.parents:
                raise ValueError(f"unsafe path in backup: {name}")
        z.extractall(home)
    return safety


# --------------------------------------------------------------------------- program health

def selftest() -> dict:
    """Quick end-to-end check of the program itself (no language model needed)."""
    results: dict[str, str] = {}

    def check(name, fn):
        try:
            fn()
            results[name] = "ok"
        except Exception as e:  # noqa: BLE001
            results[name] = f"FAIL: {e}"

    def tools():
        from .tools import load_all
        reg = load_all()
        assert {"takt_time", "oee", "roi", "layout_line", "use_skill"} <= set(reg)

    def calcs():
        from .calc.line import takt_time
        from .calc.oee import oee
        assert takt_time(20000, 2, 8, 60)["takt_time_s"] == 2.52
        assert abs(oee(420, 47, 1.0, 19271, 18848)["oee"] - 0.748) < 0.002

    def skills():
        from .skills import load_skills
        assert len(load_skills()) >= 10

    def memory():
        import tempfile
        from .memory import Memory
        with tempfile.TemporaryDirectory() as t:
            m = Memory(Path(t) / "x.db")
            m.add_feedback("selftest", "rule")
            assert m.stats()["feedback_rules"] == 1
            m.close()

    def bench_refs():
        from . import bench
        for item in bench.load_items():
            bench.expected_values(item)

    for n, f in [("tools", tools), ("calculations", calcs), ("skills", skills), ("memory", memory),
                 ("benchmark", bench_refs)]:
        check(n, f)
    results["ok"] = all(v == "ok" for v in results.values())
    return results


def _repo() -> Path | None:
    root = Path(__file__).resolve().parent.parent
    return root if (root / ".git").exists() else None


def _git(*args: str, repo: Path) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _selftest_subprocess(repo: Path) -> bool:
    """Run the self-test in a fresh interpreter so the NEW code is tested."""
    r = subprocess.run([sys.executable, "-m", "improvise.cli", "selftest", "--quiet"], cwd=repo,
                       capture_output=True, text=True)
    return r.returncode == 0


def update(log=print) -> bool:
    repo = _repo()
    if not repo:
        log("Not a git installation - update with pip instead.")
        return False
    if shutil.which("git") is None:
        log("git is not installed.")
        return False
    good = _git("rev-parse", "HEAD", repo=repo)
    (_home() / "last_good_version.txt").write_text(good, encoding="utf-8")
    log(f"backup: {backup('before-update')}")
    if _git("status", "--porcelain", "--untracked-files=no", repo=repo):
        log("You have local changes to the program; they are stashed first (git stash).")
        _git("stash", "push", "-m", "improvise-update", repo=repo)
    try:
        _git("pull", "--ff-only", repo=repo)
    except subprocess.CalledProcessError as e:
        log(f"update failed ({e.stderr.strip()[:200]}); nothing changed.")
        return False
    new = _git("rev-parse", "HEAD", repo=repo)
    if new == good:
        log("Already up to date.")
        return True
    if _selftest_subprocess(repo):
        log(f"Updated {good[:7]} -> {new[:7]}; self-test passed.")
        (_home() / "last_good_version.txt").write_text(new, encoding="utf-8")
        return True
    log(f"Self-test FAILED on {new[:7]} - rolling back to {good[:7]}.")
    _git("checkout", good, repo=repo)
    log("Rolled back. Run 'git checkout main' later to try the update again.")
    return False


def rollback(log=print) -> bool:
    repo = _repo()
    f = _home() / "last_good_version.txt"
    if not repo or not f.exists():
        log("No recorded working version.")
        return False
    good = f.read_text(encoding="utf-8").strip()
    _git("checkout", good, repo=repo)
    log(f"Program returned to the last working version {good[:7]}.")
    return True
