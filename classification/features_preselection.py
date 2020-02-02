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
    Preselection of features for malicious JS detection: ALL features appearing in a corpus.
"""

import os
import pickle
import logging
import timeit
from multiprocessing import Process, Queue
import queue  # For the exception queue.Empty which is not in the multiprocessing package

import features_space
import static_analysis
import utility


SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def handle_features_1file(unique_features_dict, all_features_dict):
    """ Fills a dict with the encountered features + the number of files they have been seen in.
    Case one file. """

    for feature in unique_features_dict:
        if feature not in all_features_dict:
            all_features_dict[feature] = 1
        else:
            all_features_dict[feature] += 1


def handle_features_1dir(samples_dir, label, level, features_choice, n, analysis_path):
    """ handle_features_1file for ALL files from a directory.
    Case one folder. """

    if not os.path.exists(analysis_path):
        os.makedirs(analysis_path)

    pickle_path = os.path.join(analysis_path, features_choice, level + '_all_features_' + label)
    utility.check_folder_exists(pickle_path)

    if os.path.isfile(pickle_path):
        all_features_dict = pickle.load(open(pickle_path, 'rb'))
    else:
        all_features_dict = dict()

    analyses = get_features_all_files_multiproc(samples_dir, level, features_choice, n)

    for analysis in analyses:
        features_dict = analysis.features
        if features_dict is not None:
            try:
                handle_features_1file(features_dict, all_features_dict)
            except:
                logging.exception('Something went wrong with %s', analysis.file_path)

    pickle.dump(all_features_dict, open(pickle_path, 'wb'))


def handle_features_all(js_dirs, labels, level, features_choice, analysis_path, n=4):
    """ handle_features_1dir for a list of directories; TO CALL. """

    if level in ('ast', 'cfg', 'pdg-dfg', 'pdg', 'tokens'):
        for i, _ in enumerate(js_dirs):
            logging.debug('Currently handling %s', js_dirs[i])
            handle_features_1dir(js_dirs[i], labels[i], level, features_choice, n, analysis_path)

    else:
        logging.error('Expected \'tokens\' or \'ast\' or \'cfg\' or \'pdg-dfg\' or \'pdg\', '
                      'got %s instead', level)


def worker_get_features(my_queue, out_queue, except_queue):
    """ Worker to get the features."""

    while True:
        try:
            [analysis, level, features_choice, n] = my_queue.get(timeout=2)
            try:
                features, _, _ = features_space.get_features(analysis.pdg_path,
                                                             level, features_choice, n)
                analysis.set_features(features)
                out_queue.put(analysis)  # To share modified analysis object between processes
            except Exception as e:  # Handle exception occurring in the processes spawned
                logging.error('Something went wrong with %s', analysis.pdg_path)
                print(e)
                except_queue.put([analysis.pdg_path, e])
        except queue.Empty:  # Empty queue exception
            break


def get_features_all_files_multiproc(samples_dir, level, features_choice, n):
    """
        Gets the features of all files from samples_dir.
    """

    my_queue = Queue()
    out_queue = Queue()
    except_queue = Queue()
    workers = list()

    for sample in os.listdir(samples_dir):
        sample_path = os.path.join(samples_dir, sample)
        analysis = static_analysis.Analysis(pdg_path=sample_path)
        my_queue.put([analysis, level, features_choice, n])

    for _ in range(utility.NUM_WORKERS):
        p = Process(target=worker_get_features, args=(my_queue, out_queue, except_queue))
        p.start()
        workers.append(p)

    analyses = list()

    while True:
        try:
            analysis = out_queue.get(timeout=0.01)
            analyses.append(analysis)
        except queue.Empty:
            pass
        all_exited = True
        for w in workers:  # Instead of join, as the worker cannot be joined when elements
            # are still in except_queue or out_queue, so it deadlocks. But they must be
            # joined before the elements are taken out of the queue
            if w.exitcode is None:
                all_exited = False
                break
        if all_exited & out_queue.empty():
            break

    return analyses


def get_top_dict_entries(top, my_dict):
    """ Gets the first top entries from a dict. """
    my_dict2 = dict()
    i = 0
    for k in my_dict.keys():
        if i < top:
            i += 1
            my_dict2[k] = my_dict[k]
    return my_dict2


def get_most_used_features(all_features_dict, top):
    """ Gets the first top entries from a dict sorted by values. """
    sorted_d = dict(sorted(all_features_dict.items(), key=lambda kv: kv[1], reverse=True))
    return get_top_dict_entries(top, sorted_d)


def get_least_used_features(all_features_dict, top):
    """ Gets the last top entries from a dict sorted by values. """
    sorted_d = dict(sorted(all_features_dict.items(), key=lambda kv: kv[1], reverse=False))
    return get_top_dict_entries(top, sorted_d)
