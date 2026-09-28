"""The precision of the embedding model: the closed set of wire names.

The admin chooses the precision in the companion, which stores it next to the
profile and answers both over the same profile route (D-25-02). Two names form a
closed set, int8 and fp32, and the same two strings name the weight files in
findling.store.vectors; a test keeps both spellings equal, and another one keeps
this set equal to SettingsService::PRECISIONS on the PHP side.

int8 is the default. A companion that never answered, or one older than the
field, leaves the container on the weights it ships with today.

Plan 25-08 adds the process state (what was chosen, what runs) to this module.

The module is neutral: stdlib only, so that both the worker and the api may
import it. It logs nothing, neither precision names nor environment values.
"""

import enum
from typing import Final


class Precision(enum.StrEnum):
    """The wire names. Display texts come from the catalogues (phase 27)."""

    INT8 = "int8"
    FP32 = "fp32"


PRECISION_NAMES: Final = frozenset(p.value for p in Precision)
PRECISION_DEFAULT: Final = Precision.INT8
