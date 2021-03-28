from .planner import *
from .render import *

if __name__ == "__main__":
    import sys

    example_tasks = [
        Task("install_linux", duration=4, workers=["alice"], requires=[]),
        Task(
            "clean_windows", duration=1, workers=["alice"], requires=["install_windows"]
        ),
        Task("install_windows", duration=4, workers=["bob"], requires=[]),
        Task(
            "install_curtains",
            duration=4,
            workers=["alice", "bob"],
            requires=["install_windows"],
        ),
        Task(
            "install_docker",
            duration=4,
            workers=["alice", "carol"],
            requires=["install_linux"],
        ),
        Task(
            "write_application",
            duration=16,
            workers=["alice", "carol"],
            requires=["install_linux"],
        ),
        Task(
            "run_app",
            duration=4,
            workers=["alice", "carol"],
            requires=["write_application", "install_docker"],
        ),
        Task("test_app", duration=4, workers=["david"], requires=["run_app"]),
        Task("fix_app", duration=10, workers=["alice", "carol"], requires=["test_app"]),
    ]

    n = 5
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    for i in range(n):
        example_tasks.append(
            Task(
                f"catch_penguin_{i}",
                duration=3,
                workers=["alice", "bob", "david", "carol"],
                requires=[f"catch_penguin_{i-2}"]
                if i > 200
                else ["install_linux", "install_windows"],
            )
        )

    solution = calculate_plan(
        example_tasks,
        params=SolverParams(
            time_seconds=60,
        ),
    )

    print_console_solution(solution, sys.stderr)
    print(render_charts_html(solution))
