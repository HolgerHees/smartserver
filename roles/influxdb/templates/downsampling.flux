option task = {
  name: "{{task_name}}",
  every: {{task_every}}
}

from(bucket: "{{task_source}}")
  |> range(start: -duration(v: int(v: task.every) * 2))
  |> aggregateWindow(every: {{task_interval}}, fn: mean, createEmpty: false)
  |> to(bucket: "{{task_target}}", org: "default-org") 
