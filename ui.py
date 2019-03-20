###############################################################
# User Interface
# for "Lil' ASCII Lab"

###############################################################

import numpy as np
import random
import curses
import os
import datetime
from curses import wrapper

# Constants based on curses' 8 basic colors:
BLACK = curses.COLOR_BLACK
BLUE = curses.COLOR_BLUE
CYAN = curses.COLOR_CYAN
GREEN = curses.COLOR_GREEN
MAGENTA = curses.COLOR_MAGENTA
RED = curses.COLOR_RED
WHITE = curses.COLOR_WHITE
YELLOW = curses.COLOR_YELLOW

colors = (BLACK, BLUE, CYAN, GREEN, MAGENTA, RED, WHITE, YELLOW)
color_names = ("BLACK", "BLUE", "CYAN", "GREEN", "MAGENTA", "RED", "WHITE", "YELLOW")

NORMAL = 0  # No offset for normal colors (1..8).
BRIGHT = 8  # Offset to get brighter colors, assuming COLORS >= 16 .
MAX_COLORS = 16  # The number of predefined colors to try to use.

LOW_ENERGY_THRESHOLD = 0.20  # Below this % energy is displayed as dangerously low.

# Output settings: Define how I/O will happen:
UI_def = {
    "resize_term": True,  # Flag to allows resizing the actual terminal where program runs.
    "spacing": 1, # Number of 'spc' chars to concatenate at the right of every tile (for an even vert/horiz aspect ratio).
    "extend_blocks": False,  # Whether blocks will be doubled to cover "holes".
    "min_ui_width": 20,  # Minimum width for the text interface, regardless of board size.
    "min_ui_height": 15,  # Minimum height for the text interface, regardeless of board size.
    "max_size": 100,  # Maximum size for width of height for the world (TODO: manage too big worlds).
    "header2_width": 6,  # Header space reserved for " LIVE ", "PAUSED", etc.
    "tracking_width": 60,  # Width for the tracking space will be set up on the right.
    "tracking_right_column": 36,  # Column where the right section of the tracker starts.
    "name_length": 10,  # Maximum length displayed of agents' names.
    "window_bg": BLACK,  # BG color of the full terminal window.
    "header_fg": WHITE + NORMAL,  # FG color of the TITLE of the world.
    "header_bg": BLUE + NORMAL,  # BG color of the TITLE of the world.
    "header_bg2": RED + BRIGHT,  # BG color of the shorter special field.
    "header_bg3": MAGENTA + BRIGHT,  # BG color of the shorter special field.
    "footer_fg": BLACK + NORMAL,  # FG color of the FOOTER.
    "footer_bg": WHITE + NORMAL,  # BG color of the FOOTER.
    "tracker_fg": GREEN,  # FG color of the Tracker window.
    "tracker_bg": BLACK + NORMAL,  # BF color of the Tracker window.
}


###############################################################
# CLASSES

