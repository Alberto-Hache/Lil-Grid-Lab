###############################################################################
# AI
# Artificial Intelligence for "Lil' ASCII Lab"'s Agents...
###############################################################################

# Libraries.
import numpy as np
from numpy import unravel_index
import random

# Modules
import act

###############################################################################
# CONSTANTS

OFF_BOARD = -1000000  # Value signalling an "illegal" out-of-the-board tile.

# Precalculated maps:
DISTANCE_MAP_2_TILES = np.array([
    [2, 2, 2, 2, 2],
    [2, 1, 1, 1, 2],
    [2, 1, 0, 1, 2],
    [2, 1, 1, 1, 2],
    [2, 2, 2, 2, 2]
])
DISTANCE_MAP_2_TILES_CENTER = [2, 2]

NO_PERCEPTION = None
NO_ACTION = None
NO_LEARNING = None


###############################################################################
# Minds: Auxiliary functions
#
# Used by Perception and Action functions.
###############################################################################

def obtain_bite(energy_map, position, radius=1, highest=False):
    # Return a delta from the given position leading to a position with
    # some energy within the radius given, or 'None' if none is found.
    # If 'highest' is True, the delta leading to the highest energy around is
    # returned.

    # Obtain submap around position ant tuple with its origin.
    energy_submap, submap_origin = copy_submap(
        energy_map,
        position,
        radius)

    # Check whether there's some available bite first.
    max_energy_around = np.nanmax(energy_submap)

    if max_energy_around > 0:
        # Go for that bite.
        if highest:
            # Obtain relative position of HIGHEST values in submap.
            bites_list = np.argwhere(energy_submap == max_energy_around)
        else:
            # Obtain relative position of any POSITIVE values in sumbap.
            bites_list = np.argwhere(energy_submap > 0)

        # Get any bite in the list.   
        bite_position = bites_list[random.randint(0, len(bites_list) - 1)]
        # Generate tuple leading to the bite chosen.
        best_bite_delta = np.array([
            submap_origin[0] + bite_position[0] - position[0],
            submap_origin[1] + bite_position[1] - position[1]
            ])
    else:
        # Handle void result.
        best_bite_delta = None

    return best_bite_delta


def obtain_move(occupation_bitmap, position, radius=1):
    # Return a delta from the given position leading to an unoccupied
    # position within the radius given, or 'None' if none is found.

    # Obtain submap around position ant tuple with its origin.
    occupation_submap, submap_origin = copy_submap(
        occupation_bitmap,
        position,
        radius)

    # Obtain relative position of all UNOCCUPIED positions in submap.
    moves_list = np.argwhere(occupation_submap == 1)

    if len(moves_list > 0):
        # Some move(s) found: pick a random one.
        move_position = moves_list[random.randint(0, len(moves_list) - 1)]

        # Generate tuple leading to the move chosen.
        move = np.array([
            submap_origin[0] + move_position[0] - position[0],
            submap_origin[1] + move_position[1] - position[1]
            ])
    else:
        # Handle void result.
        move = None

    return move


def obtain_best_escape(occupation_bitmap, position,
                       negative_touch_map, max_loss_position, radius=1):
    # Return a delta with the move best escaping from a 'bite', i.e.
    # an energy loss represented as negative in touch_map.
    # If no 'bites' are found, None is returned.

    touch_map_center = [1, 1]  # Coords. of agent in touch_map.
    best_escape = None

    # Obtain submap of occupation around position.
    occupation_submap, submap_center = overlap_maps(
        occupation_bitmap,
        position,
        negative_touch_map,
        touch_map_center)

    # Obtain submap of distances around _corrected_ max_loss_position.
    shift_x = submap_center[0] - touch_map_center[0]
    shift_y = submap_center[1] - touch_map_center[1]
    corrected_max_loss_position = [
        max_loss_position[0] + shift_x,
        max_loss_position[1] + shift_y
    ]

    distances_submap, distances_submap_center = overlap_maps(
        DISTANCE_MAP_2_TILES,
        DISTANCE_MAP_2_TILES_CENTER,
        occupation_submap,
        corrected_max_loss_position
    )

    # Cancel unreachable positions (occupied or off-board).
    legal_distances_submap = np.multiply(
        distances_submap, occupation_submap  # Occupied tiles are 0.
    )

    # Obtain position with largest distance.
    max_distance_position = unravel_index(
        legal_distances_submap.argmax(),
        legal_distances_submap.shape
    )

    # Obtain xy_delta for 'move'.
    best_escape = np.array([
        max_distance_position[0] - submap_center[0],
        max_distance_position[1] - submap_center[1]
    ])

    return best_escape


