"""The operating state of the container: file verdicts, ACL prefilter, versions.

The package is deliberately thin. ``repo`` holds every SQL statement in the
project and ``schema.sql`` holds the tables it works on, so a reviewer who wants
to know what the container persists has exactly two files to read.
"""
