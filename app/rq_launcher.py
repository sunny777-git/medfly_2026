# app/rq_launcher.py
import multiprocessing as mp
mp.set_start_method("forkserver", force=True)  # required for some platforms

import app.worker as worker  # This uses forkserver safely and runs the worker