def copy_submap(map, position, radius=1):
    # Return:
    # submap: a subset copied from the given map centered around 'position'
    # with the given radius.
    # submap_origin: the coordinates of bottom_left position of submap.
    # Note: Central 'position' is signalled OFF_BOARD.

    x0, y0 = position
    width, height = map.shape

    # Obtain 'legal' subrectangle [submap_x0, submap_x1] x
    # [submap_y0, submap_y1].
    submap_x0 = max(0, x0 - radius)
    submap_x1 = min(x0 + radius, width - 1)
    submap_y0 = max(0, y0 - radius)
    submap_y1 = min(y0 + radius, height - 1)
    # Get 'submap_origin'.
    submap_origin = [submap_x0, submap_y0]

    # Copy subrectangle on submap.
    submap = np.copy(
        map[submap_x0:submap_x1+1, submap_y0:submap_y1+1]
    )

    # Mark central position as OFF_BOARD.
    x0_submap = x0 - submap_x0
    y0_submap = y0 - submap_y0
    submap[x0_submap, y0_submap] = OFF_BOARD

    return submap, submap_origin


def overlap_maps(big_map, big_map_center, small_map, small_map_center):
    # Obtain a copy of the area within big_map overlapped by small_map,
    # matching their respective centers.
    # Return the copy and its center.

    big_map_width, big_map_height = big_map.shape
    small_map_width, small_map_height = small_map.shape

    # Obtain subrectangle [submap_x0, submap_x1] x
    # [submap_y0, submap_y1].
    submap_x0 = max(
        0,
        big_map_center[0] - small_map_center[0])
    submap_x1 = min(
        big_map_width - 1,
        big_map_center[0] + (small_map_width - 1 - small_map_center[0]))
    submap_y0 = max(
        0,
        big_map_center[1] - small_map_center[1])
    submap_y1 = min(
        big_map_height - 1,
        big_map_center[1] + (small_map_height - 1 - small_map_center[1]))

    # Copy subrectangle on submap.
    submap = np.copy(
        big_map[submap_x0:submap_x1+1, submap_y0:submap_y1+1]
    )
    # Calculate submap's center.
    submap_center = [
        big_map_center[0] - submap_x0,
        big_map_center[1] - submap_y0
    ]

    return submap, submap_center

###############################################################################
# Minds: Perception
#
# A 'perception' function extracts from the world and the agent itself
# all the information an agent will need to make decisions based on its
# 'action' function.
#
# - Input:
#       - agent, the agent itself, for introspection of its state.
#       - world, the environment in which the agent is.
#
# - Output:
#       - state,  information in the shape the agent will be able to process.
#         NOTE: This implies that "perception"'s output state must match
#         "action"'s input state.
###############################################################################


def no_info(agent, world=None):
    # Void perception function, the agent receives no information about world
    # or itself. This is useful for passive agents not actually doing anything,
    # e.g. some object or energy source.

    return None


def full_info(agent, world=None):
    # Full perception and access to agent and world is granted.
    # This is useful to program 'hard-coded' AIs which directly access
    # all currently available information.
    #
    # Limitation: Learning can't be based on the returned state because
    # it's not a static copy of data.

    state = (agent, world)  # A tuple with both references.

    return state


###############################################################################
# Minds: Action
#
# An 'action' function ('policy' in RL) selects an action at each step
# for the agent.
#
# - Input:
#       - state, the current state of world and agent.
#         TODO: Eliminate need for 'world' arg.
#
# - Output: the action chosen, as a list:
#       - action_type, e.g. act.MOVE, act.FEED, act.NONE.
#       - action_arguments, e.g. [-1, 1], [].
#
###############################################################################

def passive(state=None):
    # Void action function, the agent does not interact with the world.
    # This is useful for passive agents not actually doing anything,
    # e.g. some object or piece of food.

    return act.VOID_ACTION


def wanderer(state):
    # A hard-coded AI modelling these basic behaviourial priorities:
    # 1. Some inertia for continued movements or eating.
    # 2. Start moves on clear directions (though inertia can cause collisions).
    # 3. Eat from adjacent objects at times.
    # 4. Otherwise, do nothing.

    agent, world = state  # Extract both complete objects from tuple.

    inertia_prob = 0.66  # Probability of repeating latest action.
    stopping_prob = 0.1  # Probability of stopping vs. doing something.
    biting_prob = 0.5  # Probability of biting an adjacent agent vs. moving.

    if random.uniform(0, 1) <= inertia_prob and agent.chosen_action_success:
        # REPEAT latest action.
        action = agent.chosen_action
    else:
        if random.uniform(0, 1) <= stopping_prob:
            # NONE: Stop for a while.
            action = act.VOID_ACTION
        else:
            # EAT: Check for close agents.
            xy_delta = obtain_bite(
                world.energy_map,
                agent.position,
                act.ACTIONS_DEF[act.EAT].radius
                )
            if random.uniform(0, 1) <= biting_prob and xy_delta is not None:
                # Some bite is possible.
                action = [act.EAT, xy_delta]
            else:
                # MOVE: Choose a random legal move.
                xy_delta = obtain_move(
                    world.occupation_bitmap,
                    agent.position,
                    act.ACTIONS_DEF[act.MOVE].radius
                    )
                if xy_delta is not None:
                    action = [act.MOVE, xy_delta]
                else:
                    action = act.VOID_ACTION

    return action


