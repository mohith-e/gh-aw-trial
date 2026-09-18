#!/usr/bin/env python3
"""
Change validator for dcs_process_1 -- syntax gate with AI diagnosis and a rollback plan.

Run it before opening a PR (the .githooks/pre-push hook does this automatically), and again
in CI as the authoritative check:

    python3 validate.py                      # files changed vs the branch's upstream
    python3 validate.py --base origin/master
    python3 validate.py --all                # every pipeline .py in the tier
    python3 validate.py --files a.py b.py    # explicit paths
    python3 validate.py --no-ai              # deterministic only
    python3 validate.py --rollback           # restore the last compiling version of broken files
    python3 validate.py --json               # machine-readable, for CI
    python3 validate.py --check-pins         # every third-party import has a requirement.txt pin

WHY IT IS ORDERED THE WAY IT IS
-------------------------------
1. The deterministic check runs FIRST and decides pass/fail. CPython's own parser is the only
   authority on whether a file is valid Python; a model can miss a broken file or invent one,
   and a gate that can hallucinate is a gate people learn to bypass.
2. The AI runs SECOND, on the errors already found, and only *explains and suggests*: cause,
   a concrete fix, and rollback advice. That is the part a parser is bad at.
3. If the AI is unavailable for ANY reason -- no credentials, rate limited, token/context
   limit, truncated output, timeout, unparseable answer -- the run still reports every syntax
   error, a rule-based suggestion, and a rollback command. The AI never changes the verdict,
   so its absence can never mask a broken file.

TARGET INTERPRETER
------------------
Syntax validity depends on the Python version: 3.10+ accepts `match` statements that 3.9.15
rejects at import time, so validating with a newer interpreter would pass code that breaks the
pipeline. Every compile check therefore runs in the tier's own interpreter (.venv, else the
pyenv version named in .python-version, else ~/.pyenv/versions/dcs_env), not in whatever
python3 happens to launch this script. If none is found the run says so loudly.

AI BACKENDS, in priority order (first usable one wins):
  1. $DCS_VALIDATOR_AI_CMD  -- shell command; prompt on stdin, answer on stdout (CI / testing)
  2. the `anthropic` SDK    -- when installed and credentials resolve (pip install anthropic)
  3. the `claude` CLI       -- `claude -p`, uses an existing Claude Code login, no API key
Environment: DCS_VALIDATOR_AI_MODEL (default claude-opus-5), DCS_VALIDATOR_AI_TIMEOUT (90s),
DCS_TARGET_PYTHON (pin the interpreter to compile against -- used by CI, which has no .venv).

Exit codes: 0 = no syntax errors, 1 = syntax errors found, 2 = the validator itself failed.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

# git exports GIT_DIR to every hook it runs. With GIT_DIR set and no GIT_WORK_TREE, git stops
# discovering the work tree from the filesystem and treats the CWD as the work tree instead, so
# `rev-parse --show-toplevel` returns dcs_process_1/ rather than the repo root. Every tracked
# file then looks untracked, the changed-file diff collapses, and the run silently degrades into
# a full-tier sweep that blocks the push over files the developer never touched. That is the
# false failure this gate exists to avoid, and it fires only under the pre-push hook -- CI sets
# no GIT_DIR, which is why CI stayed green while the hook was wrong. Drop the inherited
# pointers and let git rediscover the repo the ordinary way.
for _git_env in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
    os.environ.pop(_git_env, None)

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_VERSION = 1

# Directories that hold no pipeline source of ours. .validator_backups is where --rollback
# parks broken files on purpose, so walking into it would re-report every file it saved.
SKIP_DIRS = {".venv", "__pycache__", ".git", ".githooks", "logs", "processed", "input",
             "template", ".validator_backups"}

AI_MODEL = os.environ.get("DCS_VALIDATOR_AI_MODEL", "claude-opus-5")
AI_MODEL_EXPLICIT = "DCS_VALIDATOR_AI_MODEL" in os.environ
AI_TIMEOUT = int(os.environ.get("DCS_VALIDATOR_AI_TIMEOUT", "90"))
AI_MAX_TOKENS = 8000
AI_PROMPT_BUDGET = 40000        # total bytes of prompt we will spend in one run
CONTEXT_RADIUS = 15             # source lines of context sent per error
MAX_ROLLBACK_SCAN = 25          # commits to search backwards for a compiling version

PAIRS = {"(": ")", "[": "]", "{": "}"}


# --------------------------------------------------------------------------- git helpers

_ROOT = None


def repo_root():
    global _ROOT
    if _ROOT is None:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              cwd=REPO_DIR, capture_output=True, text=True)
        _ROOT = (proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip()
                 else os.path.dirname(os.path.dirname(REPO_DIR)))
    return _ROOT


def git(*args, binary=False):
    """Always runs from the repo root, so every pathspec we pass is root-relative -- the same
    form `git diff --name-only` hands back. Running from this subdirectory instead silently
    turned `dcs-parsing/dcs_process_1/x.py` into a path relative to dcs_process_1/."""
    proc = subprocess.run(
        ["git"] + list(args), cwd=repo_root(), capture_output=True, text=not binary
    )
    out = proc.stdout if binary else proc.stdout.rstrip("\n")
    return proc.returncode, out, (proc.stderr if binary else proc.stderr.strip())


def default_base_ref():
    """The branch's upstream if it has one -- that is what "about to be pushed" means --
    else origin/master, the merge target. Same rule as run_pre_merge_tests.py."""
    code, out, _ = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if code == 0 and out:
        return out
    return "origin/master"


def is_tracked(rel_path):
    code, out, _ = git("ls-files", "--error-unmatch", rel_path)
    return code == 0 and bool(out)


# --------------------------------------------------------------- target interpreter

def _py_version(exe):
    try:
        proc = subprocess.run(
            [exe, "-c", "import sys;print('%d.%d.%d' % sys.version_info[:3])"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def find_target_python():
    """The interpreter the pipeline actually runs under. Returns
    (executable, version, matches_pinned_version, note).

    $DCS_TARGET_PYTHON overrides discovery, for environments that have no .venv and no pyenv --
    CI, most obviously, where the runner installs its own 3.9 and we want the gate to say so
    explicitly rather than quietly falling back to whatever launched it.
    """
    pinned = ""
    pin_file = os.path.join(REPO_DIR, ".python-version")
    if os.path.exists(pin_file):
        with open(pin_file) as fh:
            pinned = fh.read().strip()

    override = os.environ.get("DCS_TARGET_PYTHON")
    if override:
        exe = shutil.which(override) or override
        version = _py_version(exe)
        if version:
            series = pinned.rsplit(".", 1)[0] if pinned else ""
            matches = (not pinned) or version == pinned or version.startswith(series)
            note = "" if matches else (
                "DCS_TARGET_PYTHON=%s is %s, but .python-version pins %s" % (override, version, pinned))
            return exe, version, matches, note
        return (sys.executable, "%d.%d.%d" % sys.version_info[:3], False,
                "DCS_TARGET_PYTHON=%s could not be run -- falling back to %s" % (override, sys.executable))

    candidates = [os.path.join(REPO_DIR, ".venv", "bin", "python")]
    if pinned:
        candidates.append(os.path.expanduser("~/.pyenv/versions/%s/bin/python" % pinned))
    candidates.append(os.path.expanduser("~/.pyenv/versions/dcs_env/bin/python"))

    seen = []
    for exe in candidates:
        if not os.path.exists(exe):
            continue
        version = _py_version(exe)
        if not version:
            continue
        seen.append((exe, version))
        if not pinned or version == pinned or version.startswith(pinned.rsplit(".", 1)[0]):
            return exe, version, True, ""
    if seen:
        exe, version = seen[0]
        return exe, version, False, "found %s (%s), but .python-version pins %s" % (exe, version, pinned)

    version = "%d.%d.%d" % sys.version_info[:3]
    note = (
        "no tier interpreter found (.venv or pyenv %s) -- falling back to %s (%s). "
        "Syntax accepted here may still fail on the server." % (pinned or "?", sys.executable, version)
    )
    return sys.executable, version, False, note


# ------------------------------------------------------------------- compile probe

# Runs inside the TARGET interpreter, so both the verdict and the wording of the error
# message come from the CPython version the pipeline will actually import under.
COMPILE_PROBE = r'''
import json, sys
out = []
for path in sys.argv[1:]:
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        out.append({"file": path, "type": "OSError", "msg": str(exc),
                    "line": None, "col": None, "text": None})
        continue
    try:
        src = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        out.append({"file": path, "type": "UnicodeDecodeError", "msg": str(exc),
                    "line": None, "col": None, "text": None})
        continue
    try:
        compile(src, path, "exec", dont_inherit=True)
    except SyntaxError as exc:
        out.append({"file": path, "type": type(exc).__name__, "msg": exc.msg,
                    "line": exc.lineno, "col": exc.offset, "text": exc.text})
    except ValueError as exc:
        out.append({"file": path, "type": "ValueError", "msg": str(exc),
                    "line": None, "col": None, "text": None})
print(json.dumps(out))
'''


def compile_check(paths, target_py):
    """Compile every path in the target interpreter. Returns {abs_path: error_dict}."""
    errors = {}
    for chunk_start in range(0, len(paths), 150):
        chunk = paths[chunk_start:chunk_start + 150]
        proc = subprocess.run(
            [target_py, "-c", COMPILE_PROBE] + chunk,
            capture_output=True, text=True, timeout=600,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            raise RuntimeError(
                "compile probe failed under %s: %s" % (target_py, (proc.stderr or "no output").strip())
            )
        for item in json.loads(proc.stdout):
            errors[item["file"]] = item
    return errors


def source_compiles(source_bytes, target_py):
    """Does this blob compile under the target interpreter? Used to find a rollback target."""
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    try:
        tmp.write(source_bytes)
        tmp.close()
        return not compile_check([tmp.name], target_py)
    except Exception:
        return False
    finally:
        os.unlink(tmp.name)


# ------------------------------------------------------- deterministic diagnosis

def scan_structure(src):
    """Tolerantly locate unclosed brackets, a mismatched closer, and an unterminated string.

    Written to survive syntactically invalid input, which is the whole point -- `tokenize`
    raises on exactly the files we care about. Its output is *evidence* offered alongside the
    interpreter's own message, never a competing verdict.
    """
    stack, mismatch, unterminated = [], None, None
    state, quote, triple, str_start = "code", "", False, 0
    line, col, i, n = 1, 0, 0, len(src)

    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
            col = 0
            if state == "comment":
                state = "code"
            elif state == "str" and not triple:
                if unterminated is None:
                    unterminated = {"line": str_start, "quote": quote, "triple": False}
                state = "code"
            i += 1
            continue
        col += 1
        if state == "code":
            three = src[i:i + 3]
            if ch == "#":
                state = "comment"
            elif three in ('"""', "'''"):
                state, quote, triple, str_start = "str", three, True, line
                i += 3
                col += 2
                continue
            elif ch in "\"'":
                state, quote, triple, str_start = "str", ch, False, line
            elif ch in PAIRS:
                stack.append({"char": ch, "line": line, "col": col})
            elif ch in ")]}":
                if stack and PAIRS[stack[-1]["char"]] == ch:
                    stack.pop()
                elif mismatch is None:
                    mismatch = {
                        "char": ch, "line": line, "col": col,
                        "expected": PAIRS[stack[-1]["char"]] if stack else None,
                        "opened_line": stack[-1]["line"] if stack else None,
                    }
        elif state == "str":
            if ch == "\\":
                if i + 1 < n and src[i + 1] == "\n":
                    line += 1
                    col = 0
                i += 2
                continue
            three = src[i:i + 3]
            if triple and three == quote:
                state = "code"
                i += 3
                col += 2
                continue
            if not triple and ch == quote:
                state = "code"
        i += 1

    if state == "str" and unterminated is None:
        unterminated = {"line": str_start, "quote": quote, "triple": triple}
    return stack, mismatch, unterminated


