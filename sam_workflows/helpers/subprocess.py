import subprocess
from typing import List

class ProcessError(Exception):
    """Implements error to raise when a process fails."""

class TimeoutError(Exception):
    """Implements error to raise when a process call times out."""

def run_command(cmd: List, timeout: int = 10):
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
        err_msg = (
            f"Conversion of file"
            f"timed out after {error.timeout} seconds."
        )
        raise TimeoutError(err_msg)
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


    try:
        run_proc(proc, timeout=120)
    except ProcessError as error:
        proc.kill()
        raise ProcessError(
            f"Conversion of {input_file} failed with error: {error}"
        )
    except TimeoutExpired as error:
        proc.kill()
        _, _ = proc.communicate()
        err_msg = (
            f"Conversion of {input_file} "
            f"timed out after {error.timeout} seconds."
        )
        raise LibreError(err_msg, timeout=True)

def run_proc(proc: Popen, timeout: int) -> None:
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
    try:
        # Communicate with process, collect stderr
        _, errs = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Process timed out. Kill and re-raise.
        proc.kill()
        raise
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
