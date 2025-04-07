PyApp Template
==============

Summary
-------

This is a Python application template intended to help you start
developing your application quickly. It can provide an initial
starting point and structure for your application.

It includes:
- Command-line arguments via argparse.
- A config.ini file via ConfigParser.
- App exceptions can be emailed. See config.ini. Currently, SMTP auth is not supported.

Quick Start
-----------

1) Add any needed CLI args to `parse_command_line()`.

2) See the function `run()`. Add any CLI args you want logged to the `log_args` list.

3) See the function `do_work()`. Start adding your application code here.
