import collections
import dataclasses

from . import planner
from .dist import Dist

from typing import Dict, List


def replay_with_durations(sol: planner.Solution, durations: Dict[str, float]) -> float:
    queues = [collections.deque(tasksols) for tasksols in sol.workers.values()]

    done_at: Dict[str, float] = {}

    def _can_start_when(t):
        rv = 0
        for req in sol.tasks[t.task_name].requires:
            try:
                rv = max(rv, done_at[req])
            except KeyError:
                return None
        return rv

    while queues:
        heads = [(q, _can_start_when(q[0])) for q in queues]
        ready_heads = [(q, t) for q, t in heads if t is not None]
        ready_heads.sort(key=lambda qt: qt[1])

        q, start = ready_heads[0]
        t = q.popleft()
        end = start + durations[t.task_name]

        done_at[t.task_name] = end

        queues = [q for q in queues if q]

    return max(done_at.values())


def replay_with_duration_dist(
    sol: planner.Solution, durations: Dict[str, Dist], n: int
) -> List[float]:
    rv = []

    for i in range(n):
        assign = {k: d.generate() for k, d in durations.items()}
        rv.append(replay_with_durations(sol, assign))

    rv.sort()
    return rv


def _percentile(sorted_xs: List[float], pct: int) -> float:
    assert 0 <= pct <= 100

    if pct == 0:
        return sorted_xs[0]

    if pct == 100:
        return sorted_xs[-1]

    ratio = pct / 100
    n = len(sorted_xs) - 1

    index = round(n * ratio)
    return sorted_xs[index]


def attach_simulations(
    sol: planner.Solution, durations: Dict[str, Dist], n: int
) -> planner.Solution:
    results = replay_with_duration_dist(sol, durations, n)
    percentiles = {}
    for i in range(0, 101):
        percentiles[i] = _percentile(results, i)
    sol.simulation = planner.SimResults(
        simulations=n,
        percentiles=percentiles,
    )
    return sol


if __name__ == "__main__":
    from .planner import Task

    solution = planner.calculate_plan(
        [
            Task(name="cook", duration=1, workers=["me"], requires=[]),
            Task(name="eat", duration=1, workers=["me"], requires=["cook"]),
            Task(name="wash-dishes", duration=1, workers=["me"], requires=["eat"]),
        ]
    )
    rv = replay_with_durations(
        solution,
        {
            "cook": 2,
            "eat": 3,
            "wash-dishes": 4,
        },
    )
    print(rv)
    assert solution.total_duration == 3
    assert rv == (2 + 3 + 4)
