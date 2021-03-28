# taskplan

Taskplan is a simple task-planning tool.

Given a specification which outlines a number of tasks, how long they will
take, and who's available to perform them, it calculates a plan for
how they can be efficiently scheduled and how long overall execution
will take. In other words, given a bunch of tasks and their dependencies,
it attempts to compute a Gantt chart for an efficient solution.

While the plan itself is likely to be a little too "spherical-cow" to be
directly useful, the main aim is to convert time estimates for a number
of interdependent tasks into time estimates for a larger project as a whole.

If the individual estimates are stated probabilistically (i.e. as a
probability distribution instead of a fixed value), Taskplan can determine
the probability distribution of the duration of the whole project using
simulations.

The program uses a simple YAML format for input and output. See
`examples/house.yaml` for an example of the input, and
`examples/house.solution.yaml` for an example of the output.

It can also render a simple visualization of a generated solution.

Under the hood, Taskplan uses the [OR-Tools CP-SAT solver] to assign and
schedule tasks.

[OR-Tools CP-SAT solver]: https://developers.google.com/optimization/cp/cp_solver

## Example

```
$ poetry run python -m taskplan plan < examples/house.yaml > examples/house.solution.yaml
$ poetry run python -m taskplan render < examples/house.solution.yaml > viz.html
```

## Caveats

### Work-time vs. calendar time

Taskplan does its planning in arbitrary work-time seconds. (This absurd
resolution is to allow for some decimals, because the underlying approach is
_integer_ optimization.)

It does not account for non-work time, holidays, sleep, etc. If trying to
convert work-time seconds to a timeline, remember to perform this conversion.
For instance, assuming a 40h work-week, 1 million work-seconds should be
interpreted as roughly 7 work-weeks. Using 1 million seconds (roughly 12 days)
as a time estimate will give a blatantly wrong result.

### Simulation technique for handling uncertainty

When a model contains uncertainty, Taskplan will first determine a "plan" --
task assignments and ordering -- in the usual manner using integer optimization.
For the purposes of the optimization, the task durations are assumed to be
fixed at their medians.

After this plan is determined, it will run simulations using the pre-optimized
plan.

It is worth noting that a plan that is optimized for the median task durations
is not necessarily optimized for the realized task durations in any given
scenario. However, since one cannot generally know the precise task durations
in a project in advance, this lack of optimization for each specific scenario
to some degree reflects reality. (It is also a practical limitation: doing
optimization thousands of times would be _much_ more expensive than the
optimize-then-simulate approach.)
