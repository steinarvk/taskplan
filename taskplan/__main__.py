import click
import sys
import yaml
import json
import enum

from . import parse
from . import render
from . import planner


@click.group()
def main():
    pass


OUTPUT_FUNCS = {
    "text": render.print_console_solution,
    "html": lambda sol, fp: print(render.render_charts_html(sol), file=fp),
    "yaml": lambda sol, fp: yaml.dump(sol.dict(), fp),
    "json": lambda sol, fp: json.dump(sol.dict(), fp, indent="  "),
}


@main.command()
@click.option("--spec", type=click.File("r"), default="-")
@click.option("--output", type=click.File("x"), default="-")
@click.option("--output-format", type=click.Choice(list(OUTPUT_FUNCS)), default="yaml")
@click.option("--planning-time", type=float, default=60.0)
def plan(spec, planning_time, output, output_format):
    tasks = parse.parse_yaml_to_plannable_tasks(spec.read())
    solution = planner.calculate_plan(
        tasks,
        params=planner.SolverParams(
            time_seconds=planning_time,
        ),
    )
    OUTPUT_FUNCS[output_format](solution, output)


@main.command(name="render")
@click.option("--solution", type=click.File("r"), default="-")
@click.option("--output", type=click.File("x"), default="-")
@click.option("--output-format", type=click.Choice(list(OUTPUT_FUNCS)), default="html")
def render_(solution, output, output_format):
    solution = planner.Solution.parse_obj(yaml.safe_load(solution))
    OUTPUT_FUNCS[output_format](solution, output)


if __name__ == "__main__":
    main()
