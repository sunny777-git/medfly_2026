# app/worker.py
import multiprocessing
from redis import Redis
from rq import Worker, Queue
import app.tasks.sup_upload_tasks as sup_upload_tasks  # This registers the task

if __name__ == '__main__':
    multiprocessing.set_start_method("spawn", force=True)
    redis_conn = Redis()
    queue = Queue('default', connection=redis_conn)
    worker = Worker([queue])
    worker.work()
