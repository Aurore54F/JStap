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
    Main module to classify JavaScript files using a given model.
"""

import os
import pickle
import argparse
import logging

import machine_learning
import utility
import static_analysis


def test_model(names, labels, attributes, model, print_res=False, print_res_verbose=True,
               print_score=True, threshold=0.50):
    """
        Use an existing model to classify new JS inputs.

        -------
        Parameters:
        - names: list
            Name of the data files used to be tested using the following model.
        - labels: list
            Labels (i.e. 'benign', 'malicious', or '?') of the test data using the model.
        - attributes: csr_matrix
            Features of the data used to be tested using the following model.
        - model
            Model to be used to classify new observations.
        Beware: the model must have been constructed using files of the same format
        (i.e. same attributes) as the format of test_file.
        - print_res: bool
            Indicates whether to print or not the classifier's predictions.
        - print_res_verbose: bool
            Indicates whether to print or not the classifier's predictions, including the
            probability of membership for each class.
        - print_score: bool
            Indicates whether to print or not the classifier's performance.
        - threshold: float
            Probability of a sample being malicious over which the sample will be classified
            as malicious.

        -------
        Returns:
        - list:
            List of labels predicted.
    """

    if isinstance(model, str):
        model = pickle.load(open(model, 'rb'))

    labels_predicted_proba_test = model.predict_proba(attributes)
    # Probability of the samples for each class in the model.
    # First column = benign, second = malicious.
    # labels_predicted_test = model.predict(attributes_test)
    # accuracy_test = model.score(attributes_test, labels_test)  # Detection rate

    labels_predicted_test = machine_learning.\
        predict_labels_using_threshold(len(names), labels_predicted_proba_test, threshold)
    # Perform classification using a threshold (probability of the sample being malicious)
    # to predict the target values

    if print_res:
        machine_learning.get_classification_results(names, labels_predicted_test)

    if print_res_verbose:
        machine_learning.get_classification_results_verbose(names, labels, labels_predicted_test,
                                                            labels_predicted_proba_test, model,
                                                            attributes, threshold)

    if print_score:
        machine_learning.get_score(labels, labels_predicted_test)

    return labels_predicted_test


def parsing_commands():
    """
        Creation of an ArgumentParser object, holding all the information necessary to parse
        the command line into Python data types.
    """

    parser = argparse.ArgumentParser(description='Given a list of directory or file paths,\
    detects the malicious JS inputs.')

    parser.add_argument('--d', metavar='DIR', type=str, nargs='+',
                        help='directories containing the JS files to be analyzed')
    parser.add_argument('--l', metavar='LABEL', type=str, nargs='+',
                        choices=['benign', 'malicious', '?'],
                        help='labels of the JS directories to evaluate the model from')
    parser.add_argument('--f', metavar='FILE', type=str, nargs='+', help='files to be analyzed')
    parser.add_argument('--lf', metavar='LABEL', type=str, nargs='+',
                        choices=['benign', 'malicious', '?'],
                        help='labels of the JS files to evaluate the model from')
    parser.add_argument('--m', metavar='MODEL', type=str, nargs=1,
                        help='path of the model used to classify the new JS inputs '
                             '(see >$ python3 <path-of-clustering/learner.py> -help) '
                             'to build a model)')
    parser.add_argument('--th', metavar='THRESHOLD', type=float, nargs=1, default=[0.50],
                        help='threshold over which all samples are considered malicious')
    utility.parsing_commands(parser)

    return vars(parser.parse_args())


arg_obj = parsing_commands()
utility.control_logger(arg_obj['v'][0])


def main_classification(js_dirs=arg_obj['d'], js_files=arg_obj['f'], labels_f=arg_obj['lf'],
                        labels_d=arg_obj['l'], model=arg_obj['m'], threshold=arg_obj['th'],
                        level=arg_obj['level'], features_choice=arg_obj['features'],
                        n=arg_obj['n'][0], analysis_path=arg_obj['analysis_path'][0]):
    """
        Main function, performs a static analysis (syntactic) of JavaScript files given as input
        before predicting if the executables are benign or malicious.

        -------
        Parameters:
        - js_dirs: list of strings
            Directories containing the JS files to be analysed.
        - js_files: list of strings
            Files to be analysed.
        - labels_f: list of strings
            Indicates the label's name of the files considered: either benign or malicious.
        - labels_d: list of strings
            Indicates the label's name of the current data: either benign or malicious.
        - model: str
            Path to the model used to classify the new files
        - threshold: int
            Threshold over which all samples are considered malicious
        - n: Integer
            Stands for the size of the sliding-window which goes through the units contained in the
            files to be analysed.
        - level: str
            Either 'tokens', 'ast', 'cfg', 'pdg', or 'pdg-dfg' depending on the units you want
            to extract.
        - analysis_path: str
            Folder to store the features' analysis results in.
        - features_choice: str
            Either 'ngrams' or 'value' depending on the features you want.
        Default values are the ones given in the command lines or in the
        ArgumentParser object (function parsingCommands()).

        -------
        Returns:
        The results of the static analysis of the files given as input:
        either benign or malicious
    """

    if js_dirs is None and js_files is None:
        logging.error('Please, indicate at least a directory (--d option) '
                      'or a JS file (--f option) to be analyzed')

    elif js_dirs is not None and labels_d is not None and len(js_dirs) != len(labels_d):
        logging.error('Please, indicate as many directory labels (--l option) as the number %s '
                      'of directories to analyze', str(len(js_dirs)))

    elif js_files is not None and labels_f is not None and len(js_files) != len(labels_f):
        logging.error('Please, indicate as many file labels (--lf option) as the number %s '
                      'of files to analyze', str(len(js_files)))

    elif model is None:
        logging.error('Please, indicate a model (--m option) to be used to classify new files.\n'
                      '(see >$ python3 <path-of-clustering/learner.py> -help) to build a model)')

    elif utility.check_params(level, features_choice) == 0:
        return

    else:
        features2int_dict_path = os.path.join(analysis_path, 'Features', features_choice[0],
                                              level[0] + '_selected_features_99')

        names, attributes, labels = static_analysis.main_analysis\
            (js_dirs=js_dirs, labels_dirs=labels_d, js_files=js_files, labels_files=labels_f,
             n=n, level=level[0], features_choice=features_choice[0],
             features2int_dict_path=features2int_dict_path)

        if names:
            # Uncomment to save the analysis results in pickle objects.
            """
            machine_learning.save_analysis_results(os.path.join(js_dirs[0], "Analysis-res-stored"),
                                                   names, attributes, labels)
            """

            test_model(names, labels, attributes, model=model[0], threshold=threshold[0])

        else:
            logging.warning('No valid JS file found for the analysis')


if __name__ == "__main__":  # Executed only if run as a script
    main_classification()


def classify_analysis_results(save_dir, model, threshold):
    """
        Uses the results of a static analysis (syntactic) of JavaScript files to predict if the
        executables are benign or malicious.

        -------
        Parameters:
        - save_dir: str
            Path of the directory where the results (i.e. names of the files considered, their true
            label as well as their attributes) are stored.
        - model: str
            path to the model used to classify the new files
        - threshold: int
            threshold over which all samples are considered malicious

        -------
        Returns:
        The results of the static analysis of the files given as input:
        either benign or malicious
    """

    names = pickle.load(open(os.path.join(save_dir, 'Names'), 'rb'))
    attributes = pickle.load(open(os.path.join(save_dir, 'Attributes'), 'rb'))
    labels = pickle.load(open(os.path.join(save_dir, 'Labels'), 'rb'))

    test_model(names, labels, attributes, model=model, threshold=threshold)
