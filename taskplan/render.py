import json

from .planner import Solution

from typing import TextIO, List, Tuple


def print_console_solution(solution: Solution, fp: TextIO):
    print("optimal?", solution.optimal, file=fp)
    print("total duration:", solution.total_duration, file=fp)
    print("metadata:", solution.meta, file=fp)
    for name, tasks in solution.workers.items():
        print(name, file=fp)
        for task in tasks:
            print("  ", task, file=fp)


def render_charts_table(solution: Solution) -> List[Tuple[str, str, int, int]]:
    return [
        (
            task.worker_name,
            task.task_name,
            task.start * 1000,
            task.end * 1000,
        )
        for task in solution.tasks.values()
    ]


def render_charts_html(solution: Solution) -> str:
    table = render_charts_table(solution)
    return """
<html>
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {'packages':['timeline']});
      google.charts.setOnLoadCallback(drawChart);
      function drawChart() {
        var container = document.getElementById('timeline');
        var chart = new google.visualization.Timeline(container);
        var dataTable = new google.visualization.DataTable();

        dataTable.addColumn({ type: 'string', id: 'Worker' });
        dataTable.addColumn({ type: 'string', id: 'Task' });
        dataTable.addColumn({ type: 'number', id: 'Start' });
        dataTable.addColumn({ type: 'number', id: 'End' });
        dataTable.addRows(REPLACETHIS);

        chart.draw(dataTable);
      }
    </script>
  </head>
  <body>
    <div id="timeline" style="width: 100%; height: 100%;"></div>
  </body>
</html>
""".replace(
        "REPLACETHIS", json.dumps(table)
    )
