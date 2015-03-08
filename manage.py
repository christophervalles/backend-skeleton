#!/usr/bin/env python
"""
CLI to manage app.
"""
import os

from flask.ext.script import Manager

from src import settings, models, __version__
from src.wsgi import app
from src.cli import database

manager = Manager(app)
manager.add_command("database", database.manager)


@manager.command
def version():
    """Displays version."""
    print __version__


@manager.command
def runworkers():
    """Start workers (deprecated)."""
    os.system("celery worker --app=app.worker --beat -Qqueries,celery,scheduled_queries")


@manager.shell
def make_shell_context():
    from src.models import db
    return dict(app=app, db=db, models=models)


@manager.command
def check_settings():
    """Show the settings as the app sees them (useful for debugging)."""
    from types import ModuleType

    for name in dir(settings):
        item = getattr(settings, name)
        if not callable(item) and not name.startswith("__") and not isinstance(item, ModuleType):
            print "{} = {}".format(name, item)


if __name__ == '__main__':
    manager.run()