def wanderer2(state):
    # A hard-coded AI modelling these basic behaviourial priorities:
    # 1. If loss just suffered is too high, escape from offending tile.
    # 2. If hungry, try  best bite (highest energy) around.
    # 3. Otherwise, act as a regular 'wanderer'.

    agent, world = state  # Extract both complete objects.

    max_loss_threshold = agent.step_cost  # Arbitrary, relative to agent.
    hunger_threshold = 0.5  # Energy ratio below which eating is prioritary.

    # 0. Default action is to rest.
    action = act.VOID_ACTION

    # 1. Check for pain first.
    if action == act.VOID_ACTION:
        max_loss_position = unravel_index(
            agent.negative_touch_map.argmin(),
            agent.negative_touch_map.shape)
        loss_just_suffered = agent.negative_touch_map[max_loss_position]
        if loss_just_suffered <= max_loss_threshold:  # (Negative amounts.)
            # High loss detected: try to escape.
            best_move_delta = obtain_best_escape(
                world.occupation_bitmap,
                agent.position,
                agent.negative_touch_map,
                max_loss_position)
            if best_move_delta is not None:
                action = [act.MOVE, best_move_delta]

    # 2. Check for hunger.
    if action == act.VOID_ACTION:
        if agent.energy / agent.max_energy < hunger_threshold:
            # Hunger: try best bite.
            best_move_delta = obtain_bite(
                world.energy_map,
                agent.position,
                act.ACTIONS_DEF[act.EAT].radius,
                highest=True)
            if best_move_delta is not None:
                action = [act.EAT, best_move_delta]

    # 3. Act as a regular 'wanderer'.
    if action == act.VOID_ACTION:
        action = wanderer(state)

    return action


def killer(state):
    # A hard-coded AI modelling these basic behaviourial priorities:
    # 1. If loss just suffered is too high, escape from offending tile.
    # 2. If mid-loss suffered, or a bit hungry, bite any agent around.
    # 3. Otherwise, act as a regular 'wanderer'.

    agent, world = state  # Extract both complete objects.

    max_loss_threshold = -agent.bite_power  # Arbitrary, relative to agent.
    normal_loss_threshold = agent.step_cost  # Arbitrary, relative to agent.
    hunger_threshold = 0.9  # Energy ratio below which eating is prioritary.

    # 0. Default action is to rest.
    action = act.VOID_ACTION

    # 1. Check for energy balance first.
    if action == act.VOID_ACTION:
        max_loss_position = unravel_index(
            agent.negative_touch_map.argmin(),
            agent.negative_touch_map.shape)
        loss_just_suffered = agent.negative_touch_map[max_loss_position]
        if loss_just_suffered <= max_loss_threshold:  # (Negative amounts.)
            # High loss detected: try to escape.
            best_move_delta = obtain_best_escape(
                world.occupation_bitmap,
                agent.position,
                agent.negative_touch_map,
                max_loss_position)
            if best_move_delta is not None:
                action = [act.MOVE, best_move_delta]

    # 2. Check for energy around.
    if action == act.VOID_ACTION:
        if agent.energy / agent.max_energy < hunger_threshold or \
           loss_just_suffered <= normal_loss_threshold:
            # Hunger or low-loss attack: try best bite.
            best_move_delta = obtain_bite(
                world.energy_map,
                agent.position,
                act.ACTIONS_DEF[act.EAT].radius,
                highest=True)
            if best_move_delta is not None:
                action = [act.EAT, best_move_delta]

    # 3. Act as a regular 'wanderer'.
    if action == act.VOID_ACTION:
        action = wanderer(state)

    return action

###############################################################################
# Minds: Learning
#
# A 'learning' function updates the policy of the agent
# after trying some action based on:
#
# - Input:
#       - (S_t): state interpretation, stored in self.current_state
#       - (A_t): action taken, stored in self.chosen_action
#       - (r_t): immediate reward, stored in self.current_energy_delta
#
# - Output:
#       - result: some quantification of the learning performed,
#         (bound to the learning algorithm).
###############################################################################


def no_learning(state, action, reward):
    # Void learning function; the agent doesn't perform any modification
    # of its policy.
    # This is useful for 'hard-coded' non-Machine-Learning AIs.

    return None
