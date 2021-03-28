import collections
import json
import time
import typing

from dataclasses import dataclass

from typing import List, Dict, Optional, Tuple

from ortools.sat.python import cp_model  # type: ignore


@dataclass
class Task:
    name: str
    duration: int
    workers: List[str]
    requires: List[str]


@dataclass
class Worker:
    name: str


@dataclass
class TaskSolution:
    task_name: str
    worker_name: str
    start: int
    end: int


@dataclass
class SolverParams:
    time_seconds: float


@dataclass
class SolutionMetadata:
    params: SolverParams
    solver_time_seconds: float


@dataclass
class Solution:
    tasks: Dict[str, TaskSolution]
    workers: Dict[str, List[TaskSolution]]
    total_duration: int
    optimal: bool
    meta: Optional[SolutionMetadata]


DEFAULT_SOLVER_PARAMS = SolverParams(
    time_seconds=5.0,
)


class CyclicDependenciesError(Exception):
    pass


def _toposort_tasks(tasks: List[Task]) -> List[Task]:
    rv = []
    done = set()

    remaining = list(tasks)
    while remaining:
        new_remaining = []
        for task in remaining:
            unmet = [req for req in task.requires if req not in done]
            if unmet:
                new_remaining.append(task)
            else:
                rv.append(task)
                done.add(task.name)

        if len(new_remaining) == len(remaining):
            raise CyclicDependenciesError("cyclic dependencies")
        remaining = new_remaining

    return rv


def calculate_plan(
    tasks: List[Task],
    workers: Optional[List[Worker]] = None,
    params: Optional[SolverParams] = None,
) -> Solution:
    params = params or DEFAULT_SOLVER_PARAMS
    workers = workers or [
        Worker(s) for s in sorted(set([w for task in tasks for w in task.workers]))
    ]

    tasks = _toposort_tasks(tasks)

    tasks_by_name = {task.name: i for i, task in enumerate(tasks)}
    workers_by_name = {w.name: i for i, w in enumerate(workers)}
    total_duration = sum(task.duration for task in tasks)

    model = cp_model.CpModel()

    task_assignment_vars = []
    task_start_vars = []
    task_end_vars = []

    for task in tasks:
        prefix = f"task_{task.name}_"

        assignment_var = model.NewIntVar(0, len(workers) - 1, prefix + "assignment")
        model.AddAllowedAssignments(
            [assignment_var], [(workers_by_name[k],) for k in task.workers]
        )
        task_assignment_vars.append(assignment_var)

        task_start_var = model.NewIntVar(0, total_duration, prefix + "start")
        task_end_var = model.NewIntVar(0, total_duration, prefix + "end")
        task_interval_var = model.NewIntervalVar(
            task_start_var, task.duration, task_end_var, prefix + "interval"
        )

        task_start_vars.append(task_start_var)
        task_end_vars.append(task_end_var)

        for req in task.requires:
            reqtask_index = tasks_by_name[req]
            required_task_end_var = task_end_vars[reqtask_index]  # should be toposorted
            model.Add(task_start_var >= required_task_end_var)

    worker_is_assigned_vars = []
    for i, worker in enumerate(workers):
        worker_task_interval_vars = []

        for j, task in enumerate(tasks):
            prefix = f"worker_{worker.name}_task_{task.name}_"

            task_is_assigned_var = model.NewBoolVar(prefix + "is_assigned")
            model.Add(task_assignment_vars[j] == i).OnlyEnforceIf(task_is_assigned_var)
            model.Add(task_assignment_vars[j] != i).OnlyEnforceIf(
                task_is_assigned_var.Not()
            )
            worker_is_assigned_vars.append(task_is_assigned_var)

            task_duration = model.NewIntVar(0, task.duration, prefix + "duration")
            model.Add(task_duration == task.duration).OnlyEnforceIf(
                task_is_assigned_var
            )
            model.Add(task_duration == 0).OnlyEnforceIf(task_is_assigned_var.Not())

            task_start = model.NewIntVar(0, total_duration, prefix + "start")
            task_end = model.NewIntVar(0, total_duration, prefix + "end")
            task_intv = model.NewIntervalVar(
                task_start, task_duration, task_end, prefix + "interval"
            )

            model.Add(task_start == task_start_vars[j]).OnlyEnforceIf(
                task_is_assigned_var
            )
            model.Add(task_end == task_end_vars[j]).OnlyEnforceIf(task_is_assigned_var)

            worker_task_interval_vars.append(task_intv)

        model.AddNoOverlap(worker_task_interval_vars)

    total_time = model.NewIntVar(0, total_duration, "_total_makespan")
    model.AddMaxEquality(total_time, task_end_vars)
    model.Minimize(total_time)

    solver = cp_model.CpSolver()
    if params.time_seconds:
        solver.parameters.max_time_in_seconds = params.time_seconds

    t0 = time.time()
    status = solver.Solve(model)
    t1 = time.time()
    solution_time = t1 - t0

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"Solver exited with status: {status}")

    optimal = status == cp_model.OPTIMAL

    task_solutions_list = []

    for j, ass_task_var in enumerate(task_assignment_vars):
        assigned_worker_index = solver.Value(ass_task_var)
        assigned_worker = workers[assigned_worker_index]
        task_solutions_list.append(
            TaskSolution(
                task_name=tasks[j].name,
                worker_name=assigned_worker.name,
                start=solver.Value(task_start_vars[j]),
                end=solver.Value(task_end_vars[j]),
            )
        )

    task_solutions_list.sort(key=lambda task: task.start)

    task_solutions = {task.task_name: task for task in task_solutions_list}

    worker_solutions_dd = collections.defaultdict(list)

    for task_sol in task_solutions_list:
        worker_solutions_dd[task_sol.worker_name].append(task_sol)

    worker_solutions = {k.name: worker_solutions_dd[k.name] for k in workers}

    return Solution(
        tasks=task_solutions,
        workers=worker_solutions,
        total_duration=solver.Value(total_time),
        optimal=optimal,
        meta=SolutionMetadata(
            params=params,
            solver_time_seconds=solution_time,
        ),
    )
