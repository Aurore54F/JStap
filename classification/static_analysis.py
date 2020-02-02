#!/usr/bin/python

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
    Syntactic analysis of JavaScript files.
"""

import os
import logging
import timeit
import pickle
from multiprocessing import Process, Queue
import queue  # For the exception queue.Empty which is not in the multiprocessing package
from scipy import sparse

import utility
import features_space


features2int_dict = None


class Analysis:
    """ To store the analysis results. """

    def __init__(self, pdg_path, label=None):
        self.pdg_path = pdg_path
        self.file_path = None
        self.features = None
        self.label = label
        self.prediction = None

    def set_file_path(self, file_path):
        self.file_path = file_path

    def set_features(self, features):
        self.features = features

    def set_prediction(self, prediction):
        self.prediction = prediction


def main_analysis(js_dirs, js_files, labels_files, labels_dirs, level, features_choice, n,
                  features2int_dict_path):
    """
        Main function, performs a static analysis (syntactic using the AST)
        of JavaScript files given in input.

        -------
        Parameters:
        - js_dirs: list of strings
            Directories containing the JS files to be analysed.
        - js_files: list of strings
            Files to be analysed.
        - labels_files: list of strings
            True label's name of the current data: either benign or malicious.
            One label for one file.
        - labels_dirs: list of strings
            True label's name of the current data: either benign or malicious.
            One label for one directory.
        - n: int
            Stands for the size of the sliding-window which goes through the units contained
            in the files to be analysed.
        - level: str
            Either 'tokens', 'ast', 'cfg', 'pdg', or 'pdg-dfg' depending on the units you want
            to extract.
        - features_choice: str
            Either 'ngrams' or 'value' depending on the features you want.
        - features2int_dict_path: str
            Path where the features dictionary is stored.

        -------
        Returns:
        -list:
            Contains the results of the static analysis of the files given as input.
            * 1st element: list containing valid files' name (i.e. files that could be parsed);
            * 2nd element: list / csr_matrix representing the analysis results (n-grams frequency)
            with one line per valid JS file;
            * 3rd element: list containing the true labels of the valid JS files.
    """

    start = timeit.default_timer()

    global features2int_dict
    features2int_dict = pickle.load(open(features2int_dict_path, 'rb'))

    if js_dirs is None and js_files is None:
        logging.error('Please, indicate a directory or a JS file to be analyzed')
        return None

    if js_files is not None:
        files2do = js_files
        if labels_files is None:
            labels_files = ['?' for _, _ in enumerate(js_files)]
        labels = labels_files
    else:
        files2do, labels = [], []
    if js_dirs is not None:
        i = 0
        if labels_dirs is None:
            labels_dirs = ['?' for _, _ in enumerate(js_dirs)]
        for cdir in js_dirs:
            for cfile in os.listdir(cdir):
                files2do.append(os.path.join(cdir, cfile))
                if labels_dirs is not None:
                    labels.append(labels_dirs[i])
            i += 1

    analyses = get_features(files2do, labels, level, features_choice, n)
    logging.debug('Got all features')
    features_repr = get_features_representation(analyses)

    utility.micro_benchmark('Elapsed time for the input analysis (without features selection):',
                            timeit.default_timer() - start)

    return features_repr


def worker_get_features_vector(my_queue, out_queue, except_queue):
    """ Worker to get the features."""

    while True:
        try:
            [analysis, level, features_choice, n] = my_queue.get(timeout=2)
            try:
                features = features_space.features_vector(analysis.pdg_path, level, features_choice,
                                                          n, features2int_dict)
                analysis.set_features(features)
                out_queue.put(analysis)  # To share modified analysis object between processes
            except Exception as e:  # Handle exception occurring in the processes spawned
                logging.error('Something went wrong with %s', analysis.pdg_path)
                print(e)
                except_queue.put([analysis.pdg_path, e])
        except queue.Empty:  # Empty queue exception
            break


def get_features(files2do, labels, level, features_choice, n):
    """
        Returns an analysis object with its features attribute filled
    """

    my_queue = Queue()
    out_queue = Queue()
    except_queue = Queue()
    workers = list()

    logging.debug('Preparing processes to get all features')

    for i, _ in enumerate(files2do):
        analysis = Analysis(pdg_path=files2do[i], label=labels[i])
        my_queue.put([analysis, level, features_choice, n])

    for i in range(utility.NUM_WORKERS):
        p = Process(target=worker_get_features_vector, args=(my_queue, out_queue, except_queue))
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


def worker_features_representation(my_queue, out_queue):
    """ Worker to represent the features in the corresponding form (list or CSR). """

    analyses = list()
    tab_res0 = list()
    tab_res2 = list()
    concat_features = None

    while True:
        try:
            analysis = my_queue.get(timeout=2)
            analyses.append(analysis)
        except queue.Empty:  # Empty queue exception
            break

    for analysis in analyses:
        features = analysis.features
        if features is not None:
            tab_res0.append(analysis.pdg_path)
            concat_features = sparse.vstack((concat_features, features), format='csr')
            if concat_features is None or concat_features.nnz == 0:
                logging.error('Something strange occurred for %s with the features ',
                              analysis.pdg_path)
                logging.error(concat_features)
            tab_res2.append(analysis.label)

    logging.debug('Merged features in subprocess')

    out_queue.put([tab_res0, tab_res2, concat_features])


def get_features_representation(analyses):
    """
        Returns the features representation used in the ML modules.
    """

    my_queue = Queue()
    out_queue = Queue()
    workers = list()

    tab_res = [[], [], []]
    concat_features = None

    logging.debug('Preparing processes to merge all features efficiently')

    for i, _ in enumerate(analyses):
        analysis = analyses[i]
        my_queue.put(analysis)

    for i in range(utility.NUM_WORKERS):
        p = Process(target=worker_features_representation, args=(my_queue, out_queue))
        p.start()
        workers.append(p)

    while True:
        try:
            # Get modified analysis objects
            [tab_res0, tab_res2, features] = out_queue.get(timeout=0.01)
            if features is not None and features.nnz > 0:
                tab_res[0].extend(tab_res0)
                tab_res[2].extend(tab_res2)
                try:
                    concat_features = sparse.vstack((concat_features, features), format='csr')
                except ValueError:
                    logging.error('Problem to merge %s with %s', concat_features, features)
            logging.debug('Merged features in main process')
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

    tab_res[1].append(concat_features)
    tab_res[1] = tab_res[1][0]

    if len(tab_res[0]) != tab_res[1].shape[0] or len(tab_res[0]) != len(tab_res[2])\
            or tab_res[1].shape[0] != len(tab_res[2]):
        logging.error('Got %s files to analyze, %s features and %s labels; do not match',
                      str(len(tab_res[0])), str(tab_res[1].shape[0]), str(len(tab_res[2])))
    logging.debug('Finished to merge features, will move to ML stuff :)')

    return tab_res
