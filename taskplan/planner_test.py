from .planner import *


def test_planning():
    example_tasks = [
        Task(name="install_linux", duration=4, workers=["alice"], requires=[]),
        Task(
            name="clean_windows",
            duration=1,
            workers=["alice"],
            requires=["install_windows"],
        ),
        Task(name="install_windows", duration=4, workers=["bob"], requires=[]),
        Task(
            name="install_curtains",
            duration=4,
            workers=["alice", "bob"],
            requires=["install_windows"],
        ),
        Task(
            name="install_docker",
            duration=4,
            workers=["alice", "carol"],
            requires=["install_linux"],
        ),
        Task(
            name="write_application",
            duration=16,
            workers=["alice", "carol"],
            requires=["install_linux"],
        ),
        Task(
            name="run_app",
            duration=4,
            workers=["alice", "carol"],
            requires=["write_application", "install_docker"],
        ),
        Task(name="test_app", duration=4, workers=["david"], requires=["run_app"]),
        Task(
            name="fix_app",
            duration=10,
            workers=["alice", "carol"],
            requires=["test_app"],
        ),
    ]

    workers = ("alice", "bob", "carol", "david")

    solution = calculate_plan(
        example_tasks,
        params=SolverParams(
            time_seconds=1,
        ),
    )

    for task in example_tasks:
        tasksol = solution.tasks[task.name]
        assert tasksol.worker_name in task.workers
        assert tasksol.end == (tasksol.start + task.duration)

        assert task.name in [t.task_name for t in solution.workers[tasksol.worker_name]]

        for other_worker in workers:
            if other_worker == tasksol.worker_name:
                continue
            assert task.name not in [
                t.task_name for t in solution.workers[other_worker]
            ]

        for req in task.requires:
            assert tasksol.start >= solution.tasks[req].end

    for worker in workers:
        tasksols = solution.workers[worker]
        for i, tasksol in enumerate(tasksols):
            if i > 0:
                assert tasksol.start >= tasksols[i - 1].end
