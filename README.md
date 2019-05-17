# *"Lil' Grid Lab"*

(v 0.1) by Alberto H

## About this project

"Lil' Grid Lab" is a simple playground on which single-character beings come to life driven by their AI.
Currently, agents running around will have simple, hard-coded behaviours. The long-term plan is to integrate Machine Learning-driven agents in.

<img src="https://github.com/Alberto-Hache/Lil-ASCII-Lab/blob/master/screenshots/blocky-meadows.png" width="250">

## World rules

This is a tiled, rectangular world, consisting of these "Things":

* tiles
* blocks
* agents

A **'tile'** is just that, an empty place on which a block or agent can stand. Tiles cover the whole world.

A **'block'** is a most basic entity: it just **passively** occupies one tile, never moving and preventing agents from moving on it.

An **'agent'** is, finally, a **"living" entity**. It occupies a single tile too, but can perform specific actions on the world or other agents (but not on blocks). By doing this, it receives **immediate rewards** from the world.

A **'world'** is the setting on which a little universe takes life. This is how it works:

* worlds are initialized according to some pre-specified settings, which may include certain degrees of randomness.
* time flows as a **loop of *synchronous* 'steps' for all agents**.
* at **step start**, all agents get their status updated (including possible rewards from previous actions).
* **'during' the step**, each agent decides the action(s) to perform, as a request to the world (e.g. a move to other tile, an attack on other agent, grabbing some resource (which is just a most basing agent)).
* at **step end**, the world resolves the consequences of all requested actions (actually execute the move, or bounce against a block).
* now a new step can start, so all status are updated, and so on...

This loops goes on till some final condition is reached or the maximal number of steps has been executed, after which the world exits.

## Main loop's (simplified) pseudocode

    (start)
    initialize world with empty tiles and put blocks in
    initialize agents and put them on the world

    while (not finished)
    display the world
    check conditions to go on
    step start
        update state + rewards for agents
        request actions from agents (and user?)
        resolve results of actions from agents (and from user?)
        update the world
    step end

    display final state of the world
    (end)

## Defining a world and its inhabitants...

### World definition

* *name* of the world (e.g. "GridWorld").
* *width* in tiles (e.g. 30).
* *height* in tiles (e.g. 20).
* *bg_color* as one out of 7 basic colors to cover the background.
* *bg_intensity*, which is applied to bg_color as NORMAL or BRIGHT.
* *n_blocks_rnd*, max. % of variation in # of blocks (e.g. 0.4).
* *max_steps*, how long to run the world ('None' for infinite loop).
* *chk_steps*, how often to ask user for quit/go-on ('None' = never ask).
* *fps*, the number of stpes to run per second.
* *random_seed*, some given seed value to produce repeatable executions or None for random.

Example:

    World_def = {
        "name":         "Lil' Grid Lab",
        "width":        12,         # x from 0 to width - 1
        "height":       8,          # y from 0 to height - 1
        "bg_color":     ui.GREEN,   # background color
        "bg_intensity": ui.NORMAL,  # background intensity (NORMAL or BRIGHT)
        "n_blocks_rnd": 0.4,        # % of +/- randomness in number of blocks
        "max_steps":    None,       # How long to run the world ('None' for infinite loop)
        "chk_steps":    10,         # How often to ask user for quit/go-on ('None' = never ask)
        "fps":          12,         # Number of steps to run per second
        "random_seed":  None,       # Define seed to produce repeatable executions or None for random.
    }

### Tile definition

Each tile in the world has its own instance, though for now only ONE type of tile can be used in a world. This is how it's defined:

* *name* of the type of tile.
* *aspect* of the tile (a single character to cover the full world).
* *color* to use on _aspect_.
* *intensity* to use on *color*.
* *position* is a tuple with the [x, y] coordinates on which the tile is placed.

Example:

    Tile_def = (
        ("tile", "…", ui.GREEN, ui.BRIGHT, [None, None])
    )

### Block definition

Different types of block are possible, each with the following features:

* *number of instances* (or None for RND, based on world's width and % of randomness).
* *type*, i.e. its name.
* *aspect*:
  * " " for a generic full block (which will be doubled to fit world's spacing).
  * ONE single Unicode character, e.g. "#" (which will be replicated to fit world's spacing).
  * TWO Unicode characters for specific styles (e.g. "[]", "▛▜", "◢◣").
* *color & intensity*:  (see above).
* *position*: (a tuple, currently ignored).

Example:

    Block_def = (
        (8, "water", " ", ui.BLUE, ui.BRIGHT, [None, None]),
        (2, "block", "▛▜", ui.MAGENTA, ui.NORMAL, [None, None]),
        (None, "fence", "#", ui.BLACK, ui.BRIGHT, [None, None]),
    )

### Agent definition

Finally, a number of "living" things can be defined in a world, with the following features:

* *number of instances* to create at world start.
* *name* describing the type of agent.
* *aspect* for the agent as a single-character.
* *color & intensity*: (see above)
* *initial position* as a tuple, or [None, None] for an initial random place. If more than one instance, it will be ignored.
* *ai* (currently ignored).

Example:

    Agents_def = (
        (1, "Omi", "𝝮", ui.YELLOW, ui.BRIGHT, [0, 0], None),
        (3, "apple", "", ui.RED, ui.BRIGHT, [None, None], None),
        (3, "star", "*", ui.YELLOW, ui.BRIGHT, [None, None], None),
    )

### World initialization

This is how the world is started:

1. Firstly, *randomness* is determined based on the given seed.
1. Now the brand new empty world is fully covered with *tiles*.
1. *Agents* are then placed in order in the world according to their settings (including randomness as defined). Possible colisions are handled through random relocation.
1. Finally, *blocks* are placed in order similarly to agents.

## References

### ncurses

"Curses programming with Python"
<https://docs.python.org/3/howto/curses.html>

"curses — Terminal handling for character-cell displays"
<https://docs.python.org/3/library/curses.html#curses.pair_number>

### Unicode characters

List of Unicode characters
<https://en.wikipedia.org/wiki/List_of_Unicode_characters>

Graphic character, medium density dotted
<https://theasciicode.com.ar/extended-ascii-code/graphic-character-medium-density-dotted-ascii-code-177.html>