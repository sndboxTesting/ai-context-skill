# 🔬 Lab — SuneelWorkSpace Organ

## Purpose
Runs autolab experiments, self-challenges, and evolution loops.

## What\s Inside
* `autolab/`: Experiment runner, evaluator, and promotion gates.
* `evolution/`: Gap scanning and challenge generator.

## Key Files
* [lab/autolab/runner.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/runner.py): Autolab manager.
* [lab/autolab/evaluator.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/evaluator.py): Grader loops.
* [lab/evolution/engine.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/engine.py): Evolution engine background controller.

## Provides (to other organs)
* System optimization metrics and evolution challenger scripts.

## Needs (from other organs)
* Telemetry records from `blood`.
* Current health score from `spine`.

## CLI Commands
* `autolab-run`: Safe experiment loop runner.
* `autolab-status`: Lists experiment queues.
* `evolution-start`: Evolution daemon launch.
* `hypothesis-generate`: Hypotheses generation.

## How To Add Something Here
1. Write experiment definitions in `lab/autolab/experiments/active/`.
2. Create challenge templates in challenger.py.
