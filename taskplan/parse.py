import yaml
import collections
from functools import reduce

from . import dist
from . import planner

from pydantic import BaseModel, Extra
from typing import List, Optional, Union, Dict


class Task(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    name: str
    duration: dist.Dist
    milestone: List[str]
    worker: List[str]
    requires: List[str]


class Worker(BaseModel):
    name: str
    group: List[str]


class Model(BaseModel):
    tasks: Dict[str, Task]
    workers: Dict[str, Worker]
    milestones: Dict[str, List[str]]
    workergroups: Dict[str, List[str]]


class _RawLogNormalDist(BaseModel):
    p50: Union[str, int]
    p95: Union[str, int]


_NumberOrDist = Union[int, _RawLogNormalDist]


class _RawTask(BaseModel):
    name: str
    duration: Union[str, _NumberOrDist]
    milestone: Optional[Union[str, List[str]]]
    worker: Optional[Union[str, List[str]]]
    requires: Optional[Union[str, List[str]]]


class _RawWorker(BaseModel):
    name: str
    group: Optional[Union[str, List[str]]]


class _RawModel(BaseModel):
    tasks: List[_RawTask]
    workers: Optional[List[Union[str, _RawWorker]]]


def _parse_dist(x: Union[str, _NumberOrDist]) -> dist.Dist:
    if isinstance(x, str):
        x = _parse_humanized_duration(x)

    if isinstance(x, int):
        return dist.Constant(x)

    assert not isinstance(x, float)

    assert isinstance(x, _RawLogNormalDist)
    return dist.LogNormal(
        p50=_parse_humanized_duration(x.p50),
        p95=_parse_humanized_duration(x.p95),
    )


def _parse_humanized_duration(s: Union[str, int]) -> int:
    if isinstance(s, int):
        return s

    try:
        return int(s)
    except ValueError:
        pass

    if s[-1] == "h":
        return int(s[:-1]) * 3600

    if s[-1] == "m":
        return int(s[:-1]) * 60

    raise ValueError(f"bad duration: {s}")


def _parse_comma_string(x: str) -> List[str]:
    return [u.strip() for u in x.split(",") if u.strip()]


def _convert_to_list(x: Optional[Union[str, List[str]]]) -> List[str]:
    if not x:
        return []
    if isinstance(x, str):
        return _parse_comma_string(x)

    rv = []
    rvset = set()
    for item in x:
        for parsed in _parse_comma_string(item):
            if parsed in rvset:
                continue
            rvset.add(parsed)
            rv.append(parsed)
    return rv


def _parse_raw_worker(rw: Union[str, _RawWorker]) -> Worker:
    if isinstance(rw, str):
        return Worker(
            name=rw,
            group=[],
        )

    return Worker(
        name=rw.name,
        group=_convert_to_list(rw.group),
    )


def _make_workers_dict(workers: List[Worker]) -> Dict[str, Worker]:
    workers_dict = {}
    for w in workers:
        if w.name in workers_dict:
            raise BadModelError(f"duplicate worker {repr(w)}")
        workers_dict[w.name] = w
    return workers_dict


def _make_tasks_dict(tasks: List[Task]) -> Dict[str, Task]:
    tasks_dict = {}
    for t in tasks:
        if t.name in tasks_dict:
            raise BadModelError(f"duplicate task {repr(t)}")
        tasks_dict[t.name] = t
    return tasks_dict


def _collect_milestones(tasks: List[Task]) -> Dict[str, List[str]]:
    rv = collections.defaultdict(set)

    for task in tasks:
        rv[task.name].add(task.name)

        for ms in task.milestone:
            rv[ms].add(task.name)

    return {k: list(sorted(v)) for k, v in rv.items()}


def _collect_groups(workers: List[Worker]) -> Dict[str, List[str]]:
    rv = collections.defaultdict(set)

    for w in workers:
        rv[w.name].add(w.name)

        for g in w.group:
            rv[g].add(w.name)

    return {k: list(sorted(v)) for k, v in rv.items()}


def _derive_workers(tasks: List[Task]) -> List[Worker]:
    nameset = set()
    for t in tasks:
        for g in t.worker:
            nameset.add(g)

    names = list(nameset)
    names.sort()
    return [
        Worker(
            name=name,
            group=[],
        )
        for name in names
    ]


class BadModelError(Exception):
    pass


def parse_yaml_model(yamldata: str) -> Model:
    loaded = yaml.safe_load(yamldata)
    raw = _RawModel.parse_obj(loaded)

    tasks = []
    for rawtask in raw.tasks:
        tasks.append(
            Task(
                name=rawtask.name,
                duration=_parse_dist(rawtask.duration),
                milestone=_convert_to_list(rawtask.milestone),
                worker=_convert_to_list(rawtask.worker),
                requires=_convert_to_list(rawtask.requires),
            )
        )

    workers = []
    if not raw.workers:
        workers.extend(_derive_workers(tasks))
    else:
        for rawworker in raw.workers:
            workers.append(_parse_raw_worker(rawworker))

    tasks_dict = _make_tasks_dict(tasks)
    workers_dict = _make_workers_dict(workers)

    workergroups = _collect_groups(workers)
    milestones = _collect_milestones(tasks)

    for t in tasks:
        if not t.worker:
            raise BadModelError(f"task {t.name}: no worker or group assigned")

        for g in t.worker:
            if g not in workergroups:
                raise BadModelError(
                    f"task {t.name}: reference to unknown worker/group {repr(g)}"
                )

        for ot in t.requires:
            if ot not in milestones:
                raise BadModelError(
                    f"task {t.name}: reference to unknown task/milestone {repr(ot)}"
                )

    return Model(
        tasks=tasks_dict,
        workers=workers_dict,
        workergroups=workergroups,
        milestones=milestones,
    )


def _get_eligible_worker_names(m: Model, t: Task) -> List[str]:
    sets = []

    for w in t.worker:
        sets.append(set(m.workergroups[w]))

    combined = reduce(lambda a, b: a | b, sets)
    return sorted(list(combined))


def _get_required_task_names(m: Model, t: Task) -> List[str]:
    sets = []

    for req in t.requires:
        sets.append(set(m.milestones[req]))

    if not sets:
        return []

    combined = reduce(lambda a, b: a | b, sets)
    return sorted(list(combined))


def model_to_plannable_tasks(m: Model) -> List[planner.Task]:
    rv = []

    for t in m.tasks.values():
        requires_task_names = _get_required_task_names(m, t)
        eligible_worker_names = _get_eligible_worker_names(m, t)
        rv.append(
            planner.Task(
                name=t.name,
                duration=round(t.duration.mean),
                workers=eligible_worker_names,
                requires=requires_task_names,
            )
        )

    return rv


def parse_yaml_to_plannable_tasks(s: str) -> List[planner.Task]:
    return model_to_plannable_tasks(parse_yaml_model(s))


if __name__ == "__main__":
    import sys
    from . import render

    tasks = parse_yaml_to_plannable_tasks(sys.stdin.read())
    solution = planner.calculate_plan(
        tasks,
        params=planner.SolverParams(
            time_seconds=10,
        ),
    )

    render.print_console_solution(solution, sys.stderr)
    print(render.render_charts_html(solution))
