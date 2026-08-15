"""Command line tools that belong to the backend but not to the running app.

Nothing in here is imported by :mod:`findling.main`. These modules exist for CI
gates and for hands on diagnosis, which is why they are allowed to print and to
set an exit code while the application code is not.
"""
