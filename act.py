###############################################################################
# ACT
# Actions for "Lil' Grid Lab"'s entities...
###############################################################################

# Libraries
import numpy as np
from collections import namedtuple

# Modules
pass

###############################################################################
# CONSTANTS

# Names of actions:
NONE = "NONE"
MOVE = "MOVE"
EAT = "EAT"

# (x, y) deltas for all 8 possible adjacent tiles (excluding (0,0)).
XY_8_DELTAS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
XY_8_ICONS = ("↙", "←", "↖", "↓", "↑", "↘", "→", "↗")

# Action_def: definitions of possible actions.
# An action consists of:
# - a verb (e.g. MOVE, EAT).
# - some action-dependent arguments, expressed between brackets.

Action_def = namedtuple("Action_def", "radius energy_ratio")

ACTIONS_DEF = dict(
    # PASSIVE action.
    NONE=Action_def(
        0,  # radius: local.
        0.0  # energy_ratio: 0x -> No energy consumption.
    ),
    # MOVING to adjacent relative coordinates.
    MOVE=Action_def(
        1,  # radius: 1 tile.
        1.0  # energy_ratio: 1x -> Unmodified ratio for 1-tile moves.
    ),

    # EATING energy from adjacent relative coordinates.
    EAT=Action_def(
        1,  # radius: 1 tile.
        0.0  # energy_ratio: 0x -> No energy consumption.
    ),
)

VOID_ACTION = (
    NONE,
    np.array([])
)
