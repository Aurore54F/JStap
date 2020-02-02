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
    Selection of features for malicious JS detection: feature dependent on the label.
"""

import os
import pickle
import logging
import timeit
from multiprocessing import Process, Queue
import queue  # For the exception queue.Empty which is not in the multiprocessing package
from scipy.stats import chi2_contingency, chi2

import features_preselection
import static_analysis
import utility


SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_popular_features(all_features_dict):
    """ Gets the features used more than one time. """
    popular_features = dict()
    for k, v in all_features_dict.items():
        if v > 10:  # Tested with chi2, to ensure that feature and classification are dependent
            popular_features[k] = v
    return popular_features


def initialize_analyzed_features_dict(all_features_dict1, all_features_dict2):
    """ Create the analyzed_features_dict with all expected features (from all_features_dict_path)
    as key and [0, 0, 0, 0] as value. """

    # all_features_dict = pickle.load(open(all_features_dict_path, 'rb'))
    analyzed_features_dict = dict()
    popular_features1 = get_popular_features(all_features_dict1)
    popular_features2 = get_popular_features(all_features_dict2)

    for feature in popular_features1:
        analyzed_features_dict[feature] = [0]*4
    for feature in popular_features2:
        if feature not in analyzed_features_dict:
            analyzed_features_dict[feature] = [0]*4
    return analyzed_features_dict


def analyze_features(analyzed_features_dict, features_sample, label):
    """
        Features' analysis before selection process. We count the number of times a given feature:
            * appear in a benign sample;
            * don't appear in a benign sample;
            * appear in a malicious sample;
            * don't appear in a malicious sample.
        We do that by analyzing the features per sample.

        -------
        Parameters:
        - analyzed_features_dict: dict
            * Key: features to analyze;
            * Value: [ben_with_f, ben_wo_f, mal_with_f, mal_wo_f].
        - features_sample: dict
            Features present in the considered sample.
        - label: string
            Label of the sample: 'benign' or 'malicious'.
    """

    # Set of features that were not found in the current sample
    features_not_sample = set(analyzed_features_dict.keys()) - set(features_sample.keys())

    if label == 'benign':
        i = 0
    elif label == 'malicious':
        i = 2
    else:
        i = -1
        logging.error("The label should be 'benign' or 'malicious, got %s", label)

    for feature in features_sample:
        try:
            analyzed_features_dict[feature][i] += 1  # Increase the feature is present counter
        except KeyError as err:
            logging.debug(err)
    for feature in features_not_sample:
        analyzed_features_dict[feature][i + 1] += 1  # Increase the feature not present counter


def analyze_features_all(all_features_dict1, all_features_dict2, samples_dir_list,
                         labels_list, path_info, level, features_choice, n, analysis_path):
    """ Produces a dict containing the number of occurrences (or not) of each expected feature
    with a distinction between benign and malicious files. """

    if len(samples_dir_list) != len(labels_list):
        logging.error("The number %s of directories (--vd option) does not match the number %s "
                      "of labels (--vl option)", str(len(samples_dir_list)), str(len(labels_list)))
        return None

    if "benign" not in labels_list and "malicious" not in labels_list:
        logging.error("Expected both the labels 'benign' and 'malicious' (--vl option).\nGot %s",
                      labels_list)
        return None

    pickle_path = os.path.join(analysis_path, features_choice,
                               level + '_analyzed_features_' + path_info)
    utility.check_folder_exists(pickle_path)

    analyzed_features_dict = initialize_analyzed_features_dict(all_features_dict1,
                                                               all_features_dict2)

    analyses = get_features_all_files_multiproc(samples_dir_list, labels_list, level,
                                                features_choice, n)

    for analysis in analyses:
        features_dict = analysis.features
        label = analysis.label
        if features_dict is not None:
            analyze_features(analyzed_features_dict, features_dict, label)

    pickle.dump(analyzed_features_dict, open(pickle_path, 'wb'))

    return analyzed_features_dict


def get_chi(confidence):
    """ Gets the chi value for 1 degree of freedom and for a confidence in PERCENT. """
    return round(chi2.isf(q=1-confidence/100, df=1), 2)  # With 2 decimals


def select_features(analyzed_features_dict, confidence):
    """ chi2 test, based on the presence/absence of a given feature and depending on the sample's
    ground truth. The confidence has to be given in percent. """

    selected_features_dict = dict()
    pos = 0
    chi_critical = get_chi(confidence)

    for feature in analyzed_features_dict:
        ben_with_f, ben_wo_f, mal_with_f, mal_wo_f = analyzed_features_dict[feature]

        try:
            chi_square, _, _, _ = chi2_contingency([[ben_with_f, ben_wo_f], [mal_with_f, mal_wo_f]])

        except ValueError:
            chi_square = 0

        if chi_square >= chi_critical:  # 'confidence'% confidence
            logging.debug('Feature presence and classification are not independent, chi2 = %s',
                          str(chi_square))
            selected_features_dict[feature] = pos
            pos += 1

    return selected_features_dict


def store_features(all_features_dict_path1, all_features_dict_path2, samples_dir_list,
                   labels_list, path_info, level, features_choice, analysis_path, n=4,
                   analyzed_features_path=None, chi_confidence=99):
    """ Stores the features selected by chi2 in a dict.
        The confidence has to be given in percent. """

    pickle_path = os.path.join(analysis_path, features_choice,
                               level + '_selected_features_' + str(chi_confidence))
    utility.check_folder_exists(pickle_path)

    if analyzed_features_path is None:
        all_features_dict1 = pickle.load(open(all_features_dict_path1, 'rb'))
        all_features_dict2 = pickle.load(open(all_features_dict_path2, 'rb'))

        analyzed_features_dict = analyze_features_all(all_features_dict1, all_features_dict2,
                                                      samples_dir_list, labels_list,
                                                      path_info, level, features_choice,
                                                      n, analysis_path)

    else:
        analyzed_features_dict = pickle.load(open(analyzed_features_path, 'rb'))

    selected_features_dict = select_features(analyzed_features_dict, chi_confidence)
    pickle.dump(selected_features_dict, open(pickle_path, 'wb'))

    return selected_features_dict


def store_features_all(js_dirs_validate, labels_validate, level, features_choice,
                       analysis_path, n=4, analyzed_features_path=None, chi_confidence=99):
    """ store_features for the 2 validation directories; TO CALL """

    features_path = os.path.join(analysis_path, features_choice, level + '_all_features_')

    all_features_dict_path_bad = features_path + 'malicious'
    all_features_dict_path_good = features_path + 'benign'

    if len(js_dirs_validate) != 2:
        logging.error('Please, indicate 2 folders for the features validation process (--vd option)'
                      ', 1 benign and 1 malicious, got %s folders', str(len(js_dirs_validate)))
    elif 'benign' not in labels_validate or 'malicious' not in labels_validate:
        logging.error('Please, indicate the 2 labels for the features validation process '
                      '(--vl option), one has to be \'benign\' and the other \'malicious\', the '
                      'order should correspond to the folder order, got %s', labels_validate)

    logging.debug('Currently selecting the features with chi2')
    path_info = str('')
    store_features(all_features_dict_path_good, all_features_dict_path_bad, js_dirs_validate,
                   labels_validate, path_info, level, features_choice, analysis_path, n,
                   analyzed_features_path, chi_confidence)


def get_features_all_files_multiproc(samples_dir_list, labels_list, level, features_choice, n):
    """
        Gets the features of all files from samples_dir_list.
    """

    my_queue = Queue()
    out_queue = Queue()
    except_queue = Queue()
    workers = list()

    for i, _ in enumerate(samples_dir_list):
        samples_dir = samples_dir_list[i]
        label = labels_list[i]
        for sample in os.listdir(samples_dir):
            sample_path = os.path.join(samples_dir, sample)
            analysis = static_analysis.Analysis(pdg_path=sample_path, label=label)
            my_queue.put([analysis, level, features_choice, n])

    for i in range(utility.NUM_WORKERS):
        p = Process(target=features_preselection.worker_get_features, args=(my_queue, out_queue,
                                                                            except_queue))
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
