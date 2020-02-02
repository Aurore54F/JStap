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
    Main module to build a model to classify future JavaScript files.
"""

import os
import pickle
import logging
import argparse

import features_preselection
import features_selection
import static_analysis
import machine_learning
import utility

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def classify(names, labels, attributes, model_dir, model_name, estimators,
             print_score=False, print_res=False):
    """
        Training a classifier.

        -------
        Parameters:
        - names: list
            Name of the data files used to build a model from.
        - labels: list
            Labels (i.e. 'benign', 'malicious') of the data used to build a model from.
        - attributes: np.array
            Features of the data used to build a model from.
        - model_dir: str
            Path to store the model that will be produced.
        - model_name: str
            Name of the model that will be produced.
        - estimators: int
            Number of trees in the forest.
        - print_score: bool
            Indicates whether to print or not the classifier's performance. Default: False.
        - print_res: bool
            Indicates whether to print or not the classifier's predictions. Default: False.

        -------
        Returns:
        - The selected model constructed using the training attributes.
            Beware: the model was implemented as a global variable in sklearn.
        - If specified, can also:
            * Print the detection rate and the TP, FP, FN and TN rates of
            the training names tested with the model built from the training attributes, in stdout.
            It will only work for these two classes: 'benign' and 'malicious'.
            * Print the classifier's predictions.
            Beware, the predictions made using the same file to build and test
            the model will give hopelessly optimistic results.
            See >$ python3 <path-of-clustering/classifier.py> -help
            to test a model on new files.
    """

    # Directory to store the classification related files
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    clf = machine_learning.classifier_choice(estimators=estimators)
    trained = clf.fit(attributes, labels)  # Model
    labels_predicted = clf.predict(attributes)  # Classification and class predictions

    if print_score:
        machine_learning.get_score(labels, labels_predicted)

    if print_res:
        machine_learning.get_classification_results(names, labels_predicted)

    model_path = os.path.join(model_dir, model_name)
    pickle.dump(trained, open(model_path, 'wb'))
    logging.info('The model has been successfully stored in %s', model_path)

    return trained


def parsing_commands():
    """
        Creation of an ArgumentParser object, holding all the information necessary to parse
        the command line into Python data types.
    """

    parser = argparse.ArgumentParser(description='Given a list of directory or file paths, '
                                                 'builds a model to classify future '
                                                 'JS inputs.')

    parser.add_argument('--d', metavar='DIR', type=str, nargs='+',
                        help='directories to be used to build a model from')
    parser.add_argument('--l', metavar='LABEL', type=str, nargs='+',
                        choices=['benign', 'malicious'],
                        help='labels of the JS directories used to build a model from')
    parser.add_argument('--vd', metavar='DIR-VALIDATE', type=str, nargs='+',
                        help='2 JS dir (1 benign, 1 malicious) to select the features with chi2')
    parser.add_argument('--vl', metavar='LABEL', type=str, nargs='+',
                        choices=['benign', 'malicious'],
                        help='labels of the 2 JS dir for the features selection process')
    parser.add_argument('--md', metavar='MODEL-DIR', type=str, nargs=1,
                        default=[os.path.join(SRC_PATH, 'Analysis')],
                        help='path to store the model that will be produced')
    parser.add_argument('--mn', metavar='MODEL-NAME', type=str, nargs=1,
                        default=['model'],
                        help='name of the model that will be produced')
    parser.add_argument('--ps', metavar='BOOL', type=bool, nargs=1, default=[False],
                        help='indicates whether to print or not the classifier\'s detection rate')
    parser.add_argument('--pr', metavar='BOOL', type=bool, nargs=1, default=[False],
                        help='indicates whether to print or not the classifier\'s predictions')
    parser.add_argument('--nt', metavar='NB_TREES', type=int, nargs=1,
                        default=[500], help='number of trees in the forest')

    utility.parsing_commands(parser)

    return vars(parser.parse_args())


arg_obj = parsing_commands()
utility.control_logger(arg_obj['v'][0])


def main_learn(js_dirs=arg_obj['d'], js_dirs_validate=arg_obj['vd'], labels_validate=arg_obj['vl'],
               labels_d=arg_obj['l'], model_dir=arg_obj['md'], model_name=arg_obj['mn'],
               print_score=arg_obj['ps'], print_res=arg_obj['pr'], level=arg_obj['level'],
               n=arg_obj['n'][0], estimators=arg_obj['nt'], features_choice=arg_obj['features'],
               analysis_path=arg_obj['analysis_path'][0]):
    """
        Main function, performs a static analysis (syntactic) of JavaScript files given as input
        to build a model to classify future JavaScript files.

        -------
        Parameters:
        - js_dirs: list of strings
            Directories containing the JS files to be analysed.
        - js_dirs_validate: list of strings
            2 JS dir (1 benign, 1 malicious) to select the features with chi2.
        - labels_validate: list of strings
            Labels of the 2 JS dir for the features selection process
        - labels_d: list of strings
            Indicates the label's name of the directories considered: either benign or malicious.
        - model_dir: String
            Path to store the model that will be produced.
            Default value being the folder JS-Analysis/Classification/.
        - model_name: String
            Name of the model that will be produced.
            Default value being model.
        - print_score: Boolean
            Indicates whether to print or not the classifier's performance.
        - print_res: Boolean
            Indicates whether to print or not the classifier's predictions.
        - n: Integer
            Stands for the size of the sliding-window which goes through the units contained in the
            files to be analysed.
        - estimators: int
            Number of trees in the forest.
        - level: str
            Either 'tokens', 'ast', 'cfg', 'pdg', or 'pdg-dfg' depending on the units you want
            to extract.
        - features_choice: str
            Either 'ngrams' or 'value' depending on the features you want.
        - analysis_path: str
            Folder to store the features' analysis results in.
        Default values are the ones given in the command lines or in the
        ArgumentParser object (function parsingCommands()).
    """

    if js_dirs is None:
        logging.error('Please, indicate at least 2 directories (--d option), at least one benign '
                      'and one malicious (--l option to pass the corresponding labels).\nGot 0 '
                      'directories with the following labels: %s', labels_d)

    elif len(js_dirs) < 2 or labels_d is None\
            or 'benign' not in labels_d or 'malicious' not in labels_d:
        logging.error('Please, indicate at least 2 directories (--d option), at least one benign '
                      'and one malicious (--l option to pass the corresponding labels).\nGot %s '
                      'directories with the following labels: %s', str(len(js_dirs)), labels_d)

    elif js_dirs is not None and (labels_d is None or len(js_dirs) != len(labels_d)):
        logging.error('Please, indicate as many directory labels (--l option) as the number %s of '
                      'directories to analyze', str(len(js_dirs)))

    elif js_dirs_validate is None:
        logging.error('Please, indicate the 2 JS directories (--vd option) '
                      'with corresponding labels (--vl option, 1 benign and 1 malicious) '
                      'for the features validation process')

    elif len(js_dirs_validate) != 2 or labels_validate is None\
            or 'benign' not in labels_validate or 'malicious' not in labels_validate:
        logging.error('Please, indicate the 2 JS directories (--vd option) '
                      'with corresponding labels (--vl option, 1 benign and 1 malicious) '
                      'for the features validation process.\nGot %s directories with following '
                      'labels %s', str(len(js_dirs_validate)), labels_validate)

    elif utility.check_params(level, features_choice) == 0:
        return

    else:
        analysis_path = os.path.join(analysis_path, 'Features')
        utility.check_folder_exists(analysis_path)

        features2int_dict_path = os.path.join(analysis_path, features_choice[0],
                                              level[0] + '_selected_features_99')

        features_preselection.handle_features_all(js_dirs, labels_d, level[0], features_choice[0],
                                                  analysis_path, n)
        features_selection.store_features_all(js_dirs_validate, labels_validate, level[0],
                                              features_choice[0], analysis_path, n)

        names, attributes, labels = static_analysis.main_analysis\
            (js_dirs=js_dirs, labels_dirs=labels_d, js_files=None, labels_files=None,
             n=n, level=level[0], features_choice=features_choice[0],
             features2int_dict_path=features2int_dict_path)

        if names:
            # Uncomment to save the analysis results in pickle objects.
            """
            utility.save_analysis_results(os.path.join(model_dir[0], "Analysis-n" + str(n) + "-dict"
                                                       + str(dict_not_hash)),
                                          names, attributes, labels)
            """

            classify(names, labels, attributes, model_dir=model_dir[0], model_name=model_name[0],
                     print_score=print_score[0], print_res=print_res[0], estimators=estimators[0])

        else:
            logging.warning('No valid JS file found for the analysis')


if __name__ == "__main__":  # Executed only if run as a script
    main_learn()
