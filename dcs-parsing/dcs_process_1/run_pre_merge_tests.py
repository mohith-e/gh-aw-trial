#!/usr/bin/env python3
"""
Pre-merge test gate for dcs_process_1.

Finds which pipeline files changed relative to a base ref, discovers any test_*.py file
that imports each changed module by name, runs those tests, and exits non-zero if any of
them fail -- meant to be called from a git pre-push hook (see install_git_hooks.sh) or a
CI/PR check, so a broken pipeline can't reach a merge unnoticed (PME-... "Incorrect Pipeline
Status" showed DMG itself can silently report success on a failing pipeline -- this gate is
a second, independent check that doesn't rely on that reporting).

Coverage is intentionally advisory, not a hard requirement: a changed pipeline with no
matching test file prints a WARNING (not a failure) and does not block the push, since not
every one of the ~150 pipeline scripts has a regression fixture yet. Existing tests that
fail DO block. As more test_*.py files are added (see test_pipeline_fixes.py /
dcs_test_helpers.py for the pattern), coverage -- and the strength of this gate -- grows
without any change to this script.

Usage:
    python3 run_pre_merge_tests.py                  # compare against origin/master
    python3 run_pre_merge_tests.py --base HEAD~1     # compare against a specific ref
    python3 run_pre_merge_tests.py --all             # run every test_*.py, ignore git diff
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import unittest

REPO_DIR = os.path.dirname(os.path.abspath(__file__))


def reexec_under_tier_interpreter():
    """Re-run this script under the interpreter the pipeline actually uses.

    The pipeline's dependencies (xlwings 0.30.8, pandas 1.5.0) live in the tier's own env, not
    in whatever `python3` the git hook happened to resolve. Run the suite under the wrong
    interpreter and every test that imports DCS_etl_functions dies on `ModuleNotFoundError: No
    module named 'xlwings'` -- 20 of 22 here -- which is a false failure, and false failures are
    exactly what teach people to reach for `git push --no-verify`.

    Interpreter discovery is shared with validate.py rather than duplicated, so the two gates
    can never disagree about which Python the tier runs.
    """
    if os.environ.get("DCS_TESTS_REEXECED"):
        return
    try:
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)
        from validate import find_target_python
        exe, _version, _exact, _note = find_target_python()
    except Exception:
        return                                  # no validate.py: carry on as before
    if os.path.realpath(exe) == os.path.realpath(sys.executable):
        return
    os.environ["DCS_TESTS_REEXECED"] = "1"
    try:
        os.execv(exe, [exe, os.path.abspath(__file__)] + sys.argv[1:])
    except OSError:
        pass                                    # exec failed: run here rather than not at all

# Directories whose .py files are pipeline scripts worth gating on. DCS_etl_functions.py and
# auto_dcs_process_integrations.py are included too since they're shared by every pipeline
# (a change there has the widest blast radius of anything in this repo).
PIPELINE_DIRS = [
    'rent_roll_processes', 'tenancy_schedules_processes', 'trial_balance_processes',
    'budget_processes', 'box_score_processes', 'aged_receivables_processes',
]
SHARED_FILES = ['DCS_etl_functions.py', 'auto_dcs_process_integrations.py']


def _run(cmd):
    result = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def changed_python_files(base_ref):
    """Files changed relative to base_ref, plus anything currently staged/unstaged/untracked,
    since a developer running this before a push wants to see the effect of their
    working-tree changes too, not just what's already committed -- and `git diff` alone
    misses brand-new files (a new pipeline script or a new test) that haven't been added yet."""
    files = set()
    for cmd in [
        ['git', 'diff', '--name-only', f'{base_ref}...HEAD'],
        ['git', 'diff', '--name-only', 'HEAD'],
        ['git', 'diff', '--name-only', '--cached'],
        ['git', 'ls-files', '--others', '--exclude-standard'],
    ]:
        code, out, err = _run(cmd)
        if code == 0:
            files.update(f for f in out.splitlines() if f.endswith('.py'))
    return sorted(files)


def module_name_for(path):
    return os.path.splitext(os.path.basename(path))[0]


def is_gated_pipeline_file(path):
    basename = os.path.basename(path)
    if basename in SHARED_FILES:
        return True
    parts = path.split(os.sep)
    return len(parts) >= 2 and parts[-2] in PIPELINE_DIRS


def find_test_files_for_module(module_name):
    """Any test_*.py at the repo root that imports this module by name, matching either
    `import <module_name>` or `from <module_name> import ...`."""
    matches = []
    pattern = re.compile(r'^\s*(import\s+' + re.escape(module_name) + r'\b|from\s+' + re.escape(module_name) + r'\s+import)', re.MULTILINE)
    for test_file in glob.glob(os.path.join(REPO_DIR, 'test_*.py')):
        try:
            with open(test_file) as f:
                content = f.read()
        except OSError:
            continue
        if pattern.search(content):
            matches.append(test_file)
    return matches


def shared_file_test_files():
    """For DCS_etl_functions.py / auto_dcs_process_integrations.py, treat every test_*.py
    as potentially relevant -- a shared-file change can affect any pipeline's behavior via
    write_to_db/to_template_ftp, so run the full suite rather than trying to guess which
    subset is actually exercised by a given change."""
    return sorted(glob.glob(os.path.join(REPO_DIR, 'test_*.py')))


def default_base_ref():
    """The current branch's upstream tracking branch (e.g. origin/pipeline_issues) if one is
    set, since that's what "about to be pushed" actually means day-to-day; falls back to
    origin/master (the merge target) if there's no upstream, e.g. a brand-new local branch."""
    code, out, _ = _run(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'])
    if code == 0 and out:
        return out
    return 'origin/master'


def main():
    reexec_under_tier_interpreter()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base', default=None, help='Git ref to diff against (default: current branch\'s upstream, else origin/master)')
    parser.add_argument('--all', action='store_true', help='Run every test_*.py in the repo, ignoring git diff')
    args = parser.parse_args()
    base_ref = args.base or default_base_ref()

    if args.all:
        test_files = sorted(glob.glob(os.path.join(REPO_DIR, 'test_*.py')))
        uncovered = []
    else:
        print(f'Comparing against: {base_ref}\n')
        changed = [f for f in changed_python_files(base_ref) if is_gated_pipeline_file(f)]
        if not changed:
            print('No pipeline files changed -- nothing to test.')
            return 0

        print(f'Changed pipeline files ({len(changed)}):')
        for f in changed:
            print(f'  {f}')
        print()

        test_files = set()
        uncovered = []
        for f in changed:
            basename = os.path.basename(f)
            if basename in SHARED_FILES:
                matches = shared_file_test_files()
            else:
                matches = find_test_files_for_module(module_name_for(f))
            if matches:
                test_files.update(matches)
            else:
                uncovered.append(f)
        test_files = sorted(test_files)

    if uncovered:
        print('WARNING: no regression test found for these changed files (not blocking, but consider adding one):')
        for f in uncovered:
            print(f'  {f}')
        print()

    if not test_files:
        print('No applicable tests to run.')
        return 0

    print(f'Running {len(test_files)} test file(s):')
    for f in test_files:
        print(f'  {os.path.basename(f)}')
    print()

    sys.path.insert(0, REPO_DIR)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_file in test_files:
        module_name = module_name_for(test_file)
        suite.addTests(loader.loadTestsFromName(module_name))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        print('\nFAIL: one or more pipeline tests failed. Fix before merging.')
        return 1

    print('\nOK: all applicable pipeline tests passed.')
    if uncovered:
        print(f'({len(uncovered)} changed file(s) had no test coverage -- see warning above)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