BLOCK_KEYWORDS = (
    "if", "elif", "else", "for", "while", "def", "class", "try", "except",
    "finally", "with",
)


def _previous_code_line(lines, lineno):
    """The nearest non-blank, non-comment line above lineno. In 3.9 a bare "invalid syntax"
    frequently points at the line *after* the real mistake, so this is worth surfacing."""
    idx = lineno - 2
    while idx >= 0:
        stripped = lines[idx].strip()
        if stripped and not stripped.startswith("#"):
            return idx + 1, lines[idx]
        idx -= 1
    return None, None


def deterministic_diagnosis(err, src, lines, version):
    """Map the interpreter's own message (the authoritative signal) to a cause and a fix.

    Keyed on CPython's error text rather than on guesses about the code, so it stays correct
    across versions: a message we do not recognise degrades to the structural evidence from
    scan_structure instead of inventing an explanation.
    """
    msg = err.get("msg") or ""
    lineno = err.get("line") or 0
    etype = err.get("type") or "SyntaxError"
    stack, mismatch, unterminated = scan_structure(src)
    evidence = []

    if etype == "TabError" or "tabs and spaces" in msg:
        return ("indentation mixes tab and space characters",
                "make the indentation of the block containing line %d consistently spaces "
                "(this file's convention is 4 spaces)" % lineno,
                evidence)

    if etype == "UnicodeDecodeError":
        return ("the file is not valid UTF-8",
                "re-save it as UTF-8; a byte copied from Excel or a PDF is the usual cause", evidence)

    if etype == "OSError":
        return ("the file could not be read", "check the path and permissions", evidence)

    m = re.search(r"Missing parentheses in call to '(\w+)'", msg)
    if m:
        return ("Python 2 statement syntax -- `%s` is a function in Python 3" % m.group(1),
                "wrap the argument in parentheses: %s(...)" % m.group(1), evidence)

    if "was never closed" in msg or "unexpected EOF" in msg or "EOF in multi-line" in msg or (
        "closing parenthesis" in msg
    ):
        if stack:
            opener = stack[0]
            return ("the '%s' opened on line %d (column %d) is never closed" % (
                        opener["char"], opener["line"], opener["col"]),
                    "close it, or delete it if the call was meant to end on that line",
                    ["unclosed %s at line %d col %d" % (o["char"], o["line"], o["col"]) for o in stack])
        return ("the file ends inside an unfinished statement",
                "complete the statement at the end of the file", evidence)

    if mismatch and ("invalid syntax" in msg or "closing parenthesis" in msg or "unmatched" in msg):
        if mismatch["expected"]:
            return ("'%s' on line %d closes a '%s' opened on line %d -- expected '%s'" % (
                        mismatch["char"], mismatch["line"],
                        {v: k for k, v in PAIRS.items()}[mismatch["expected"]],
                        mismatch["opened_line"], mismatch["expected"]),
                    "change it to '%s', or fix the bracket order" % mismatch["expected"], evidence)
        return ("'%s' on line %d closes a bracket that was never opened" % (
                    mismatch["char"], mismatch["line"]),
                "delete it, or add the matching opener", evidence)

    if "unterminated triple-quoted" in msg or (unterminated and unterminated.get("triple")):
        start = unterminated["line"] if unterminated else lineno
        return ("the triple-quoted string opened on line %d is never closed" % start,
                "close it with %s" % (unterminated["quote"] if unterminated else '"""'), evidence)

    if "EOL while scanning string literal" in msg or "unterminated string literal" in msg:
        return ("the string literal on line %d is missing its closing quote" % lineno,
                "add the closing quote, or use a triple-quoted string if the text spans lines",
                evidence)

    if "expected ':'" in msg:
        return ("the block header on line %d has no trailing ':'" % lineno,
                "add ':' at the end of line %d" % lineno, evidence)

    if "expected an indented block" in msg:
        return ("the block opened above line %d has no body" % lineno,
                "indent the body one level, or add `pass` as a placeholder", evidence)

    if "unexpected indent" in msg:
        return ("line %d is indented further than the block it belongs to" % lineno,
                "dedent line %d to match the surrounding block" % lineno, evidence)

    if "unindent does not match" in msg:
        return ("line %d dedents to a column that matches no enclosing block" % lineno,
                "align line %d with one of the enclosing blocks; check for a stray tab" % lineno,
                evidence)

    m = re.search(r"cannot assign to (\w[\w ]*)", msg)
    if m:
        return ("line %d assigns to a %s" % (lineno, m.group(1)),
                "use '==' if you meant a comparison, or assign to a name instead", evidence)

    m = re.search(r"invalid (?:character|non-printable character) '?(.)'?", msg)
    if m:
        return ("line %d contains the non-ASCII character %r" % (lineno, m.group(1)),
                "replace it with its ASCII equivalent -- smart quotes and dashes pasted from "
                "Excel or email are the usual source", evidence)

    if "Perhaps you forgot a comma" in msg:
        return ("two expressions on line %d are juxtaposed with no separator" % lineno,
                "add the missing comma", evidence)

    if "positional argument follows keyword argument" in msg:
        return ("a positional argument appears after a keyword argument on line %d" % lineno,
                "move the positional argument before the first keyword argument", evidence)

    if "leading zeros in decimal integer" in msg:
        return ("a decimal literal on line %d has a leading zero" % lineno,
                "drop the leading zero, or quote it if it is an identifier like '007'", evidence)

    # Syntax the pipeline's own interpreter is too old for. This is the class of bug that a
    # newer local python would silently wave through -- valid where it was written, an
    # ImportError on the server -- so name the version explicitly.
    minor = 0
    try:
        minor = int(version.split(".")[1])
    except (IndexError, ValueError):
        pass
    cur = (err.get("text") or (lines[lineno - 1] if 0 < lineno <= len(lines) else "") or "").strip()
    if minor < 10 and re.match(r"(match|case)\b.*:$", cur):
        return ("`%s` is a match statement -- structural pattern matching needs Python 3.10, "
                "the target here is %s" % (cur.split()[0], version),
                "rewrite it as if/elif, or the pipeline will fail on import", evidence)
    if minor < 11 and re.match(r"except\s*\*", cur):
        return ("`except*` needs Python 3.11, the target here is %s" % version,
                "use a plain `except` clause", evidence)

    # A block header on the error line with no ':'. Python 3.9 reports this as a bare
    # "invalid syntax" with the caret at end of line, so the message alone does not say it.
    # Guarded: an unclosed bracket anywhere, or a line ending in an operator, means this is a
    # legitimate multi-line header and the real error is elsewhere.
    CONTINUES = ("\\", ",", "+", "-", "*", "/", "=", "<", ">", "%", "&", "|", "^",
                 "(", "[", "{", " and", " or", " not", " in", " is")
    head_match = re.match(r"(\w+)\b", cur)
    if (head_match and head_match.group(1) in BLOCK_KEYWORDS and not cur.endswith(":")
            and not stack and not cur.endswith(CONTINUES)):
        return ("the `%s` header on line %d has no trailing ':'" % (head_match.group(1), lineno),
                "add ':' at the end of line %d" % lineno, evidence)

    # Unrecognised message: offer structure, and the previous line, without asserting a cause.
    if stack:
        evidence.append("unclosed %s opened at line %d col %d" % (
            stack[0]["char"], stack[0]["line"], stack[0]["col"]))
    prev_no, prev_text = _previous_code_line(lines, lineno) if lineno else (None, None)
    if prev_no:
        evidence.append("previous code line %d: %s" % (prev_no, prev_text.strip()))
        head = prev_text.strip().split(" ")[0].rstrip("(:")
        if head in BLOCK_KEYWORDS and not prev_text.rstrip().endswith(":"):
            return ("line %d is rejected because the `%s` header on line %d has no ':'" % (
                        lineno, head, prev_no),
                    "add ':' at the end of line %d" % prev_no, evidence)
    return ("the parser rejected line %d: %s" % (lineno, msg),
            "check line %d and the line above it; the reported position is where the parser "
            "gave up, not always where the mistake is" % lineno,
            evidence)


