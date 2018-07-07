"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import uos as os
import sys


class Exclog():
    """REST API handler"""

    async def get(self, data):
        """Get contents of exception log"""
        try:
            with open('exclog', mode='r') as f:
                for line in f:
                    yield line
                yield '\n'
        except Exception as e:
            yield 'Nothing\n'

    def delete(self, data):
        """Delete exclog file"""
        os.unlink('exclog')
        return "Deleted\n"


def log_exception(e):
    """Simply log exception into file"""
    sys.print_exception(e)
    with open('exclog', mode='a') as f:
        sys.print_exception(e, f)
        f.write('\n')
