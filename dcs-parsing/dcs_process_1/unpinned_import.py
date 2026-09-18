"""Compiles fine, but imports a package with no pin in requirement.txt.

Exists to prove dependency-pins reports the finding without turning the PR red.
"""
import dateparser


def parse(text):
    return dateparser.parse(text)