# ------------------------------------------------------------------ rollback plan

def rollback_plan(abs_path, rel_path, target_py):
    """Find the newest revision of this file that compiles, and how to get back to it."""
    if not is_tracked(rel_path):
        return {
            "kind": "quarantine",
            "revision": None,
            "revision_subject": None,
            "command": None,
            "note": "file is untracked -- there is no previous version to restore. "
                    "--rollback moves it aside into .validator_backups/ instead.",
        }

    code, out, _ = git("log", "--format=%H", "-n", str(MAX_ROLLBACK_SCAN), "--", rel_path)
    history = [h for h in out.splitlines() if h] if code == 0 else []

    for rev in ["HEAD"] + history:
        code, blob, _ = git("show", "%s:%s" % (rev, rel_path), binary=True)
        if code != 0:
            continue
        if not source_compiles(blob, target_py):
            continue
        code, subject, _ = git("log", "-1", "--format=%h %s (%ad)", "--date=short", rev)
        if rev == "HEAD":
            return {
                "kind": "git-checkout",
                "revision": "HEAD",
                "revision_subject": subject if code == 0 else None,
                "command": "git checkout -- %s" % rel_path,
                "note": "HEAD compiles -- the breakage is only in the working tree, so this "
                        "discards uncommitted changes to this file.",
            }
        return {
            "kind": "git-checkout",
            "revision": rev,
            "revision_subject": subject if code == 0 else None,
            "command": "git checkout %s -- %s" % (rev, rel_path),
            "note": "newest revision of this file that compiles under Python %s." % target_py,
        }

    return {
        "kind": "none",
        "revision": None,
        "revision_subject": None,
        "command": None,
        "note": "no revision in the last %d commits touching this file compiles -- the file "
                "may have been broken before it was committed. Fix forward." % MAX_ROLLBACK_SCAN,
    }


