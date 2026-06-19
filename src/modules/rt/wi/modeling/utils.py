import re
from src.modules.rt.wi.modeling.errors import FormatError

def look_next_line(infile):
    """
    Read the next line from a file without advancing the file cursor.

    This function temporarily reads one line from the current file position and
    then restores the cursor to its original position. It is useful for checking
    the next line before deciding which parser should consume it.

    Args:
        infile: Open input file object.

    Returns:
        The next line in the file as a string, without consuming it.
    """
    now = infile.tell()
    line = infile.readline()
    infile.seek(now)
    return line

def match_or_error(exp, infile):
    """
    Read one line from a file and match it against a regular expression.

    This function consumes the next line from the input file and checks whether
    it matches the provided regular expression. If the line matches, the match
    object is returned. Otherwise, a ``FormatError`` is raised with information
    about the expected pattern and the actual line found.

    Args:
        exp: Regular expression pattern expected for the next line.
        infile: Open input file object positioned at the line to be matched.

    Returns:
        A regular expression match object.

    Raises:
        FormatError: If the consumed line does not match the expected pattern.
    """
    line = infile.readline()
    match = re.match(exp, line)
    if match:
        return match
    else:
        raise FormatError(
            'Expected "{}", found "{}"'.format(exp, line))