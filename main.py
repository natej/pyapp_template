import os
import sys
import types
import argparse
import configparser
import pathlib
import smtplib
import email
import socket
import traceback
import logging
import logging.handlers

__version__ = "0.1.0"

APP_VERSION = __version__
APP_NAME = "myappname"
APP_DESCRIPTION = "My app description."
APP_HELP_EPILOG = """
If the app run is successful, a zero exit status is returned. If there's an
error, a non-zero exit status is returned. Log messages are written to
stderr and the log file specified in the config file.
"""

log = logging.getLogger()


def do_work(app):
    # Start adding your application code here.
    id(app)


def run(app):
    """Return status int for sys.exit()."""
    log.info(f"{app.name} version {app.version}")
    log_args = ["config"]
    for arg_name in log_args:
        log.info(f"{arg_name}: {getattr(app.args, arg_name)}")
    do_work(app)
    return 0


def get_hostname():
    return socket.getfqdn()


def send_email(app, message):
    try:
        enabled = asbool(app.config.get("email_exceptions", "enabled").strip())
        if not enabled:
            return
        server_host = app.config.get("email_exceptions", "server_host").strip()
        server_port = int(app.config.get("email_exceptions", "server_port").strip())
        from_ = app.config.get("email_exceptions", "from").strip()
        to = app.config.get("email_exceptions", "to").strip()
        subject = app.config.get("email_exceptions", "subject").strip()
        hostname = get_hostname()
        content = f"This is a message from the application {app.name} on host {hostname}:\n\n{message}"

        # Create a text/plain message
        email_msg = email.message.EmailMessage()
        email_msg.set_content(content)
        email_msg["Subject"] = subject
        email_msg["From"] = from_
        email_msg["To"] = to
        s = smtplib.SMTP(server_host, server_port)
        s.send_message(email_msg)
        s.quit()
    except:
        log.error(f"error sending app exception email:\n{traceback.format_exc()}")


def asbool(obj):
    """(c) 2005 Ian Bicking and contributors; written for Paste (https://pythonpaste.org)
    Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php"""
    if isinstance(obj, str):
        obj = obj.strip().lower()
        if obj in ["true", "yes", "on", "y", "t", "1"]:
            return True
        elif obj in ["false", "no", "off", "n", "f", "0"]:
            return False
        else:
            raise ValueError("String is not true/false: %r." % obj)
    return bool(obj)


def get_size_bytes(size_str, default_unit="m"):
    """Return int from size string with possible suffixes k, m, g."""
    suffixes = {
        "k": 1024,
        "m": 1024 * 1024,
        "g": 1024 * 1024 * 1024,
    }
    s = size_str.strip()
    if not s:
        raise ValueError("Size string is empty.")
    unit = s[-1]
    if unit.isdecimal():
        unit = default_unit
    else:
        s = s[:-1]
    unit = unit.lower()
    if unit not in suffixes:
        raise ValueError(f'Invalid size suffix "{unit}".')
    size = int(s)
    size *= suffixes[unit]
    return size


def setup_log(app):
    log_dir = pathlib.Path(app.config.get("log", "dir")).expanduser()
    log_filename = app.config.get("log", "filename")
    log_max_size = get_size_bytes(app.config.get("log", "max_size"))
    log_backup_count = app.config.getint("log", "backup_count")
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    sh = logging.StreamHandler(stream=sys.stderr)
    fh = logging.handlers.RotatingFileHandler(log_dir / log_filename,
                                              encoding="utf-8",
                                              maxBytes=log_max_size,
                                              backupCount=log_backup_count)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    debug = asbool(app.config.get("log", "debug"))
    level = logging.DEBUG if debug else logging.INFO
    for handler in (sh, fh):
        handler.setFormatter(formatter)
        handler.setLevel(level)
        log.addHandler(handler)
    log.setLevel(level)


def parse_config(fname):
    """Return ConfigParser object."""
    # Make sure we can read the file so we get an error now, since ConfigParser.read() doesn't.
    with open(fname, "r") as f:
        f.read()
    here = os.path.dirname(os.path.abspath(fname))
    defaults = dict(here=here)
    config = configparser.ConfigParser(defaults)
    config.read(fname)
    return config


def parse_command_line(argv):
    """Return argparse args."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=APP_DESCRIPTION,
                                     epilog=APP_HELP_EPILOG,
                                     add_help=True)
    # Add additional CLI app arguments below, for example:
    # parser.add_argument("my_input_arg", help="My input argument help message.")
    parser.add_argument("-c", "--config", action="store", default="config.ini",
                        help="config filename (default: %(default)s in current dir)")
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s {version}".format(version=APP_VERSION))

    # On error, argparse.parse_args() prints a message to stderr and exits with status 2.
    args = parser.parse_args(argv[1:])

    return args


def main(argv=None):
    """Return status int for sys.exit()."""
    if argv is None:
        argv = sys.argv
    app = None
    try:
        args = parse_command_line(argv)
        config = parse_config(args.config)
        app = types.SimpleNamespace(name=APP_NAME, version=APP_VERSION, description=APP_DESCRIPTION,
                                    args=args, config=config)
        setup_log(app)
        exit_status = run(app)
    except Exception as e:
        formatted_traceback = traceback.format_exc()
        log.error(f"exception occurred: {e}:\n{formatted_traceback}")
        if app is not None:
            send_email(app, f"An application exception occurred: {e}\n\n{formatted_traceback}")
        return 1
    else:
        log.info("exiting")
        return exit_status


if __name__ == "__main__":
    sys.exit(main())