def apply_rollback(finding, root, backup_dir):
    """Restore (or quarantine) one broken file, after saving the broken copy."""
    plan = finding["rollback"]
    rel, abs_path = finding["file"], finding["abs_path"]

    backup_target = os.path.join(backup_dir, rel)
    os.makedirs(os.path.dirname(backup_target), exist_ok=True)
    shutil.copy2(abs_path, backup_target)

    if plan["kind"] == "git-checkout":
        args = ["checkout", "--", rel] if plan["revision"] == "HEAD" else \
               ["checkout", plan["revision"], "--", rel]
        code, _, err = git(*args)
        if code != 0:
            return False, "git checkout failed: %s" % err
        return True, "restored from %s (broken copy saved to %s)" % (
            plan["revision"], os.path.relpath(backup_target, root))
    if plan["kind"] == "quarantine":
        os.unlink(abs_path)
        return True, "moved aside to %s (untracked file, nothing to restore)" % (
            os.path.relpath(backup_target, root))
    return False, plan["note"]


# ------------------------------------------------------------------------ AI layer

class AIUnavailable(Exception):
    """Raised for every AI failure mode. Always caught -- it downgrades the run, never fails it."""


AI_SYSTEM = (
    "You diagnose Python syntax errors in a legacy ETL codebase. The target interpreter is "
    "CPython {version} -- never suggest syntax newer than that (no match statements, no "
    "f-string nesting beyond 3.9, no PEP 604 unions in runtime code). The error has already "
    "been confirmed by the interpreter; do not question whether it is real. Reply with one "
    "JSON object and nothing else."
)

