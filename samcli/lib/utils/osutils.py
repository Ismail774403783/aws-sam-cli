"""
Common OS utilities
"""

import sys
import os
import shutil
import tempfile
import logging
import contextlib

from contextlib import contextmanager


LOG = logging.getLogger(__name__)


@contextmanager
def mkdir_temp(mode=0o755):
    """
    Context manager that makes a temporary directory and yields it name. Directory is deleted
    after the context exits

    Parameters
    ----------
    mode : octal
        Permissions to apply to the directory. Defaults to '755' because don't want directories world writable

    Returns
    -------
    str
        Path to the directory

    """

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, mode)

        yield temp_dir

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir)


def stdout():
    """
    Returns the stdout as a byte stream in a Py2/PY3 compatible manner

    Returns
    -------
    io.BytesIO
        Byte stream of Stdout
    """
    return sys.stdout.buffer


def stderr():
    """
    Returns the stderr as a byte stream in a Py2/PY3 compatible manner

    Returns
    -------
    io.BytesIO
        Byte stream of stderr
    """
    return sys.stderr.buffer


def remove(path):
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


@contextlib.contextmanager
def tempfile_platform_independent():
    # NOTE(TheSriram): Setting delete=False is specific to windows.
    # https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
    _tempfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        yield _tempfile
    finally:
        _tempfile.close()
        remove(_tempfile.name)


# NOTE: Py3.8 or higher has a ``dir_exist_ok=True`` parameter to provide this functionality.
#       This method can be removed if we stop supporting Py37
def copytree(source, destination, ignore=None):
    """
    Similar to shutil.copytree except that it removes the limitation that the destination directory should
    be present.
    :type source: str
    :param source:
        Path to the source folder to copy
    :type destination: str
    :param destination:
        Path to destination folder
    :type ignore: function
    :param ignore:
        A function that returns a set of file names to ignore, given a list of available file names. Similar to the
        ``ignore`` property of ``shutils.copytree`` method
    """

    if not os.path.exists(destination):
        os.makedirs(destination)

        try:
            # Let's try to copy the directory metadata from source to destination
            shutil.copystat(source, destination)
        except OSError as ex:
            # Can't copy file access times in Windows
            LOG.debug("Unable to copy file access times from %s to %s", source, destination, exc_info=ex)

    names = os.listdir(source)
    if ignore is not None:
        ignored_names = ignore(source, names)
    else:
        ignored_names = set()

    for name in names:
        # Skip ignored names
        if name in ignored_names:
            continue

        new_source = os.path.join(source, name)
        new_destination = os.path.join(destination, name)

        if os.path.isdir(new_source):
            copytree(new_source, new_destination, ignore=ignore)
        else:
            shutil.copy2(new_source, new_destination)
