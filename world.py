###############################################################
# The world
# for "Lil' Grid Lab" and its entities...

###############################################################

# Libraries.
import numpy as np
import random
import time

# Modules.
import things
import act
import ui


# World definition:
# This is what the world simulated will look like:
WORLD_DEF = dict(
    # Aspect:
    name="Random Blox",  # Descriptive string.
    width=15,  # Defining coordinate x from 0 to width - 1
    height=10,  # Defining coordinate y from 0 to height - 1
    bg_color=ui.BLACK,  # background color (see ui.py module).
    bg_intensity=ui.NORMAL,  # background intensity (see ui.py module).
    n_blocks_rnd=0.4,  # % of +/- randomness in number of blocks [0, 1]
    # Simulation:
    max_steps=None,  # How long to run the world ('None' for infinite loop).
    pause_step=None,  # World will be paused at that step if not 'None'.
    fps=5,  # Frames-Per-Second, i.e. number of time steps run per second ('None' for full-speed).
    initial_pause=True,  # Initiates world in 'pause' mode.
    random_seed=None,  # Seed for reproducible runs (None for random).
)

# Simulation definition:
# These are the settings provided to the simulation:
Simulation_def = dict(
    world=WORLD_DEF,  # Some specific world definition.
    tile=things.TILE_DEF,  # The tiles it will contain.
    blocks=things.BLOCKS_DEF,  # The blocks to put in it.
    agents=things.AGENTS_DEF,  # The agents who will live in it.
)

# Constants:
WORLD_DEFAULT_FPS = 5  # Fall-back world speed (in frames-per-second).
WORLD_DEFAULT_SPF = 1 / WORLD_DEFAULT_FPS  # (the same in seconds-per-frame).

###############################################################


