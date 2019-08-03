# Backlog

## Bugs

* .....

## NFR

* Review code to include clip() function (not min(), max()...).

## Overall features

1.0:

* Provide placeholder ML templates for the basic AI methods.
* Add basic metrics:
  * fps reached at full-speed.
  * Agents' performance (by type, top- / bottom- performers)
  * ...
* Basic profiling: obtain and analyze performance metrics on different conditions.
* PEP8 coding conventions:
  http://books.agiliq.com/projects/essential-python-tools/en/latest/linters.html
* Review TODO's and implement or move to backlog.
* Structure files and docs in repo (see: https://docs.python-guide.org/writing/structure/)
Future:

* Auto-pause the world when all agents are dead?
* Extract strings with program name, version, etc ("Lil' Grid Lab"...). from code.
* Add logging (using standard 'logging' module).
* L10N: Move all strings to ui.py or to yaml file(s).
* Refactor environment for asynchronous threads/processes?

## AI - Action

1.0:

* ...

Future:

* Implement "grass" tiles which:
  * Have some limited energy.
  * Get empty when used up.
  * Replenish over time.
  * Reproduce in good conditions (e.g. after some number of steps in healthy
    state)
* Refine wanderer / hunter: Move towards highest-energy accessible (i.e. visible) targets.
* Implement dynamics of inventory (grab, drop, max.weight...).

## AI - Perception

1.0:

* Generate all arrays required for perception (tensors, etc.).

Future:

* Visual limitation (full world, subsection around agent).
* Messages from other agents.
* Visual limitation: opacity of blocks.
* Other senses: (environment conditions, e.g. smell, lightness, rain, temperature...).

## UI - User Interface

1.0:

* ...

Future:

* Footer: Allow 2 lines when board is too narrow for text to fit.
* Board: make "dead" respawnable agents BLINK.
* Tracker (aesthetics): Review tracker's layout (split sub-areas?).
* Add color to logo at program exit.
* Implement basic agent animation in "aspect" (2 or 3 looping chars).
* Tracking: Maintain agents' heatmaps (where they've been around).
* Allow checkered background by alternating line patterns:
  "▐█▌ ▐█▌ ▐█▌ ▐█▌ ▐█▌ ▐█▌  "
  "  ▐█▌ ▐█▌ ▐█▌ ▐█▌☻▐█▌ ▐█▌"
* Handle resize terminal without exiting.
* Detect when resizing the terminal would exceed screen dimensions.

## World Dynamics

1.0:

* ...

Future:

* Review / generalize diffeferent game dynamics:
  * Full information / partially observable
  * Predictability / unpredictability (hidden info, inherent randomness)
  * Turn-based / pseudo-simultaneous / truly simultaneous
* Review / generalize pre-step sorting dynamics:
    a) Sort by enery level (benefits stronger agents; may generate undesired strategies if agents learn this advantage/disadvantage)
    b) Randomize: (probably the most fair and safe approach)
    c) Other?
* Improve world generation with patterns of blocks.
* Allow several 'respawn' options for AIs:
  * Full start: all memories and learnings wiped out.
  * Keep learnings: memories wiped out BUT learnings (the trained model(s)) are kept.
  * Keep everything: memories are kept and so are learnings (it's basically a random jump).
  * All cases: energy is refilled and new agent moved to a random position.
* Improve respawn (e.g. generalize agent's __init__ to clone a given agent?).
* Implement DELAYED recharge for agents (similar to batteries)?
* Maintain a count of number of instances per type of agent.
* Implement new agent's feature:
  * agents that can be picked, carried and dropped (e.g. fruits).
  * Rest of agents (can't be picked).
* Main loop: Decouple UI / AI refresh rates, e.g. one AI step every 5 UI steps.
* Consider creating "pit" blocks, causing instant death.


#######################################
# Available Features (add to README.md)
#######################################

Overall features:

* Add setting for auto-exit when no more agents are alive.
* Extract all world & agents config. to external yaml files.
* Handle maximum size of the world with detailed error.
* Add arguments to main program (module argparse).
  * world to load (yaml file)
  * seed ('repeat', number)
  * halt ('pause' simulation at some given step)
* Reproducibility throudh random seed:
  * Configuration parameter within world definition.
  * Command line argument overriding world definition.


AI:

* Create AI for 'killer':
    1. If loss just suffered is too high, escape from offending tile.
    2. If mid-loss suffered, or a bit hungry, bite any agent around.
    3. Otherwise, act as a regular 'wanderer'.
* Implement new AI: 'wanderer2', refinement on 'wanderer':
  * Escape from attacks:
    * Prioritize moving over feeding/no-action.
    * Choose best direction.
    * Otherwise, act as wanderer.
  * Prevent 2 hungry wanderers from coupling for good.
* Implement a basic random AI (e.g. random moves / still, with RND inertia).
* Refine AI for 'wanderer':
  * Not to miss adjacent food when energy starts to be low.
  * Choose highest-energy adjacent target for food.
* Implement "EAT" action.
* Implement full basic AI logic:
  * Input = Status + Reward, from the World. [DONE] 
  * Mind/policy run = hardcoded behaviours (random, herbivores, predators...). [DONE]
  * Mind/policy learn = placeholder for the learning method. [DONE]
  * Actions = Move, Eat, No-action. [DONE]


World dynamics:

* Allow "buying" action's priority by investing larger energy amounts? (faster = more expensive)
* execute_action(): check for impossible "EAT" actions (e.g. on a Block).
* Bite effect doesn't exceed agent's max_energy (limiting damage on prey).
* Implement new agent's energy dynamics:
  * a) fixed resources always at full energy ("stars").
  * b) mobile resources ("fruit") with limited energy.
* Implement dynamics of basic attributes: energy (initialization, consumption, death).
* Define dynamics at death. Once energy is 0, AI is no longer active.
* Implement synchronized steps, e.g. 12 fps, 24 fps.
* Allow Fast-Forward execution (off-clock).

UI:

* ui.draw(): allow UI action (select a new agent) on paused world by decoupling draw/step loops (draw would loop drawing the same frame till user moves on)!
* Improve highlight for tracked agent (blinking tiles around).
* Add Tab control during step-by-step mode.
* Add step-by-step control in "pause" menu to move fwd. 1 step.
* Tracker: Show current world speed (at fps, full-speed).
* Tracker: Tab selects only living agents with some mind.
* Tracker: Show agents with minds only (not mindless "resources").
* Add key controls:
  * Left / right key to control simulation speed.
  * Up key for full speed.
  * Space to pause simulation.
  * Tab to change tracked_agent.
* Tracker: Show AI identifiers = Mind + Senses.
* Tracker: Highlight tracked agent on the right (with "▶")
* Tracker: Differentiate agents' names.
* Tracker/World: Energy deltas displayed as number with red/green color.
* Tracker: Signal failed "FEED" actions.
* Tracker/World: Signal agent's about to die (blinking?).
* World: Differentiate tracked agent with surrounding highlights.
* World: Highlight when energy's won with a better BG, e.g. agent's color NORMAL.
* World: Change dead agents' color to grey, and no longer blinking on screen.
* Add ncurses terminal support for b&w, 8 or 16 colors.
* Handle sizes not fitting on terminal:
* Overall UI:
  * excessive board width
  * excessive board height
  * insufficient space for board + tracker

Add "Lil' ASCI Lab" logo to tracker.

Check Board for:

* Long world names
* Long "LIVE/PAUSED" strings?
* Long ask()/say() arguments

Check Tracker for:

* Long main character name
* Long number of steps
* long placeholder
