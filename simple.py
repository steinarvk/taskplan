from dataclasses import dataclass
from typing import List

from ortools.sat.python import cp_model

@dataclass
class Job:
    name: str
    duration: int
    workers: List[str]
    requires: List[str]

jobs = [
    Job("install_windows", duration=4, workers=["bob"], requires=[]),
    Job("install_linux", duration=4, workers=["alice"], requires=[]),
    Job("clean_windows", duration=1, workers=["alice"], requires=["install_windows"]),
    Job("install_curtains", duration=4, workers=["alice", "bob"], requires=["install_windows"]),
    Job("install_docker", duration=4, workers=["alice", "carol"], requires=["install_linux"]),
    Job("write_application", duration=16, workers=["alice", "carol"], requires=["install_linux"]),
    Job("run_app", duration=4, workers=["alice", "carol"], requires=["write_application", "install_docker"]),
]

for i in range(4):
    jobs.append(Job(f"catch_penguin_{i}", duration=3, workers=["alice", "bob", "carol"], requires=["install_linux", "install_windows"]))

workers = list(sorted(set([w for job in jobs for w in job.workers])))

jobs_by_name = {job.name: i for i, job in enumerate(jobs)}
workers_by_name = {w: i for i, w in enumerate(workers)}
total_duration = sum(job.duration for job in jobs)


model = cp_model.CpModel()

job_assignment_vars = []
job_start_vars = []
job_end_vars = []

for job in jobs:
    prefix = f"task_{job.name}_"

    assignment_var = model.NewIntVar(0, len(workers)-1, prefix + "assignment")
    model.AddAllowedAssignments([assignment_var], [(workers_by_name[k],) for k in job.workers])
    print("allowed assignments for", job.name, [(workers_by_name[k],) for k in job.workers])
    job_assignment_vars.append(assignment_var)

    job_start_var = model.NewIntVar(0, total_duration, prefix + "start")
    job_end_var = model.NewIntVar(0, total_duration, prefix + "end")
    job_interval_var = model.NewIntervalVar(job_start_var, job.duration, job_end_var, prefix + "interval")

    job_start_vars.append(job_start_var)
    job_end_vars.append(job_end_var)

    for req in job.requires:
        reqjob_index = jobs_by_name[req]
        required_job_end_var = job_end_vars[reqjob_index]  # should be toposorted
        model.Add(job_start_var >= required_job_end_var)

worker_is_assigned_vars = []
for i, worker in enumerate(workers):
    worker_job_interval_vars = []

    for j, job in enumerate(jobs):
        prefix = f"worker_{worker}_job_{job.name}_"

        job_is_assigned_var = model.NewBoolVar(prefix + "is_assigned")
        model.Add(job_assignment_vars[j] == i).OnlyEnforceIf(job_is_assigned_var)
        model.Add(job_assignment_vars[j] != i).OnlyEnforceIf(job_is_assigned_var.Not())
        worker_is_assigned_vars.append(job_is_assigned_var)

        job_duration = model.NewIntVar(0, job.duration, prefix + "duration")
        model.Add(job_duration == job.duration).OnlyEnforceIf(job_is_assigned_var)
        model.Add(job_duration == 0).OnlyEnforceIf(job_is_assigned_var.Not())

        job_start = model.NewIntVar(0, total_duration, prefix + "start")
        job_end = model.NewIntVar(0, total_duration, prefix + "end")
        job_intv = model.NewIntervalVar(job_start, job_duration, job_end, prefix + "interval")

        model.Add(job_start == job_start_vars[j]).OnlyEnforceIf(job_is_assigned_var)
        model.Add(job_end == job_end_vars[j]).OnlyEnforceIf(job_is_assigned_var)

        worker_job_interval_vars.append(job_intv)

    model.AddNoOverlap(worker_job_interval_vars)

total_time = model.NewIntVar(0, total_duration, "_total_makespan")
model.AddMaxEquality(total_time, job_end_vars)
model.Minimize(total_time)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 5.0

status = solver.Solve(model)
named = {
    cp_model.OPTIMAL: "optimal",
    cp_model.FEASIBLE: "feasible",
    cp_model.INFEASIBLE: "infeasible",
}

print(status, named.get(status))
print(solver.Value(total_time))

for j, ass_task_var in enumerate(job_assignment_vars):
    assigned_worker_index = solver.Value(ass_task_var)
    assigned_worker = workers[assigned_worker_index]
    print(jobs[j].name, assigned_worker)
    print("  worker#:", assigned_worker_index)
    print("  worker:", assigned_worker)
    print("  start:", solver.Value(job_start_vars[j]))
    print("  end:", solver.Value(job_end_vars[j]))