class World:
    # A tiled, rectangular setting on which a little universe takes life.
    def __init__(self, Simulation_def):
        # Create a world from the definitions given.
        world_def = Simulation_def["world"]
        tile_def = Simulation_def["tile"]
        blocks_def = Simulation_def["blocks"]
        agents_def = Simulation_def["agents"]

        # Assign values from w_def.
        self.name = world_def["name"]
        self.width = world_def["width"]
        self.height = world_def["height"]
        self.bg_color = world_def["bg_color"]
        self.bg_intensity = world_def["bg_intensity"]
        self.n_blocks_rnd = world_def["n_blocks_rnd"]
        self.max_steps = world_def["max_steps"]
        self.pause_step = world_def["pause_step"]

        # Time and speed settings.
        self.initialize_fps(world_def["fps"])
        self.paused = world_def["initial_pause"]  # Whether the user has paused simulation.
        self.step_by_step = world_def["initial_pause"]  # Whether the user has activated step-by-step.
        self.user_break = False  # Whether user has interrupted simulation.
        self.creation_time = time.time

        # Initialize world: randomness, steps and list of 'things' on it.
        seed = world_def["random_seed"]
        assert seed is not None, \
            "World initialization received a random_seed of value 'None'"
        self.random_seed = seed
        random.seed(seed)

        self.steps = 0
        # A grid for agents and blocks [references].
        self.things = np.full((self.width, self.height), None)
        # A grid tracking energy [floats] on each tile.
        self.energy_map = np.zeros((self.width, self.height))
        # A grid tracking occupation [1 / 0] of each tile.
        self.occupation_bitmap = np.full(
            (self.width, self.height), 1)  # Unoccupied tile.
        # A grid tracking aspect (a character) of Things on each tile (or "").
        self.occupation_map = np.full(
            (self.width, self.height), "")

        # Put TILES on the ground.
        self.ground = np.full((self.width, self.height), None)  # Fill in the basis of the world.
        for x in range(self.width):
            for y in range(self.height):
                # Create tile.
                tile = things.Tile(tile_def)
                self.ground[x, y] = tile
                self.occupation_map[x, y] = tile.aspect

        # Put AGENTS in the world.
        self.agents = []  # List of all types of agent in the world.
        self.tracked_agent = None  # The agent to track during simulation.
        for a_def in agents_def:  # Loop over the types of agent defined.
            for i in range(a_def.n_instances):  # Create the number of instances specified.
                # Create agent as defined, defining now its suffix.
                if a_def.n_instances == 1:  # Check if it's a single instance.
                    agent_suffix = None
                else:
                    agent_suffix = i
                agent = things.Agent(
                    a_def.thing_settings,
                    a_def.energy_settings,
                    a_def.ai_settings,
                    agent_suffix
                    )
                # Put agent in the world on requested position, relocating on colisions (on failure, Agent is ignored).
                success = self.place_at(agent, agent.position, relocate=True)
                if success:
                    # Update agents list and tracked_agent (only the first time).
                    self.agents.append(agent)
                    if self.tracked_agent is None:
                        self.tracked_agent = agent
                else:
                    # Ignore agent and report incidence.
                    # TODO: Track issue.
                    pass

        # Put in some BLOCKS.
        self.blocks = []
        for b_def in blocks_def:  # List of all types of block in the world.
            if (b_def.n_instances is None):
                # Unspecified number of blocks; base on width.
                n_random_blocks = (self.width * self.n_blocks_rnd) // 1  # abs. max variation.
                n_random_blocks = self.width + random.randint(-n_random_blocks, n_random_blocks)
            else:
                # Specified No. of blocks.
                n_random_blocks = b_def.n_instances

            n = 0
            while n < n_random_blocks:
                block = things.Block(b_def.thing_settings)
                success = self.place_at(block)  # Put in random position if possible (fail condition ignored).
                if success:
                    # Update blocks list.
                    self.blocks.append(block)
                else:
                    # Ignore block and report incidence.
                    # TODO: Track issue.
                    pass
                n += 1

        # Final settings.
        self.total_energy = self.energy_map.sum()  # Total from all agents.
        self.aux_msg = ""

    def initialize_fps(self, fps):
        # fps, spf is the current world speed (frames-per-second, seconds-per-frame).
        # original_fps, original_spf keeps the original setting.
        # previous_fps remembers latest fps speed before going 'full-speed',
        # or establishes WORLD_DEFAULT_FPS when starting af 'full-speed'.

        self.fps = fps
        if fps is None:
            self.spf = None
            self.previous_fps = WORLD_DEFAULT_FPS

        else:
            self.spf = 1 / fps
            self.previous_fps = fps

        self.original_fps = self.fps
        self.original_spf = self.spf

    def update_fps(self, fps_factor):
        if fps_factor is None:
            # 'None' means 'go full-speed'.
            if self.fps is None:
                # Already at full-speed; no action needed.
                pass
            else:
                # Update needed.
                self.previous_fps = self.fps
                self.fps = None
                self.spf = None
        else:
            # Check current fps.
            if self.fps is None:
                # Slow down from 'full-speed' to previous fps/spf.
                self.fps = self.previous_fps
            else:
                # Simply apply factor to fps.
                self.fps *= fps_factor
            # Update spf.
            self.spf = 1 / self.fps

    def seconds_run(self):
        # Return the number of seconds run in world's time based on spf(seconds per frame).
        # Assumptions:
        # - Since speed can vary at user's request, original_spf is assumed.
        # - And if original_fps was None, WORLD_DEFAULT_SPF us assumed.

        if self.original_spf is not None:
            referential_spf = self.original_spf
        else:
            referential_spf = WORLD_DEFAULT_SPF

        return (self.steps * referential_spf) // 1

    def place_at(self, thing, position=things.RANDOM_POSITION, relocate=False):
        # Put "things" in the world at certain position, updating the thing and
        # the world's internal status (self.things and self.energy_map).
        #
        # If position is not defined, find a random free place and move the Thing there.
        # If position is defined,
        #       if not occupied, move a Thing to position;
        #       if occupied, relocate randomly if allowed by 'relocate', or fail otherwise.
        # Result of action: (True: success; False: fail).
        if position == things.RANDOM_POSITION:
            # position not defined; try to find a random one.
            position, success = self.find_free_tile()
        else:
            # position is defined; check if it is empty (or the current one).
            if self.tile_is_empty(position) or position == thing.position:
                # position is empty (or already the current one): success!
                success = True
            elif relocate:
                # position is occupied, try to relocate as requested.
                position, success = self.find_free_tile()
            else:
                # position is occupied and no relocation requested; FAIL.
                success = False

        if success:
            # The move is possible, (re)locate Thing.
            if thing.position != things.RANDOM_POSITION:
                # The Thing was already in the world; clear out old place.
                self.things[thing.position[0], thing.position[1]] = None
                self.energy_map[thing.position[0], thing.position[1]] = 0
                self.occupation_bitmap[
                    thing.position[0], thing.position[1]
                    ] = 1  # Unoccupied tile.
                self.occupation_map[
                    thing.position[0], thing.position[1]
                    ] = \
                    self.ground[
                    thing.position[0], thing.position[1]  # Tile's aspect.
                    ]

            self.things[position[0], position[1]] = thing
            if type(thing) is things.Agent:
                self.energy_map[position[0], position[1]] = thing.energy
            self.occupation_bitmap[
                position[0], position[1]
                ] = 0  # Occupied tile.
            self.occupation_map[
                position[0], position[1]
                ] = thing.aspect
            thing.position = position

        elif thing.position != things.RANDOM_POSITION and position == things.RANDOM_POSITION:
            # The move is not possible, BUT the thing was already in the world,
            # and target position didn't matter:
            # Leave the thing where it was.
            success = True

        return success

    def tile_is_empty(self, position):
        # Check if a given position exists within world's limits and is free.
        x, y = position
        if (0 <= x <= self.width - 1) and (0 <= y <= self.height - 1):
            result = self.things[x, y] is None
        else:
            result = False
        return result

    def find_free_tile(self):
        # Try to find a tile that is empty in the world.
        # Result of action: (True: success; False: fail).

        # First, try a random tile.
        x = random.randint(0, self.width - 1)
        y = random.randint(0, self.height - 1)
        found = self.tile_is_empty([x, y])

        x0, y0 = x, y  # Starting position to search from.
        success = True
        while not found and success:
            x = (x + 1) % self.width  # Increment x not exceeding width.
            if x == 0:  # When x is back to 0, increment y not exceeding height.
                y = (y + 1) % self.height
            if self.tile_is_empty([x, y]):  # Check "success" condition.
                found = True
            elif (x, y) == (x0, y0):  # Failed if loop over the world is complete.
                success = False

        if success:
            position = [x, y]
        else:
            position = things.RANDOM_POSITION
        return position, success

    def step(self):
        # Prepare world's info for step.
        self.pre_step()

        # Run step over all "living and acting" agents.
        for agent in filter(lambda a:
                            a.energy > 0 and a.action is not None,
                            self.agents):
            # New check for a.energy (which can change within loop).
            assert agent.energy > 0, \
                "Agent {} with energy {} was active in step() loop.".format(
                    agent.name,
                    agent.energy
                )
            # Request action from agent based on world state.
            action = agent.choose_action(world=self)
            # Try to execute action.
            self.execute_action(agent, action)
            # Update agent's internal information.
            agent.update_after_action()

        # Update the world's info after step.
        self.post_step()

    def pre_step(self):
        # Prepare world's info before actually running core step() functionality.

        # Reset agents' step variables.
        for agent in self.agents:
            agent.pre_step()

        # TODO: Generate new energy in the world?
        pass

        # TODO: Remove long-dead non-RECHARGEABLE agents.
        pass

    def post_step(self):
        # Execute actions after a world's step (and before 'respawns').

        # Call all agents' post_step() here.
        for agent in self.agents:
            if agent.energy <= 0 and agent.recycling == things.RESPAWNABLE:
                # Respawn dead agent on new random place.
                _ = self.update_agent_energy(agent, energy_delta=None)
                result = self.place_at(agent)
                assert result, "Failed place_at({}) after respawn().".format(
                    agent.name)
            else:
                # Regular post_step()
                agent.post_step()

        # Update rest of world's internal info.
        self.total_energy = self.energy_map.sum()
        assert np.isclose(  # Sanity check of energy totals.
            self.total_energy,
            sum(a.energy for a in self.agents)
            ), "Total energy mismatch ({}) between world.energy_map and \
                world.agents.".format(
                self.total_energy - sum(a.energy for a in self.agents)
                )
        self.agents.sort(key=lambda x: x.energy, reverse=True)
        self.steps += 1
        if self.steps == self.pause_step:
            self.paused = True
            self.step_by_step = False

    def execute_action(self, agent, action):
        # Check if the action is feasible and execute it on world and agents.
        # Acting 'agent': it may update position, energy attributes,
        # and chosen_action_success.
        # [other agent involved: energy attributes].

        # Initialize internal variables.
        action_type, action_arguments = action
        action_energy_ratio = act.ACTIONS_DEF[action_type].energy_ratio

        # Calculate energy cost IF action is actually made.
        action_delta = agent.move_cost * action_energy_ratio  # <0
        # Manage abandoned_position, for cases when the agent moves.
        abandoned_position = None

        if agent.energy + action_delta + agent.step_cost < 0:
            # Not enough energy for the move and the step cost.
            success = False
            action_delta = 0
            energy_delta = action_delta + agent.step_cost
            self.update_agent_energy(agent, energy_delta)

        elif action_type == act.NONE:
            # Rest action.
            success = True
            energy_delta = action_delta + agent.step_cost
            self.update_agent_energy(agent, energy_delta)

        elif action_type == act.MOVE:
            # Update locations [try to], checking if destination tile is free.
            success = self.place_at(agent,
                                    [agent.position[0] + action_arguments[0],
                                     agent.position[1] + action_arguments[1]]
                                    )
            if not success:
                action_delta = 0
                # TODO: Penalize collisions?
            energy_delta = action_delta + agent.step_cost
            self.update_agent_energy(agent, energy_delta)

        elif action_type == act.EAT:
            # Firstly, update energy spent in step for whichever result,
            # (to allow full replenishment).
            _ = self.update_agent_energy(agent, agent.step_cost)  # Dropped energy is lost.

            prey = self.things[agent.position[0] + action_arguments[0],
                               agent.position[1] + action_arguments[1]]
            if prey in self.agents:
                # Viable action. Try to take energy from prey.
                max_possible_bite = min(
                    agent.bite_power,
                    agent.max_energy - agent.energy)
                energy_taken = self.update_agent_energy(
                    prey,
                    -max_possible_bite,
                    agent.position)
                action_delta += - energy_taken
                success = action_delta > 0
                # Give energy to eating agent.
                _ = self.update_agent_energy(
                    agent,
                    action_delta,
                    prey.position)
            else:
                # Failed action.
                success = False
                action_delta = 0

            energy_delta = action_delta + agent.step_cost

        else:
            raise Exception('Invalid action type passed: {}.'.format(action_type))

        # Update agent on success of action.
        agent.chosen_action_success = success

    def update_agent_energy(self, agent,
                            energy_delta=None,
                            energy_source_position=None):
        # Execute agent's method to update its 'energy' state by
        # 'energy_delta',
        # or agent's respawn method if 'energy_delta' is None.
        # Then update the world's internal status (self.energy_map).
        # Return actual energy change for the agent.

        if energy_delta is not None:
            energy_taken = agent.update_energy(
                energy_delta,
                energy_source_position)
        else:
            energy_taken = agent.respawn()
        self.energy_map[agent.position[0], agent.position[1]] = agent.energy

        return energy_taken

    def is_end_loop(self):
        # Check if the world's loop has come to an end
        # or user has interrupted simulation.
        if self.user_break:
            end = True
        elif self.max_steps is None:
            end = False
        else:
            end = self.steps >= self.max_steps

        return end

    def process_key_stroke(self, key):
        # Process user's keyboard input:
        #   - Left / right / up key to control simulation speed.
        #   - Down key for a step-by-step simulation.
        #   - Space to pause/un-pause world simulation.
        #   - Q/q to quit simulation
        #   - Tab to change tracked_agent.

        if key == -1:  # No key pressed.
            pass
        elif key in [ui.KEY_LEFT, ui.KEY_SLEFT]:  # Slow down speed.
            self.update_fps(fps_factor=0.5)
            self.step_by_step = False
        elif key in [ui.KEY_RIGHT, ui.KEY_SRIGHT]:  # Faster speed.
            self.update_fps(fps_factor=2.0)
            self.step_by_step = False
        elif key in [ui.KEY_UP]:  # Go full speed!
            self.update_fps(fps_factor=None)
            self.step_by_step = False
        elif key in [ui.KEY_DOWN]:  # Go step-by-step.
            self.paused = False
            self.step_by_step = True
        elif key == ord(' '):  # Pause/un-pause the world.
            if self.paused or self.step_by_step:
                self.paused = self.step_by_step = False
            else:
                self.paused = True
                self.step_by_step = False
        elif key in [ord('Q'), ord('q')]:
            if self.paused or self.step_by_step:
                self.user_break = True
                self.paused = self.step_by_step = False
        elif key == ord('\t'):  # Track a different agent.
            initial_idx = idx = self.agents.index(self.tracked_agent)
            next_agent = None
            end_search = False
            while not end_search:
                # Pick next index, and its corresponding agent.
                if idx == len(self.agents) - 1:
                    idx = 0
                else:
                    idx += 1
                next_agent = self.agents[idx]
                # Check if valid [alive and no void 'action'], or if full cycle is complete.
                if (next_agent.action is not None and next_agent.energy > 0) or idx == initial_idx:
                    end_search = True
            self.tracked_agent = next_agent
        else:
            self.paused = False
            self.step_by_step = False


###############################################################
# MAIN PROGRAM
# (code for TESTING purposes only.)

if __name__ == '__main__':
    print("world.py is a module of Lil' Grid Lab and has no real main module.")
    _ = input("Press to exit...")
