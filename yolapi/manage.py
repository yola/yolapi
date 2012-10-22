#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yolapi.settings")

    # We'd prefer the world to start one level up
    app_dir = os.path.abspath(os.path.dirname(__file__))
    st_first = os.stat(sys.path[0])
    st_app = os.stat(app_dir)
    assert ((st_first.st_dev, st_first.st_ino)
            == (st_app.st_dev, st_app.st_ino))

    base_dir = os.path.dirname(app_dir)
    sys.path[0] = base_dir

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
