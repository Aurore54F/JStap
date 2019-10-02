# Copyright (C) 2019 Aurore Fass
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
    Utility file, stores shared information.
"""

import sys
import timeit
import logging
import signal


sys.setrecursionlimit(400000)

NUM_WORKERS = 2


class UpperThresholdFilter(logging.Filter):
    """
    This allows us to set an upper threshold for the log levels since the setLevel method only
    sets a lower one
    """

    def __init__(self, threshold, *args, **kwargs):
        self._threshold = threshold
        super(UpperThresholdFilter, self).__init__(*args, **kwargs)

    def filter(self, rec):
        return rec.levelno <= self._threshold


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.ERROR)
LOGGER = logging.getLogger()
LOGGER.addFilter(UpperThresholdFilter(logging.CRITICAL))


def micro_benchmark(message, elapsed_time):
    """ Micro benchmarks. """
    logging.info('%s %s%s', message, str(elapsed_time), 's')
    return timeit.default_timer()


def get_ram_usage(ram):
    """ RAM usage. """
    logging.info('%s %s%s', 'Current RAM usage:', str(ram / 1024 / 1024 / 1024), 'GB')


class Timeout:
    """ Timeout class using ALARM signal. """

    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)  # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()
