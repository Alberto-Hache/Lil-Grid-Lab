###############################################################
# Lil' ASCII Lab
# Main world simulation loop.

###############################################################

# Libraries.
from curses import wrapper
import time

# Modules.
import world as w
import ui


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

    # Create the world and start "wrapped" environment.
    world = w.World(w.Simulation_def)
    wrapper(main_loop, world)

    # Quit program.
    print("Lil' ASCII Lab v0.1")
    print("{:<20}{}".format("- Started:", time_0))
    print("{:<20}{}".format("- Ended:", time.ctime()))
    print("{:<20}{:,}".format("- Steps run:", world.steps))
    print("{:<20}{}".format("- Random seed used:", world.random_seed))
