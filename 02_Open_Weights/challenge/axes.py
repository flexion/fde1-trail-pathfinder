# Variation axes for Trail Pathfinder's synthetic data (TC2).
#
# These describe real situations a skill-gap profile can be in, not text
# style. They are meant to be crossed (itertools.product) to generate
# profiles that exercise each combination.

from typing import Sequence

AXES: dict[str, Sequence[str]] = {
    # Does a matching, vetted training exist for a given skill gap?
    # "no_training_available" is the mandatory decline case: the system must
    # say no training exists rather than inventing one.
    "training_availability": [
        "approved_training_exists",
        "training_exists_not_yet_approved",
        "no_training_available",
        "multiple_trainings_match",
    ],
    # How many skill gaps does the profile have? Few-or-none never forces the
    # cap/ranking logic to run; 4+ forces it to actually pick and order.
    "gap_count": [
        "zero_gaps",
        "one_to_three_gaps",
        "four_or_more_gaps",
    ],
}
