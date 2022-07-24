import sys

from server.compute.utils import get_q

if __name__ == "__main__":
    worker_type = str(sys.argv[1])
    if worker_type == "batch":
        worker_name = "nm_batch_worker"
        job_name = "nm_batch_task"
    else:
        worker_name = "nm_realtime_worker"
        job_name = "nm_realtime_task"

    # following the way of stackoverflow threads
    # https://stackoverflow.com/questions/55244729/python-rq-how-to-pass-information-from-the-caller-to-the-worker
    q = get_q(worker_name)
    nm_job = q.fetch_job(job_name)
    nm_job.connection.set(nm_job.key + b":should_stop", 1, ex=30)
