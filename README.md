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

Taskplan does its planning in arbitrary work-time seconds. (This absurd
resolution is to allow for some decimals, because the underlying approach is
_integer_ optimization.)

It does not account for non-work time, holidays, sleep, etc. If trying to
convert work-time seconds to a timeline, remember to perform this conversion.
For instance, assuming a 40h work-week, 1 million work-seconds should be
interpreted as roughly 7 work-weeks. Using 1 million seconds (roughly 12 days)
as a time estimate will give a blatantly wrong result.
