###############################################################
# Lil' Grid Lab
# Main world simulation loop.

###############################################################

# Libraries.
from curses import wrapper
import time
import argparse
import os

# Modules.
import world as w
import ui


def generate_simulation_definition(args):
    # Capture settings for the simulation from:
    # (1) Simulation definition (stored as a 'dict' in code for now).
    # (2) Arguments passed to program, possibly overriding (1).

    # (1) Capture definition set.
    simulation_def = w.Simulation_def  # TODO: read from yaml file.

    # (2) Process now arguments passed, overriding initial settings.

    # Check for aux/ folder.
    if not os.path.exists("aux"):
        os.makedirs("aux")

    # Arguments related to RANDOM SEED:
    if args.repeat:
        # Seed must be reused from previous simulation.
        with open("aux/seed.txt", "r") as f:
            seed = float(f.read())
        seed_source = "PREVIOUS"
    elif args.seed:
        # A seed was passed.
        seed = float(args.seed)
        seed_source = "PASSED"
        # Store the seed passed.
        with open("aux/seed.txt", "w") as f:
            f.write(str(seed))
    else:
        # No seed specified: check if set in world settings or generate one.
        seed = simulation_def["world"]["random_seed"]
        seed_source = "WORLD DEF"
        if seed is None:
            # A new seed must be generated.
            seed = time.time()
            seed_source = "NEW"
        else:
            seed = float(seed)
        # Store the new seed.
        with open("aux/seed.txt", "w") as f:
            f.write(str(seed))

    # Set now the seed in simulation_def.
    simulation_def["world"]["random_seed"] = seed
    print("Initialization with {} seed: {}".format(seed_source, seed))

    # Arguments related to PAUSE_STEP:
    if args.pause:
        simulation_def["world"]["pause_step"] = int(args.pause)

    return simulation_def


def process_args():
    # Process arguments passed, returning usable class:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    """
    TODO: manage 'world' argument passed.
    parser.add_argument(
        "world",
        help="file defining the world to load for simulation"
    )
    """
    parser.add_argument(
        "-p", "--pause",
        help="pause simulation at the specified step"
    )
    group.add_argument(
        "-r", "--repeat",
        action="count",
        help="repeat latest simulation (same random seed)"
    )
    group.add_argument(
        "-s", "--seed",
        help="random seed used in simulation (overrides config. file)"
    )
    # Return args:
    arguments = parser.parse_args()
    return arguments


def produce_final_results(world):
    print("Lil' Grid Lab v0.1")
    print("{:<20}{}".format("- Started:", time_0))
    print("{:<20}{}".format("- Ended:", time.ctime()))
    print("{:<20}{:,}".format("- Steps run:", world.steps))
    print("{:<20}{}".format("- Random seed used:", world.random_seed))


def main_loop(stdscr, world):
    '''
    :param stdscr: standard screen created by curses' wrapper.
    :param world: the world on which the simulation will run.
    :return: (nothing).
    '''

    # Initialize UI.
    u_i = ui.UI(stdscr, world)

    # Main world loop.
    end_loop = False
    while not end_loop:
        # Display the world as it is now.
        u_i.draw()

        # Check conditions to go on.
        end_loop = world.is_end_loop()
        if not end_loop:
            # Evolve world by one time-fixed step.
            t_start = time.time()
            world.step()
            if world.spf is not None:
                # No full-speed mode; keep time-step duration.
                t_end = time.time()
                time.sleep(max(0, world.spf - (t_end - t_start)))

    # Exit program.
    # TODO: Produce final results.

if __name__ == '__main__':
    # Main program.
    time_0 = time.ctime()  # Start time.

    # Create the world and start "curses-wrapped" environment.
    arguments = process_args()  # Capture arguments passed.
    simulation_def = generate_simulation_definition(arguments)
    world = w.World(simulation_def)
    wrapper(main_loop, world)

    # Quit program.
    produce_final_results(world)
