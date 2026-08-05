from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory storage (slowapi/limits default) — fine for this single-instance
# deployment; swap to a Redis storage_uri here if the app ever runs behind
# multiple backend replicas, since counts wouldn't be shared otherwise.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
