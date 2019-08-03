###############################################################################
# Classess of Thing in a "Lil' Grid Lab" 'World':
# Thing
#   ├- Tile
#   ├- Block
#   └- Agent
###############################################################################

# Libraries.
import numpy as np
from collections import namedtuple

# Modules.
import ai
import act
import ui

# Constants
RANDOM_POSITION = None  # Old value was tuple (None, None)
# Agents' recycling_settings: types of dynamics.
NON_RECHARGEABLE = 'NON_RECHARGEABLE'  # Regular loss; useless after 'death'.
RECHARGEABLE = 'RECHARGEABLE'  # Regular loss; can be recharged after 'death'.
EVERLASTING = 'EVERLASTING'  # NO loss regardless of energy taken.
RESPAWNABLE = 'RESPAWNABLE'  # Regular loss; resurrected after death at random location.


###############################################################################
# Classess of Thing in a "Lil' Grid Lab" 'World':
# Thing
#   ├- Tile
#   ├- Block
#   └- Agent
###############################################################################


class Thing:
    # Root class containing the common attributes for all classes.
    def __init__(self, thing_def):
        self.name = thing_def["name"]  # Name of the thing.
        self.aspect = thing_def["aspect"]  # Text character to display.
        self.color = thing_def["color"]  # Color for the character.
        self.intensity = thing_def["intensity"]  # Intensity to apply.
        self.position = thing_def["initial_position"]  # Its position in the world.


class Tile(Thing):
    pass  # Use root class'.


class Block(Thing):
    num_blocks = 0

    # It passively occupies one tile, never moving.
    def __init__(self, thing_def):
        # Initialize inherited attributes.
        super().__init__(thing_def)
        # Update class variable.
        Block.num_blocks += 1


class Agent(Thing):
    # Default class for Agents.
    num_agents = 0

    def __init__(self,
                 thing_settings,
                 energy_settings,
                 ai_settings,
                 agent_suffix=None):
        # Initialize inherited attributes, customizing 'name'.
        super().__init__(thing_settings)
        if agent_suffix is not None:
            self.name = "{}.{}".format(self.name, str(agent_suffix))

        # Attributes related to energy.
        self.energy = energy_settings["initial_energy"]
        self.max_energy = energy_settings["maximum_energy"]
        self.bite_power = energy_settings["bite_power"]
        self.step_cost = energy_settings["step_cost"]
        self.move_cost = energy_settings["move_cost"]
        self.recycling = energy_settings["recycling_type"]
        self.acceptable_energy_drop = 2*self.step_cost + self.move_cost  # Heuristic threshold for UI highlights.

        # Attributes related to AI:
        self.perception = ai_settings["perception"]
        self.action = ai_settings["action"]
        self.learning = ai_settings["learning"]

        # Keep original attributes for recycling.
        self.original_color = self.color
        self.original_intensity = self.intensity

        # Initialize internal variables.
        self.initialize_state()

        Agent.num_agents += 1

    def initialize_state(self):
        # Initialize agent-specific attributes.
        self.steps = 0
        self.current_state = None
        self.current_energy_delta = 0
        self.negative_touch_map = np.zeros([3, 3])
        self.positive_touch_map = np.zeros([3, 3])
        self.chosen_action = act.VOID_ACTION
        self.chosen_action_success = True
        self.action_icon = ""
        self.learn_result = None

    def reset_touch_maps(self):
        # Set all surrounding tiles to 0.
        self.negative_touch_map[:] = 0
        self.positive_touch_map[:] = 0

    def pre_step(self):
        # Reset agents' step variables before a step is run.
        self.current_energy_delta = 0

    def update_energy(self, energy_delta, delta_source_position=None):
        # Handle 'energy' updates, including 'recycling' cases.
        #   - Updates energy change in self.current_energy_delta.
        # Updates 'touch_maps' at 'energy_source_position':
        #   - energy change passed is allocated to the source position passed.
        #   - when no source position is passed, local position is assumed,
        #     i.e. (1, 1) which is the center of the map.
        # Updates 'aspect' if needed.

        if self.recycling == EVERLASTING:
            # ENERGY:
            # No change to agent's energy despite the energy_delta.
            self.current_energy_delta = 0
            energy_used = energy_delta
            # No need to update self.negative_touch_map
            # or self.positive_touch_map.
        else:
            # ENERGY:
            # Keep within 0 and agent's max_energy.
            prev_energy = self.energy
            self.energy = max(min(self.energy + energy_delta, self.max_energy), 0)
            energy_used = self.energy - prev_energy  # Actual impact on agent.
            self.current_energy_delta += energy_used
            # Update 'touch_maps'.
            if delta_source_position is None:
                delta_source_position = self.position
            if energy_used < 0:
                touch_map = self.negative_touch_map
            else:
                touch_map = self.positive_touch_map
            touch_map[
                1 + delta_source_position[0] - self.position[0],
                1 + delta_source_position[1] - self.position[1]
            ] += energy_used

            # ASPECT:
            # Check for death condition:
            if self.energy <= 0:
                # Update aspect (RESPAWNEABLE condition handled by world).
                self.color, self.intensity = ui.DEAD_AGENT_COLOR_INTENSITY

        return energy_used

    def choose_action(self, world):
        # First, update agent's interpretation of the world (its current_state).
        self.current_state = self.perception(agent=self, world=world)
        # Now its "acting mind" is requested to choose an action.
        self.chosen_action = self.action(self.current_state)

        return self.chosen_action

    def update_after_action(self):
        # Update internal state of agent after trying some action.

        # Update internal variables, aspect, etc.
        self.reset_touch_maps()

        # UI: Capture action's icon, if any.
        action = self.chosen_action[1].tolist()
        if action in act.XY_8_DELTAS:
            action_idx = act.XY_8_DELTAS.index(action)
            self.action_icon = act.XY_8_ICONS[action_idx]
        else:
            self.action_icon = ""

        # TODO: Update aspect (character(s) displayed, color...)?

    def post_step(self):
        # Actions on agent after a step is run.

        # Update policy (learning).
        if self.learning is not None:
            self.learn_result = self.learning(
                self.current_state,
                self.chosen_action,
                self.current_energy_delta)

        # Now the 'step' is finished.
        self.steps += 1

    def respawn(self):
        # Restablish a fresh copy of the agent back to its optimal state.
        # All previous state data is wiped out.

        # Energy:
        prev_energy = self.energy
        self.energy = self.max_energy
        energy_used = self.energy - prev_energy  # Actual impact on agent.

        # Look:
        self.color = self.original_color
        self.intensity = self.original_intensity

        # Initialize internal variables.
        self.initialize_state()

        return energy_used
