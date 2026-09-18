"""Valid Python 3.10+, a SyntaxError on the tier's pinned 3.9.15.

The single most important property of this gate: validating with a newer interpreter than the
server runs would pass this file and it would then die on import in production.
"""


def classify(kind):
    match kind:
        case "rent_roll":
            return 1
        case _:
            return 0
