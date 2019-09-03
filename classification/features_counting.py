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

""" Features frequency analysis. """


import logging

import features_ngrams
import features_value


def n_grams_list(numbers_list, n):
    """
        Producing n-grams from units by moving a fixed-length window to extract subsequence
        of length n.

        -------
        Returns:
        - Matrix
            Rows: tuples representing every possible n-gram (produced from numbers_list);
            Columns: part of the previous tuples
        - or None if numbers_list is empty.
    """

    if numbers_list is not None:
        len_numbers_list = len(numbers_list)
        if n < 1:
            logging.warning('Please indicate a value so that n > 0, current %s', n)
        elif n > len_numbers_list:
            matrix_all_n_grams = list()
            ngram = [None for _ in range(n)]
            for i, _ in enumerate(numbers_list):
                ngram[i] = numbers_list[i]
            matrix_all_n_grams.append(tuple(ngram))
            return matrix_all_n_grams
        else:
            range_n = range(n)
            matrix_all_n_grams = list()
            range_list = range(len_numbers_list - (n - 1))
            for j in range_list:  # Loop on all the n-grams
                matrix_all_n_grams.append(tuple(numbers_list[j + i] for i in range_n))
            return matrix_all_n_grams
    return None


def count_ngrams(file_repr, level, n):
    """
        Given a matrix containing every possible n-gram (for a JavaScript given file), count
        and store (once) the number of occurrences of each set of n-gram in a dictionary.

        Returns:
        - Dictionary
            Key: tuple representing an n-gram;
            Value: number of occurrences of a given tuple of n-gram.
        - int: the number of different features.
        - or None, None if matrix_all_n_grams is empty.
    """

    features_list, pdg_size = features_ngrams.extract_features(file_repr, level)
    matrix_all_n_grams = n_grams_list(features_list, n)
    # Each row: tuple representing an n-gram.

    if matrix_all_n_grams is not None:
        dico_of_n_grams = {}
        # Nb of lines in the matrix, i.e. of sets of n-grams
        for j, _ in enumerate(matrix_all_n_grams):
            if matrix_all_n_grams[j] in dico_of_n_grams:
                dico_of_n_grams[matrix_all_n_grams[j]] += 1
            else:
                dico_of_n_grams[matrix_all_n_grams[j]] = 1

        return dico_of_n_grams, len(matrix_all_n_grams), pdg_size
    return None, None, pdg_size


def count_value(file_repr, level):
    """ Returns (context, value) features + the total number of features. """

    features_list, pdg_size = features_value.extract_features(file_repr, level)
    if features_list is not None:
        unique_features_dict = dict()
        for feature in features_list:
            if feature not in unique_features_dict:
                unique_features_dict[feature] = 1
            else:
                unique_features_dict[feature] += 1
        return unique_features_dict, len(features_list), pdg_size
    return None, None, pdg_size


def count_ngram_value(file_repr, level, n):
    """ Returns (context, value) * n-gram features + the total number of features. """

    features_list, pdg_size = features_value.extract_features(file_repr, level)
    matrix_all_n_grams = n_grams_list(features_list, n)
    # Each row: tuple representing an n-gram.

    if matrix_all_n_grams is not None:
        dico_of_n_grams = {}
        # Nb of lines in the matrix, i.e. of sets of n-grams
        for j, _ in enumerate(matrix_all_n_grams):
            if matrix_all_n_grams[j] in dico_of_n_grams:
                dico_of_n_grams[matrix_all_n_grams[j]] += 1
            else:
                dico_of_n_grams[matrix_all_n_grams[j]] = 1

        return dico_of_n_grams, len(matrix_all_n_grams), pdg_size
    return None, None, pdg_size
