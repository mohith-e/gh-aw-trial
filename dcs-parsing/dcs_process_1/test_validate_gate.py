#!/usr/bin/env python3
"""Regression tests for validate.py's own environment handling.

These exist because the gate's two callers do not run it the same way. CI invokes validate.py
from a clean environment; the pre-push hook invokes it from inside git, which exports GIT_DIR.
A bug that only appears under GIT_DIR is therefore invisible to CI by construction -- it shipped
once already, silently turning every push into a full-tier sweep that blocked on files the
developer had not touched. Stdlib only, so this can run in the dependency-free syntax job.
"""
import json
import os
import subprocess
import sys
import unittest

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATE = os.path.join(REPO_DIR, "validate.py")


def run_validator(extra_env=None):
    env = dict(os.environ)
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    env.pop("GIT_INDEX_FILE", None)
    env.update(extra_env or {})
    proc = subprocess.run(
        [sys.executable, VALIDATE, "--no-ai", "--no-report", "--json"],
        cwd=REPO_DIR, capture_output=True, text=True, env=env,
    )
    # Exit 2 is the validator itself failing; 0 and 1 both produce a usable report.
    if proc.returncode == 2:
        raise AssertionError("validator errored: %s" % proc.stderr.strip())
    return json.loads(proc.stdout)


class GitEnvIsolationTests(unittest.TestCase):
    """git exports GIT_DIR to hooks. With it set and no GIT_WORK_TREE, git treats the CWD as the
    work tree, so the repo root resolves to dcs_process_1/ instead of the repository root: every
    tracked file looks untracked and the changed-file diff collapses into a whole-tier sweep."""

    def setUp(self):
        probe = subprocess.run(["git", "rev-parse", "--absolute-git-dir"],
                               cwd=REPO_DIR, capture_output=True, text=True)
        if probe.returncode != 0:
            self.skipTest("not inside a git work tree")
        self.git_dir = probe.stdout.strip()

    def test_hook_environment_selects_the_same_files_as_a_clean_environment(self):
        clean = run_validator()
        hooked = run_validator({"GIT_DIR": self.git_dir})
        # Not asserting a particular mode: on a PR, CI checks out a detached merge ref, so
        # which base the validator resolves is environment-dependent and not the point. The
        # invariant is that both environments agree -- under the bug they did not.
        self.assertEqual(hooked["invocation"]["mode"], clean["invocation"]["mode"])
        self.assertEqual(
            hooked["summary"]["files_checked"], clean["summary"]["files_checked"],
            "GIT_DIR changed which files the gate checks: %d under the hook vs %d in CI. The "
            "hook would block pushes over files the developer never touched."
            % (hooked["summary"]["files_checked"], clean["summary"]["files_checked"]),
        )

    def test_hook_environment_resolves_the_same_head(self):
        self.assertEqual(run_validator({"GIT_DIR": self.git_dir})["repo"]["head"],
                         run_validator()["repo"]["head"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
