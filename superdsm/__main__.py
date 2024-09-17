import sys

import repype.cli

import superdsm.task

if __name__ == '__main__':
    if repype.cli.run_cli(superdsm.task.Task):
        sys.exit(0)
    else:
        sys.exit(1)
