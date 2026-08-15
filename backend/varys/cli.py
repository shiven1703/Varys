"""Controlled maintenance commands."""

from __future__ import annotations

import argparse
import getpass

from sqlalchemy.exc import IntegrityError

from varys.auth import create_user
from varys.config import load_settings
from varys.db import create_session_factory


def main() -> int:
    parser = argparse.ArgumentParser(prog="varys")
    commands = parser.add_subparsers(dest="command", required=True)
    create_admin = commands.add_parser("create-admin")
    create_admin.add_argument("--username", required=True)
    arguments = parser.parse_args()

    if arguments.command != "create-admin":
        return 2
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        parser.error("passwords do not match")
    settings = load_settings()
    if settings.database_url is None:
        parser.error("VARYS_DATABASE_URL is required")
    factory = create_session_factory(settings.database_url)
    with factory.begin() as database:
        try:
            create_user(database, arguments.username, password)
        except (IntegrityError, ValueError) as error:
            parser.error(str(error))
    return 0
