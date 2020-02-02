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

import os
import timeit
import logging


NUM_WORKERS = 2
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


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


LOGGER = logging.getLogger()
LOGGER.addFilter(UpperThresholdFilter(logging.CRITICAL))


def micro_benchmark(message, elapsed_time):
    """ Micro benchmarks. """
    logging.info('%s %s%s', message, str(elapsed_time), 's')
    return timeit.default_timer()


def check_folder_exists(folder_path):
    """ Checks if folder exists, otherwise create it. """

    if not os.path.isdir(folder_path):
        folder_path = os.path.dirname(folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def get_files2handle(list_files_path, label):
    """ Gets the files to handle, along with their label. """

    with open(list_files_path) as f:
        files2do = f.readlines()
    files2do = [file_path.replace('\n', '') for file_path in files2do]
    return files2do, [label]*len(files2do)


def parsing_commands(parser):
    """
        Filling of an ArgumentParser object to later parse the command line into Python data types.

        -------
        Parameter:
        - parser: ArgumentParser
            Parser to fill.

        -------
        Returns:
        - ArgumentParser
            Parser filled.
    """

    parser.add_argument('--analysis_path', metavar='DIR', type=str, nargs=1,
                        default=[os.path.join(SRC_PATH, 'Analysis')],
                        help='folder to store the features\' analysis results in')
    parser.add_argument('--n', metavar='INTEGER', type=int, nargs=1, default=[4],
                        help='stands for the size of the sliding-window which goes through the '
                             'units contained in the files to be analyzed')
    parser.add_argument('--v', metavar='VERBOSITY', type=int, nargs=1, choices=[0, 1, 2, 3, 4, 5],
                        default=[2], help='controls the verbosity of the output, from 0 (verbose) '
                                          'to 5 (less verbose)')
    parser.add_argument('--level', metavar='LEVEL', type=str, nargs=1,
                        choices=['tokens', 'ast', 'cfg', 'pdg-dfg', 'pdg'],
                        help='stands for the level of the analysis (tokens, ast, cfg, pdg-dfg, pdg')
    parser.add_argument('--features', metavar='FEATURES_CHOICE', type=str, nargs=1,
                        choices=['ngrams', 'value'],
                        help='features\'s choice (ngrams, value)')

    return parser


def control_logger(logging_level):
    """
        Builds a logger object.

        -------
        Parameter:
        - logging_level: int
            Verbosity of the logging. Between 0 and 5.
    """

    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.getLevelName(logging_level * 10))


def check_params(level, features_choice):
    """ Generic parameters checks before running. """

    if level is None:
        logging.error('Please, indicate the level of the analysis (--level option, '
                      'either tokens, ast, cfg, pdg-dfg or pdg)')

    elif features_choice is None:
        logging.error('Please, indicate your features\' choice (--features option, '
                      'either ngrams, value)')

    else:
        return 1
    return 0