class UI:
    def __init__(self, stdscr, world):
        # Register curses screen and world to represent. Initialize attributes.
        self.stdscr = stdscr
        self.world = world

        # Check IO settings.
        self.resize_term = UI_def["resize_term"]
        self.spc_len = UI_def["spacing"]  # Multiplier for tiles spacing.
        self.spc_str = " " * self.spc_len  # Doubling columns for esthetic reasons.
        self.extend_blocks = UI_def["extend_blocks"]
        self.tracker_width = UI_def["tracking_width"]
        self.tracking_right_column = UI_def["tracking_right_column"]
        self.name_length = UI_def["name_length"]

        # UI layout dimensions.
        self.height = max(UI_def["min_ui_height"], 1 + self.world.height + 1)  # header + board + footer.
        self.board_width = max(UI_def["min_ui_width"],
                               self.world.width * (1 + self.spc_len))  # Adapt to settings, with a minimum width.
        self.width = self.board_width + self.tracker_width
        self.header2_width = UI_def["header2_width"]
        self.tracker_height = UI_def["min_ui_height"]

        # Check if UI dimensions fit in terminal.
        self.safe_columns = 1  # Number of extra characters on the right.
        term_size_ok, term_height, term_width = self.handle_terminal_size(self.stdscr)
        if not term_size_ok:
            raise Exception(
                "World and UI ({} x {}) don't fit in the terminal ({} x {}).".format(self.height, self.width,
                                                                                     term_height, term_width))

        # Reshape aspect of world's blocks to fit UI settings.
        self.reshape_blocks(self.world.blocks)

        # Produce AUX strings.
        self.tracker_frame_1 = "┌" + "─" * (self.tracker_width - 2) + "┐"
        self.tracker_frame_2 = "│" + " " * (self.tracker_width - 2) + "│"
        self.tracker_frame_3 = "└" + "─" * (self.tracker_width - 2) + "┘"

        # Initialize curses settings.
        self.stdscr.nodelay(False)  # Enable waiting for user input stop.
        curses.curs_set(2)  # Set cursor as 'very' visible.

        # COLORS: try to initialize curses' pairs; set UI colors as defined.
        self.has_colors, self.color_pairs = self.init_all_pairs()
        self.window_bg = UI_def["window_bg"]
        self.header_fg = UI_def["header_fg"]
        self.header_bg = UI_def["header_bg"]
        self.header_bg2 = UI_def["header_bg2"]
        self.header_bg3 = UI_def["header_bg3"]
        self.footer_fg = UI_def["footer_fg"]
        self.footer_bg = UI_def["footer_bg"]
        self.tracker_fg = UI_def["tracker_fg"]
        self.tracker_bg = UI_def["tracker_bg"]

        # Create curses windows (extending width by N extra columns for safe addstr()...).
        self.header = curses.newwin(1, self.board_width + self.safe_columns, 0, 0)
        self.board = curses.newwin(self.world.height, self.board_width + self.safe_columns, 1, 1)
        self.footer = curses.newwin(1, self.board_width + self.safe_columns, self.world.height + 1, 0)
        self.tracker = curses.newwin(UI_def["min_ui_height"], self.tracker_width + self.safe_columns, 0,
                                     self.board_width + 1)
        self.footer.keypad(True)  # Footer will handle keyboard input, so enabling cursor keys or navigation keys.

        # Fill in the background of all windows with their color.
        left_pair = self.pair(self.window_bg, self.window_bg)
        right_pair = self.pair(self.tracker_bg, self.tracker_bg)

        stdscr.bkgd(" ", left_pair)
        self.header.bkgd(" ", left_pair)
        self.board.bkgd(" ", left_pair)
        self.footer.bkgd(" ", left_pair)
        self.tracker.bkgd(" ", right_pair)

        stdscr.refresh()

    def reshape_blocks(self, world_blocks):
        # Reshape aspect of world's blocks to fit UI settings.
        if self.extend_blocks:
            reshape_factor = 1 + self.spc_len
        else:
            reshape_factor = 1
        for block in world_blocks:
            block.aspect = (block.aspect * reshape_factor)[:reshape_factor]

    def init_all_pairs(self):
        curses.use_default_colors()  # Set default values for colors (including transparency color number -1).
        has_colors = curses.has_colors()  # Boolean: whether the terminal can display colors

        color_pairs = np.full((MAX_COLORS, MAX_COLORS), 0)
        if has_colors:
            pair = 1  # Skip pair 0 ("wired" to black and white)
            # Terminal has colors: initialize pairs for curses
            for fg in range(MAX_COLORS):  # colors ranging from 0 to 15
                for bg in range(MAX_COLORS):  # colors ranging from 0 to 15
                    if curses.COLORS >= 16:
                        # Full allocation of all 16x16 pair combinations
                        curses.init_pair(pair, fg, bg)
                        color_pairs[fg, bg] = pair
                        pair += 1
                    else:
                        # Restrict to 8x8 pair combinations within the 16x16 shape
                        if (fg <= 8 and bg <= 8):
                            # Allocate new basic pair
                            curses.init_pair(pair, fg, bg)
                            color_pairs[fg, bg] = pair
                            pair += 1
                        else:
                            # Reuse lower preallocated pairs
                            color_pairs[fg, bg] = color_pairs[max(fg, fg - 8), max(bg, bg - 8)]

        else:
            # Terminal has NO colors: leave ALL pairs as 0 (curses' default pair for fg/bg)
            pass

        return has_colors, color_pairs

    def pair(self, fg, bg):
        return curses.color_pair(self.color_pairs[fg, bg])

    def handle_terminal_size(self, stdscr):
        if self.resize_term:
            self.resize_terminal(self.height, self.width + 2 * self.safe_columns)
            curses.resize_term(self.height, self.width + 2 * self.safe_columns)
        term_height, term_width = stdscr.getmaxyx()
        if term_height >= self.height and term_width >= self.width:
            term_size_ok = True  # UI will fit in terminal.
        else:
            term_size_ok = False
        return (term_size_ok, term_height, term_width)

    def resize_terminal(self, rows, columns):
        # Xterm Control Sequences through “CSI” (“Control Sequence Introducer”).
        # Resize terminal.
        os.system("printf '\e[8;{};{}t'".format(rows, columns))

    def draw_header(self, color_pair):
        # Header: put world's name at top left.
        title = " " + self.world.name + " "
        fill = " " * max(0, self.board_width - len(title))
        pair = self.pair(self.header_fg, self.header_bg)
        self.header.addnstr(0, 0, title + fill, self.board_width - self.header2_width, color_pair | curses.A_BOLD)
        self.header.noutrefresh()

    def draw_header2(self, text, color_pair):
        # Header: put text at top right.
        title2 = (text.center(self.header2_width))[:self.header2_width]
        self.header.addstr(0, self.board_width - self.header2_width, title2, color_pair)
        self.header.noutrefresh()

    def say(self, text):
        # Print some text on footer area.
        self.footer.erase()
        pair = self.pair(self.footer_fg, self.footer_bg)
        self.footer.addnstr(0, 0, text.ljust(self.board_width - 1), self.footer.getmaxyx()[1] - 2, pair)
        self.footer.noutrefresh()

    def ask(self, question):
        # Ask user for input on footer zone.
        # But first, signal the simulation is paused.
        pair = self.pair(self.header_fg, self.header_bg2)
        self.draw_header2("PAUSED", pair)

        curses.flushinp()  # Throw away any typeahead not yet processed.
        self.footer.erase()  # Erase footer window.
        pair = self.pair(self.footer_fg, self.footer_bg)
        self.footer.addnstr(0, 0, question.ljust(self.board_width - 1), self.footer.getmaxyx()[1] - 2,
                            pair | curses.A_BLINK)
        self.footer.refresh()
        answer = self.footer.getkey()
        return answer

    def draw_board(self):
        # Update board state.
        x_tracked, y_tracked = self.world.tracked_agent.position

        for y in range(self.world.height - 1, -1, -1):
            x_screen = 0
            for x in range(self.world.width):
                thing = self.world.things[x, y]
                if thing == None:
                    # Emtpy TILE here. May be highlighted.
                    tile = self.world.ground[x, y]
                    text = tile.aspect + self.spc_str
                    if (x_tracked - 1 <= x <= x_tracked + 1) and (y_tracked - 1 <= y <= y_tracked + 1):
                        color, intensity = WHITE, BRIGHT
                    else:
                        color, intensity = tile.color, tile.intensity
                    pair = self.pair(color + intensity, self.world.bg_color + self.world.bg_intensity)
                    self.board.addstr(self.world.height - y - 1, x_screen, text, pair | curses.A_NORMAL)
                else:
                    # Some AGENT/BLOCK here.
                    if thing in self.world.blocks:
                        # A BLOCK:
                        t_aspect = thing.aspect
                        if t_aspect[0] == " ":  # Generic full block style.
                            pair = self.pair(thing.color + thing.intensity, thing.color + thing.intensity)
                        else:
                            pair = self.pair(thing.color + thing.intensity,
                                             self.world.bg_color + self.world.bg_intensity)
                        # Display the block.
                        self.board.addstr(self.world.height - y - 1, x_screen, t_aspect, pair | curses.A_BOLD)
                    else:
                        # An AGENT:
                        if thing.current_energy_delta > 0:
                            pair = self.pair(thing.color + thing.intensity, thing.color + NORMAL)
                        else:
                            pair = self.pair(thing.color + thing.intensity,
                                             self.world.bg_color + self.world.bg_intensity)
                        if 0 < thing.energy < thing.max_energy * LOW_ENERGY_THRESHOLD:
                            pair = pair | curses.A_BLINK
                        # Display the agent and the required blanks right after.
                        self.board.addstr(self.world.height - y - 1, x_screen, thing.aspect, pair | curses.A_BOLD)
                        pair = self.pair(thing.color + thing.intensity, self.world.bg_color + self.world.bg_intensity)
                        self.board.addstr(self.spc_str, pair)
                x_screen += 1 + self.spc_len  # X must follow specific spacing.
        self.board.noutrefresh()

    def draw_tracker(self):
        # Define colors.
        fg_color_pair = self.pair(self.tracker_fg, self.tracker_bg)
        fg_bright_color_pair = self.pair(self.tracker_fg + BRIGHT, self.tracker_bg)
        red_color_pair = self.pair(RED, self.tracker_bg)
        bright_red_color_pair = self.pair(RED + BRIGHT, self.tracker_bg)
        tracked_agent = self.world.tracked_agent
        agent_color_pair = self.pair(tracked_agent.color + tracked_agent.intensity, self.tracker_bg)

        # Clean up and draw a fresh Box.
        self.tracker.erase()
        self.tracker.addstr(0, 0, self.tracker_frame_1, fg_bright_color_pair)
        for y in range(1, self.tracker_height - 1):
            self.tracker.addstr(y, 0, self.tracker_frame_2, fg_bright_color_pair)
        self.tracker.addstr(self.tracker_height - 1, 0, self.tracker_frame_3, fg_bright_color_pair)

        # Tracked agent: header.
        self.tracker.addstr(0, 1, "[ ", fg_bright_color_pair)
        self.tracker.addstr(tracked_agent.aspect, agent_color_pair | curses.A_BOLD)
        self.tracker.addstr(" ({}) ".format(tracked_agent.name[:self.name_length]), fg_bright_color_pair)
        energy_percent = round(100 * tracked_agent.energy / tracked_agent.max_energy)
        n_blocks = 5
        n_greens = round(n_blocks * energy_percent / 100)
        n_reds = n_blocks - n_greens
        for i in range(n_greens):
            self.tracker.addstr("▉", fg_color_pair)
        for i in range(n_reds):
            self.tracker.addstr("▉", red_color_pair)
        self.tracker.addstr(" {}% ]".format(energy_percent), fg_bright_color_pair)

        # Tracked agent: energy.
        self.tracker.addstr(2, 2, "{:<14}".format('Energy:'), fg_color_pair)
        if tracked_agent.energy > tracked_agent.max_energy * LOW_ENERGY_THRESHOLD:
            pair = fg_bright_color_pair
        else:
            pair = bright_red_color_pair
        self.tracker.addstr("{:.1f}".format(tracked_agent.energy), pair)
        self.tracker.addstr("/{:.0f} ".format(tracked_agent.max_energy), fg_bright_color_pair)
        if tracked_agent.current_energy_delta < 0:
            self.tracker.addstr("{:.1f}".format(tracked_agent.current_energy_delta), bright_red_color_pair)
        elif tracked_agent.current_energy_delta > 0:
            self.tracker.addstr("+{:.1f}".format(tracked_agent.current_energy_delta), fg_bright_color_pair)

        # Tracked agent: Other information.
        self.tracker.addstr(3, 2, "{:<14}".format("AI:"), fg_color_pair)
        self.tracker.addstr("{}".format(tracked_agent.mind.__name__), fg_bright_color_pair)
        self.tracker.addstr(4, 2, "{:<14}".format(" "), fg_color_pair)
        self.tracker.addstr("{}".format(tracked_agent.senses.__name__), fg_bright_color_pair)

        if tracked_agent.chosen_action_success:
            pair = fg_bright_color_pair
        else:
            pair = bright_red_color_pair
        self.tracker.addstr(6, 2, "{:<14}".format('Action:'), fg_color_pair)
        self.tracker.addstr("{} {}".format(tracked_agent.chosen_action[0], tracked_agent.chosen_action[1]), pair)

        self.tracker.addstr(7, 2, "{:<14}".format('Carrying:'), fg_color_pair)
        self.tracker.addstr("{}".format('[]'), fg_bright_color_pair)
        self.tracker.addstr(8, 2, "{:<14}".format('Message:'), fg_color_pair)
        self.tracker.addstr("{}".format('[]'), fg_bright_color_pair)
        self.tracker.addstr(9, 2, "{:<14}".format('Explored:'), fg_color_pair)
        self.tracker.addstr("{}".format('-'), fg_bright_color_pair)
        self.tracker.addstr(10, 2, "{:<14}".format('Plc_holdr:'), fg_color_pair)
        self.tracker.addstr("{}".format('012345678901234567890123456789'), fg_bright_color_pair)

        # Rest of Things (agents, blocks?).
        y = 2  # Initial line.
        agents_list = self.world.agents[
                      :self.tracker_height - 4]  # Pick top of list, preserving 2 top rows + 2 bottom rows.
        for agent in agents_list:
            agent_color_pair = self.pair(agent.color + agent.intensity, self.tracker_bg)
            if agent == tracked_agent:
                prefix = "▶ "
            else:
                prefix = "  "
            self.tracker.addstr(y, self.tracking_right_column, prefix, fg_bright_color_pair)
            self.tracker.addstr(agent.aspect, agent_color_pair)
            self.tracker.addstr(" {:<11}".format(agent.name[:self.name_length]), fg_color_pair)
            if agent.energy > agent.max_energy * LOW_ENERGY_THRESHOLD:
                pair = fg_bright_color_pair
            else:
                pair = bright_red_color_pair
            self.tracker.addstr(" {:>6.2f}".format(agent.energy), pair)
            y += 1

        # Tracker's footer.
        time_run = str(datetime.timedelta( \
            seconds=(self.world.steps * self.world.spf) // 1))
        left_line = " Step {:,} ({}) ".format(self.world.steps, time_run)
        right_line = " Lil' ASCII Lab 0.1 "
        self.tracker.addstr(self.tracker_height - 1, 1, left_line, fg_bright_color_pair | curses.A_REVERSE)
        self.tracker.addstr(self.tracker_height - 1, self.tracker_width - 1 - len(right_line), right_line,
                            fg_bright_color_pair)

        # All ready to refresh.
        self.tracker.noutrefresh()

    def draw(self):
        # Generate and display a full refresh of the world state using curses lib.

        # Erase screen first.
        self.stdscr.erase()

        # HEADER: Title on top + status.
        self.draw_header(self.pair(self.header_fg, self.header_bg))
        self.draw_header2("LIVE", self.pair(self.header_fg, self.header_bg2))

        # BOARD: Update world representation.
        self.draw_board()

        # TRACKER: Update current state of the world.
        self.draw_tracker()

        # FOOTER: Update message at bottom.
        self.say("(running...)")

        # Refresh screen.
        curses.doupdate()


###############################################################
# MAIN PROGRAM
# code for TESTING purposes only.

def main(scr):
    scr.scrollok(True)  # Not really working, so limiting tests to terminal's height.

    # Call as main module generates a series of tests on the terminal.
    if not curses.has_colors():
        # Print basic b&w message.
        scr.erase()
        scr.addstr(0, 0, "This is a B&W terminal. Press to exit...", 0)
        scr.refresh()
        _ = scr.getkey()
    else:
        # Go for the colors.
        curses.use_default_colors()  # Set default values for colors (including transparency color number -1).
        c_colors = curses.COLORS  # The full capacity.
        n_colors = min(16, c_colors)  # Demo is limited to 16 colors.
        color_pairs = np.full((n_colors, n_colors), 0)

        # Loop over possible pairs.
        scr.erase()

        # Start reporting.
        scr.addstr(0, 0, "This terminal can use {} colors. See some combinations:".format(c_colors), 0)

        pair = 1
        n_pairs = 0
        for fg in range(n_colors):  # Loop over FG colors.
            for bg in range(n_colors):  # Loop over BG colors.
                if c_colors >= 16:
                    curses.init_pair(pair, fg, bg)
                    color_pairs[fg, bg] = pair
                    pair += 1
                else:
                    if fg <= 8 and bg <= 8:
                        curses.init_pair(pair, fg, bg)
                        color_pairs[fg, bg] = pair
                        pair += 1
                    else:
                        color_pairs[fg, bg] = color_pair[max(fg, fg - 8), max(bg, bg - 8)]
                n_pairs += 1

        # Demo out some combinations.
        max_y, _ = scr.getmaxyx()
        for y in range(1, max_y - 1):
            pair = random.randint(1, n_pairs)
            scr.addstr(y, 0, "  Random fg&bg colors  ", curses.color_pair(pair))
            y += 1

        # Final message.
        scr.addstr(y, 0, "Press to exit...", 0)
        scr.refresh()
        _ = scr.getkey()


if __name__ == '__main__':
    # Call as main module generates a series of tests on the terminal.
    print("ui.py is a module of Lil' ASCII Lab.")
    _ = input("Press to test some of 'ncurses' colors...")
    wrapper(main)