AI_SCHEMA_HINT = """Reply with exactly this JSON shape and no prose, no markdown fence:
{"cause": "one sentence, what is actually wrong",
 "fix": "one sentence, the minimal edit that fixes it",
 "corrected_lines": [{"line": <int>, "text": "<the full corrected source line>"}],
 "rollback_advice": "one sentence: is reverting this file safer than fixing forward, and why",
 "confidence": "high|medium|low"}"""


def ai_backend():
    """(kind, detail, reason_if_unavailable)."""
    cmd = os.environ.get("DCS_VALIDATOR_AI_CMD")
    if cmd:
        return "command", cmd, None
    try:
        import anthropic  # noqa: F401
        has_creds = any(os.environ.get(k) for k in (
            "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_FEDERATION_RULE_ID",
        )) or os.path.isdir(os.path.expanduser("~/.config/anthropic"))
        if has_creds:
            return "sdk", None, None
    except ImportError:
        pass
    claude = shutil.which("claude")
    if claude:
        return "claude-cli", claude, None
    return None, None, ("no AI backend: set DCS_VALIDATOR_AI_CMD, `pip install anthropic` with "
                        "credentials, or install the claude CLI")


def _call_sdk(prompt, version):
    import anthropic
    client = anthropic.Anthropic(timeout=float(AI_TIMEOUT), max_retries=1)
    kwargs = dict(
        model=AI_MODEL,
        max_tokens=AI_MAX_TOKENS,
        system=AI_SYSTEM.format(version=version),
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        resp = client.messages.create(output_config={"effort": "medium"}, **kwargs)
    except TypeError:
        resp = client.messages.create(**kwargs)   # SDK predates output_config
    except Exception as exc:
        raise AIUnavailable("%s: %s" % (type(exc).__name__, exc))
    if getattr(resp, "stop_reason", None) == "max_tokens":
        raise AIUnavailable("model output hit max_tokens (%d) and was truncated" % AI_MAX_TOKENS)
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise AIUnavailable("model returned no text (stop_reason=%s)" % getattr(resp, "stop_reason", "?"))
    return text


def _call_process(argv_or_cmd, stdin_text, shell):
    """stdin_text is what the backend reads on stdin -- the prompt for a $DCS_VALIDATOR_AI_CMD
    filter, and "" for the claude CLI (which takes the prompt as an argument and would block
    on an inherited stdin)."""
    try:
        proc = subprocess.run(
            argv_or_cmd, input=stdin_text, capture_output=True, text=True,
            timeout=AI_TIMEOUT, shell=shell, cwd=REPO_DIR,
        )
    except subprocess.TimeoutExpired:
        raise AIUnavailable("backend timed out after %ds" % AI_TIMEOUT)
    except OSError as exc:
        raise AIUnavailable("backend could not start: %s" % exc)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        raise AIUnavailable("backend exited %d: %s" % (
            proc.returncode, detail[-1][:200] if detail else "no output"))
    if not proc.stdout.strip():
        raise AIUnavailable("backend returned empty output")
    return proc.stdout


def extract_json(text):
    """Pull one JSON object out of a reply that may be wrapped in prose or a fence."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fence.group(1) if fence else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise AIUnavailable("no JSON object in the model's reply")
        candidate = text[start:end + 1]
    try:
        parsed = json.loads(candidate)
    except ValueError as exc:
        raise AIUnavailable("model reply was not valid JSON (%s)" % exc)
    if not isinstance(parsed, dict):
        raise AIUnavailable("model reply was not a JSON object")
    return parsed


def build_prompt(finding, lines, version):
    lineno = finding["line"] or 1
    lo = max(1, lineno - CONTEXT_RADIUS)
    hi = min(len(lines), lineno + CONTEXT_RADIUS)
    numbered = "\n".join(
        "%s%5d | %s" % (">" if n == lineno else " ", n, lines[n - 1]) for n in range(lo, hi + 1)
    )
    return (
        "File: %s\nTarget interpreter: CPython %s\n"
        "Interpreter error: %s: %s (line %s, column %s)\n\n"
        "Source (the marked line is where the parser stopped):\n%s\n\n%s"
    ) % (finding["file"], version, finding["error_type"], finding["error"],
         finding["line"], finding["column"], numbered, AI_SCHEMA_HINT)


def normalise_ai(raw):
    """Keep only the fields we promise, coerced to the shapes the report declares."""
    lines_out = []
    for item in raw.get("corrected_lines") or []:
        if isinstance(item, dict) and "text" in item:
            try:
                lines_out.append({"line": int(item.get("line") or 0), "text": str(item["text"])})
            except (TypeError, ValueError):
                continue
    confidence = str(raw.get("confidence") or "").lower()
    return {
        "cause": str(raw.get("cause") or "").strip(),
        "fix": str(raw.get("fix") or "").strip(),
        "corrected_lines": lines_out,
        "rollback_advice": str(raw.get("rollback_advice") or "").strip(),
        "confidence": confidence if confidence in ("high", "medium", "low") else "unknown",
    }


def run_ai(findings, sources, version, max_files):
    """Attach an AI diagnosis to each finding. Degrades per-file; never raises."""
    kind, detail, reason = ai_backend()
    state = {"backend": kind or "none", "model": None, "status": "unavailable",
             "reason": reason, "files_diagnosed": 0, "files_skipped": 0}
    if not kind:
        return state
    state["model"] = AI_MODEL if kind in ("sdk", "command") or AI_MODEL_EXPLICIT else "cli-default"
    state["reason"] = None

    spent, failures = 0, []
    for finding in findings[:max_files]:
        prompt = build_prompt(finding, sources[finding["abs_path"]]["lines"], version)
        if spent + len(prompt) > AI_PROMPT_BUDGET:
            finding["ai_status"] = "skipped: prompt budget (%d bytes) exhausted" % AI_PROMPT_BUDGET
            state["files_skipped"] += 1
            continue
        spent += len(prompt)
        try:
            if kind == "sdk":
                text = _call_sdk(prompt, version)
            elif kind == "command":
                # The SDK path sends AI_SYSTEM as a system prompt; a process backend has no
                # such channel, so it goes in front of the prompt instead.
                text = _call_process(
                    detail, AI_SYSTEM.format(version=version) + "\n\n" + prompt, shell=True)
            else:
                argv = [detail, "-p", AI_SYSTEM.format(version=version) + "\n\n" + prompt]
                if AI_MODEL_EXPLICIT:
                    argv[1:1] = ["--model", AI_MODEL]
                text = _call_process(argv, "", shell=False)
            finding["ai"] = normalise_ai(extract_json(text))
            finding["ai_status"] = "ok"
            state["files_diagnosed"] += 1
        except AIUnavailable as exc:
            finding["ai_status"] = "failed: %s" % exc
            failures.append(str(exc))
            state["files_skipped"] += 1
        except Exception as exc:                      # a backend surprise must not kill the gate
            finding["ai_status"] = "failed: unexpected %s: %s" % (type(exc).__name__, exc)
            failures.append("%s: %s" % (type(exc).__name__, exc))
            state["files_skipped"] += 1

    for finding in findings[max_files:]:
        finding["ai_status"] = "skipped: --ai-max-files=%d reached" % max_files
        state["files_skipped"] += 1

    if state["files_diagnosed"] and not failures:
        state["status"] = "ok"
    elif state["files_diagnosed"]:
        state["status"] = "degraded"
        state["reason"] = failures[0]
    else:
        state["status"] = "unavailable"
        state["reason"] = failures[0] if failures else "no files diagnosed"
    return state


# ----------------------------------------------------------------- target selection

def all_pipeline_files():
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO_DIR):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


# --------------------------------------------------------------------------- dependency pins

# import name -> PyPI distribution name, where they differ.
IMPORT_ALIASES = {
    "dateutil": "python-dateutil",
    "yaml": "pyyaml",
}


def _stdlib_names():
    """sys.stdlib_module_names is the interpreter's own list -- not a hand-maintained guess,
    and unlike importlib.util.find_spec() it does not require the module to be installed (CI
    deliberately does not install requirement.txt: tensorflow alone would cost minutes on every
    PR for no added signal). Needs 3.10+, which is *why* this check runs as its own CI job on a
    newer interpreter rather than inside validate.py's usual tier-pinned 3.9.15 process -- that
    interpreter choice is about compiling pipeline code correctly, not about parsing imports."""
    if sys.version_info >= (3, 10):
        return set(sys.stdlib_module_names)
    raise RuntimeError(
        "--check-pins needs Python 3.10+ (this process is running %s); run it under a newer "
        "interpreter, e.g. `python3.11 validate.py --check-pins`. The syntax/compile check is "
        "unaffected -- that always runs in the tier's own pinned interpreter regardless."
        % ".".join(map(str, sys.version_info[:3])))


def _local_names(root):
    """Every local module/package name, so `from DCS_etl_functions import x` or a package dir
    is never mistaken for a third-party distribution. Honors SKIP_DIRS -- walking into .venv
    would otherwise harvest every *installed* package's directory name as "local" and silently
    defeat the whole check."""
    names = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        names.update(dirnames)
        names.update(os.path.splitext(f)[0] for f in filenames if f.endswith(".py"))
    return names


def _read_pins(req_path):
    pinned = set()
    if os.path.isfile(req_path):
        with open(req_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    pinned.add(re.split(r"[=<>!\[;]", line)[0].strip().lower())
    return pinned


def _top_level_imports(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read(), filename=path)
    except (SyntaxError, OSError, ValueError):
        return []  # compile_check already reports a broken file; don't double-report here
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module.split(".")[0])
    return names


def check_dependency_pins():
    """Every third-party import under the tier has a pin in requirement.txt. Parser modules are
    loaded dynamically via importlib at runtime (see auto_dcs_process_integrations.py) and are
    never imported at startup, so a missing pin is otherwise invisible until that one pipeline
    runs in prod and dies on ImportError. Pure AST parse -- no package needs to be installed.

    Scoped to REPO_DIR (the dcs_process_1 tier), not repo_root() (the monorepo top level) --
    requirement.txt lives here, and the other ~40 top-level modules have their own pins this
    check has no business judging."""
    stdlib = _stdlib_names()
    # requirement.txt (singular) is what ships to the box; requirements-dev.txt covers tooling
    # that only ever runs in CI/pre-push (validate.py's own `anthropic` import). Both are pin
    # files for this tier -- an import missing from *both* is the thing worth catching.
    pinned = _read_pins(os.path.join(REPO_DIR, "requirement.txt"))
    pinned |= _read_pins(os.path.join(REPO_DIR, "requirements-dev.txt"))
    local = _local_names(REPO_DIR)

    missing = {}
    for path in all_pipeline_files():
        for name in _top_level_imports(path):
            if name in stdlib or name in local:
                continue
            dist = IMPORT_ALIASES.get(name.lower(), name.lower())
            if dist not in pinned:
                missing.setdefault(dist, set()).add(os.path.relpath(path, REPO_DIR))
    return {"pinned_count": len(pinned),
            "missing": {dist: sorted(files) for dist, files in sorted(missing.items())}}


def _git_changed(base_ref):
    files = set()
    for args in (
        ["diff", "--name-only", "%s...HEAD" % base_ref],
        ["diff", "--name-only", "HEAD"],
        ["diff", "--name-only", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        code, out, _ = git(*args)
        if code == 0:
            files.update(f for f in out.splitlines() if f.endswith(".py"))
    return sorted(files)


def changed_files(base_ref, root):
    """Root-relative changed .py paths. Delegates to run_pre_merge_tests when it is present so
    the two gates always agree on what "changed" means."""
    rel = None
    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)
    try:
        import run_pre_merge_tests
        rel = run_pre_merge_tests.changed_python_files(base_ref)
    except Exception:
        rel = _git_changed(base_ref)
    # `git diff --name-only` yields root-relative paths, but `git ls-files --others` yields
    # paths relative to the cwd git ran in -- so a returned path can be based at either. Try
    # both bases: assuming only one silently dropped every untracked file, which is exactly
    # the case worth catching (a brand-new reader script).
    out = []
    for path in rel:
        for base in (root, REPO_DIR):
            abs_path = os.path.abspath(os.path.join(base, path))
            if os.path.isfile(abs_path) and abs_path.startswith(REPO_DIR + os.sep):
                out.append(abs_path)
                break
    return sorted(set(out))


# ---------------------------------------------------------------------- reporting

def caret_line(text, column):
    if not text or not column or column < 1:
        return None
    prefix = text[:column - 1]
    return "".join("\t" if ch == "\t" else " " for ch in prefix) + "^"


def render(report, use_color):
    def paint(code, text):
        return "\033[%sm%s\033[0m" % (code, text) if use_color else text

    out = []
    interp = report["interpreter"]
    header = "dcs validator | %d file(s) checked | Python %s (%s)" % (
        report["summary"]["files_checked"], interp["version"],
        os.path.basename(os.path.dirname(os.path.dirname(interp["executable"]))) or interp["executable"])
    out.append(paint("1", header))
    if interp["note"]:
        out.append(paint("33", "  warning: %s" % interp["note"]))

    ai = report["ai"]
    label = {"ok": "32", "degraded": "33", "unavailable": "33"}.get(ai["status"], "33")
    ai_line = "  AI: %s via %s" % (ai["status"], ai["backend"])
    if ai.get("model") and ai["backend"] != "none":
        ai_line += " (%s)" % ai["model"]
    if ai.get("reason"):
        ai_line += " -- %s" % ai["reason"]
    out.append(paint(label, ai_line))
    if ai["status"] != "ok" and report["summary"]["files_with_errors"]:
        out.append(paint("33", "  falling back to the built-in rule-based diagnosis "
                               "(the verdict below does not depend on the AI)"))
    out.append("")

    if not report["findings"]:
        out.append(paint("32", "PASS: no syntax errors."))
        return "\n".join(out)

    for idx, f in enumerate(report["findings"], 1):
        out.append(paint("31;1", "[%d] %s:%s:%s" % (idx, f["file"], f["line"], f["column"])))
        out.append("    %s: %s" % (f["error_type"], f["error"]))
        if f.get("source_line"):
            out.append("    %5d | %s" % (f["line"], f["source_line"].rstrip("\n")))
            if f.get("caret"):
                out.append("          | %s" % f["caret"])
        det = f["deterministic"]
        out.append("    %s %s" % (paint("36", "cause      :"), det["cause"]))
        out.append("    %s %s" % (paint("36", "suggestion :"), det["suggestion"]))
        for item in det.get("evidence") or []:
            out.append("    %s %s" % (paint("36", "evidence   :"), item))
        if f.get("ai"):
            ai_f = f["ai"]
            out.append("    %s %s (confidence: %s)" % (
                paint("35", "AI cause   :"), ai_f["cause"], ai_f["confidence"]))
            out.append("    %s %s" % (paint("35", "AI fix     :"), ai_f["fix"]))
            for line in ai_f["corrected_lines"]:
                out.append("      %s" % paint("31", "%5d - %s" % (
                    line["line"], (f["all_lines"][line["line"] - 1]
                                   if 0 < line["line"] <= len(f.get("all_lines") or []) else "").rstrip())))
                out.append("      %s" % paint("32", "%5d + %s" % (line["line"], line["text"].rstrip())))
            if ai_f["rollback_advice"]:
                out.append("    %s %s" % (paint("35", "AI rollback:"), ai_f["rollback_advice"]))
        elif f.get("ai_status"):
            out.append("    %s %s" % (paint("33", "AI         :"), f["ai_status"]))

        rb = f["rollback"]
        if rb["command"]:
            subject = " [%s]" % rb["revision_subject"] if rb.get("revision_subject") else ""
            out.append("    %s %s%s" % (paint("33", "rollback   :"), rb["command"], subject))
            out.append("    %s %s" % (paint("33", "             "), rb["note"]))
        else:
            out.append("    %s %s" % (paint("33", "rollback   :"), rb["note"]))
        applied = f.get("rollback_applied")
        if applied:
            out.append("    %s %s" % (
                paint("32" if applied["restored"] else "31", "applied    :"), applied["detail"]))
        out.append("")

    n = len(report["findings"])
    if report["invocation"].get("rollback_applied"):
        done = sum(1 for r in report.get("rollback_results", []) if r["restored"])
        out.append(paint("32;1" if done == n else "31;1",
                         "ROLLED BACK: %d of %d file(s) restored or quarantined." % (done, n)))
        out.append("Broken copies were saved first. Re-run the validator to confirm the tree compiles.")
        return "\n".join(out)
    out.append(paint("31;1", "FAIL: %d file(s) will not compile under Python %s." % (n, interp["version"])))
    out.append("Fix the errors above, or restore the last compiling version with:")
    out.append("    python3 validate.py --rollback%s" % (
        "" if report["invocation"]["mode"] == "changed" else " --files <path>"))
    return "\n".join(out)


# --------------------------------------------------------------------------- main

def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default=None,
                        help="git ref to diff against (default: branch upstream, else origin/master)")
    parser.add_argument("--all", action="store_true", help="check every .py in the tier")
    parser.add_argument("--check-pins", action="store_true",
                        help="check every third-party import has a requirement.txt pin, then "
                             "exit -- skips the syntax/AI checks entirely. Needs Python 3.10+ "
                             "(run it as its own job on a newer interpreter than the tier's "
                             "pinned 3.9.15; that pin is for compiling correctly, not this)")
    parser.add_argument("--files", nargs="+", metavar="PATH", help="check these paths only")
    parser.add_argument("--no-ai", action="store_true", help="skip the AI diagnosis entirely")
    parser.add_argument("--ai-max-files", type=int, default=10,
                        help="most files to send to the AI in one run (default 10)")
    parser.add_argument("--rollback", action="store_true",
                        help="restore the newest compiling version of each broken file "
                             "(the broken copy is saved under .validator_backups/ first)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--report", metavar="PATH", default=None,
                        help="also write the JSON report here (default validation-report.json)")
    parser.add_argument("--no-report", action="store_true", help="do not write a report file")
    parser.add_argument("--require-pinned-interpreter", action="store_true",
                        help="fail (exit 2) if the interpreter used does not match "
                             ".python-version -- for CI, where a silent fallback to the "
                             "runner's default python would defeat the point of the gate")
    args = parser.parse_args(argv)

    root = repo_root()

    if args.check_pins:
        try:
            result = check_dependency_pins()
        except RuntimeError as exc:
            print("validator error: %s" % exc, file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(result, indent=2))
        elif not result["missing"]:
            print("OK - %d pinned distributions cover every third-party import"
                  % result["pinned_count"])
        else:
            for dist, files in result["missing"].items():
                print("%s: '%s' is imported but not pinned in requirement.txt"
                      % (files[0], dist))
            print("\n%d distribution(s) missing from requirement.txt -- add the exact version "
                  "installed on the box, don't guess (see CICD_DESIGN.md sec 3c)."
                  % len(result["missing"]))
        return 1 if result["missing"] else 0

    target_py, version, exact, note = find_target_python()

    if args.require_pinned_interpreter and not exact:
        print("validator error: interpreter %s (%s) does not match .python-version.\n  %s"
              % (target_py, version, note or "no matching interpreter found"), file=sys.stderr)
        return 2

    if args.files:
        targets, mode = [os.path.abspath(p) for p in args.files], "files"
    elif args.all:
        targets, mode = all_pipeline_files(), "all"
    else:
        base = args.base or default_base_ref()
        targets, mode = changed_files(base, root), "changed"

    missing = [p for p in targets if not os.path.isfile(p)]
    targets = [p for p in targets if os.path.isfile(p)]

    try:
        errors = compile_check(targets, target_py) if targets else {}
    except (RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print("validator error: %s" % exc, file=sys.stderr)
        return 2

    findings, sources = [], {}
    for abs_path in targets:
        err = errors.get(abs_path)
        if not err:
            continue
        try:
            with open(abs_path, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError:
            src = ""
        lines = src.splitlines()
        sources[abs_path] = {"src": src, "lines": lines}
        cause, suggestion, evidence = deterministic_diagnosis(err, src, lines, version)
        lineno = err.get("line")
        source_line = err.get("text") or (lines[lineno - 1] if lineno and lineno <= len(lines) else None)
        rel = os.path.relpath(abs_path, root)
        findings.append({
            "file": rel,
            "abs_path": abs_path,
            "line": lineno,
            "column": err.get("col"),
            "error_type": err.get("type"),
            "error": err.get("msg"),
            "source_line": source_line,
            "caret": caret_line(source_line, err.get("col")),
            "all_lines": lines,
            "deterministic": {"cause": cause, "suggestion": suggestion, "evidence": evidence},
            "ai": None,
            "ai_status": "not requested" if args.no_ai else None,
            "rollback": rollback_plan(abs_path, rel, target_py),
        })

    if args.no_ai or not findings:
        ai_state = {"backend": "none", "model": None, "status": "skipped",
                    "reason": "--no-ai" if args.no_ai else "no syntax errors to diagnose",
                    "files_diagnosed": 0, "files_skipped": 0}
    else:
        ai_state = run_ai(findings, sources, version, args.ai_max_files)

    code, head, _ = git("rev-parse", "HEAD")
    _, branch, _ = git("rev-parse", "--abbrev-ref", "HEAD")
    report = {
        "tool": "dcs-validate",
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "invocation": {"mode": mode, "base": args.base or (default_base_ref() if mode == "changed" else None),
                       "rollback_applied": False},
        "repo": {"branch": branch, "head": head if code == 0 else None, "missing_paths": missing},
        "interpreter": {"executable": target_py, "version": version,
                        "matches_pinned": exact, "note": note},
        "ai": ai_state,
        "summary": {"files_checked": len(targets), "files_with_errors": len(findings),
                    "clean": not findings},
        "findings": findings,
    }

    if args.rollback and findings:
        backup_dir = os.path.join(REPO_DIR, ".validator_backups",
                                  datetime.now().strftime("%Y%m%d-%H%M%S"))
        results = []
        for finding in findings:
            ok, detail = apply_rollback(finding, root, backup_dir)
            results.append({"file": finding["file"], "restored": ok, "detail": detail})
            finding["rollback_applied"] = {"restored": ok, "detail": detail}
        report["invocation"]["rollback_applied"] = True
        report["rollback_results"] = results

    # Render first: the human report quotes the original line from all_lines, which is then
    # dropped so the JSON report does not carry a copy of every broken file.
    rendered = None if args.json else render(report, use_color=sys.stdout.isatty())
    for finding in report["findings"]:
        finding.pop("all_lines", None)
    print(json.dumps(report, indent=2, default=str) if rendered is None else rendered)

    if not args.no_report:
        path = args.report or os.path.join(REPO_DIR, "validation-report.json")
        try:
            with open(path, "w") as fh:
                json.dump(report, fh, indent=2, default=str)
        except OSError as exc:
            print("warning: could not write %s: %s" % (path, exc), file=sys.stderr)

    if args.rollback and findings:
        return 0 if all(r["restored"] for r in report["rollback_results"]) else 1
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
