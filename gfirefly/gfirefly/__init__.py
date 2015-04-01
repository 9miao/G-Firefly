VERSION = (0, 1, 9, 'alpha', 0)

def get_version(*args, **kwargs):
    # Only import if it's actually called.
    from gfirefly.utils.version import get_version
    return get_version(*args, **kwargs)
