import subprocess
from subprocess import CalledProcessError
from typing import List


class ProcessError(Exception):
    """Implements error to raise when a process fails."""


class TimeoutError(Exception):
    """Implements error to raise when a process call times out."""


def run(cmd: List, timeout: int = 10) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
    except CalledProcessError as error:
        raise ProcessError(
            f"Process failed with error: {error.stderr.strip().decode()}"
        )


def run_command(cmd: List, timeout: int = 10) -> None:
    """Runs a Popen process with a given timeout. Kills the process and raises
    TimeoutExpired if the process does not finish within timeout in seconds. If
    there are messages in stderr, these are collected and a ProcessError is
    raised.

    Parameters
    ----------
    cmd : List
        The cmd to execute.
    timeout : int
        Number of seconds before timeput.

    Raises
    ------
    TimeoutError
        If communication with the process fails to terminate within timeout
        seconds, the process is killed and TimeoutExpired is raised.
    ProcessError
        If the process terminates within timeout seconds, but has messages in
        stderr and/or exit code != 0, a ProcessError is raised.
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    try:
        # Communicate with process, collect stderr
        _, errs = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        # Process timed out. Kill and re-raise.
        proc.kill()
        _, _ = proc.communicate()
        raise TimeoutError(f"Command timed out after {error.timeout} seconds.")
    else:
        exit_code: int = proc.returncode
        err_msg: str = ""

        # Check stderr/exit code from process call.
        if errs:
            err_msg = errs.strip().decode()
        elif exit_code != 0:
            # Fail with nothing in stderr :(
            err_msg = f"Exited with code {exit_code} and empty stderr"

        if err_msg:
            raise ProcessError(err_msg)
