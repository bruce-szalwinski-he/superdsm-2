import repype.textual.app

import superdsm.task

app = repype.textual.app.Repype(task_cls=superdsm.task.Task)
app.run()
