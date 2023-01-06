- add monitoring of task progress in manager script - manager should be informed which frames are already rendered and which are not
- add monitoring of instances interruptions in manager
  - If instance interruption is detected, manager should add task to queue again (excluding part of task which was completed)
  - probably second SQS queue will be needed for that
- in worker script, blender CLI should be run in separate thread and main thread should periodically check whether the instance is interrupted (currently it is done after rendering frame, but frames take more than 2 minutes to render, so some interruptions might go undetected)
- add collecting of statistics - overall time, average time for frame to render, interruption count
- prepare test cases (`.blend` file and indices of frames to render) and run them on following configurations (remember about checking and comparing the cost):
  - 3 On-Demand instances
  - 3 Spot instances
  - 10 On-Demand instances
  - 10 Spot instances