
"""
    Extracting syntactic units from a JavaScript file and converting them into integers.
"""

import sys
import os
import pickle
import logging
from subprocess import run, PIPE


SRC_PATH = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(SRC_PATH, 'tokens2int'))
import parser_esprima
import tokenizer_esprima

sys.path.insert(0, os.path.join(SRC_PATH, '..', 'pdg_generation'))
import node


sys.setrecursionlimit(400000)  # Probably need it to unpickle BIG PDGs ;)


def get_tokens_features(input_file):
    """
        Given a JavaScript file, create a list containing the esprima lexical units.

        -------
        Parameter:
        - input_file: str
            Path of the JS file to analyze.

        -------
        Returns:
        - list of str
            Lexical units (tokens) extracted.
        or None if something wrong occurred.
    """

    get_tokens = run(['node', os.path.join(SRC_PATH, 'tokenizer.js'), input_file],
                     stdout=PIPE)
    try:
        tokens = get_tokens.stdout.decode('utf-8').split('\n')[:-1]  # Last one being ''
        return tokens
    except:
        logging.error('Something went wrong with %s', input_file)
    return None


def get_ast_features(pdg, features_list, handled_set):
    """
        Given the PDG of a JavaScript file, create a list containing the esprima syntactic
        units.
        The order of the units stored in the previous list resembles a tree traversal using
        the depth-first pre order.

        -------
        Parameters:
        - pdg: node
            PDG of the JS file to analyze.
        - features_list: list
            Contains the units found so far.
        - handled_list: list
            Contains the nodes id handled so far.
    """

    for child in pdg.children:
        if child.id not in handled_set:
            handled_set.add(child.id)
            features_list.append(child.name)
            get_ast_features(child, features_list, handled_set)


def get_size_subgraph(node, size=0):
    """ Gets a subtree size."""
    for child in node.children:
        size += 1
        size = get_size_subgraph(child, size)
    return size


def get_cfg_features(pdg, features_list, handled_set, handled_features_set):
    """ To provide complete code coverage while following only the CF. """

    for child in pdg.children:
        if child.id not in handled_set:
            traverse_cfg(child, features_list, handled_set, handled_features_set)
        get_cfg_features(child, features_list, handled_set, handled_features_set)


def traverse_cfg(pdg, features_list, handled_set, handled_features_set):
    """
        Given the PDG of a JavaScript file, create a list containing the esprima syntactic
        units with a Control dependency.
        The order of the units stored in the previous list resembles a tree traversal using
        the depth-first pre order.

        -------
        Parameters:
        - pdg: node
            PDG of the JS file to analyze.
        - features_list: list
            Contains the units found so far.
        - handled_list: list
            Contains the nodes id handled so far.
    """

    if pdg.control_dep_children:
        features_list.append(pdg.name)
        handled_features_set.add(pdg.id)  # Store id from features handled
        get_ast_features(pdg, features_list, handled_features_set)  # Handled only once
    for control_dep in pdg.control_dep_children:
        control_flow = control_dep.extremity
        # Otherwise missing CF pointing to a node already analyzed
        if not control_flow.control_dep_children or control_flow.id in handled_set:
            features_list.append(control_flow.name)
        # else: the node name will be added while calling traverse_cfg
        if control_flow.id not in handled_set:
            handled_set.add(control_flow.id)
            handled_features_set.add(control_flow.id)  # Store id from features
            get_ast_features(control_flow, features_list, handled_features_set)  # Once
            traverse_cfg(control_flow, features_list, handled_set, handled_features_set)


def get_pdg_features(pdg, features_list, handled_set, handled_features_set):
    """ To provide complete code coverage while following only the CF. """

    for child in pdg.children:
        if child.id not in handled_set:
            traverse_pdg(child, features_list, handled_set, handled_features_set)
        get_pdg_features(child, features_list, handled_set, handled_features_set)


def traverse_pdg(pdg, features_list, handled_set, handled_features_set):
    """
        Given the PDG of a JavaScript file, create a list containing the esprima syntactic
        units with a Data dependency.
        The order of the units stored in the previous list resembles a tree traversal using
        the depth-first pre order.

        -------
        Parameters:
        - pdg: node
            PDG of the JS file to analyze.
        - features_list: list
            Contains the units found so far.
        - handled_list: list
            Contains the nodes id handled so far.
    """

    if pdg.data_dep_children:
        features_list.append(pdg.name)
        handled_features_set.add(pdg.id)  # Store id from features handled
        get_ast_features(pdg, features_list, handled_features_set)  # Handled only once
    for data_dep in pdg.data_dep_children:
        data_flow = data_dep.extremity
        # Otherwise missing CF pointing to a node already analyzed
        if not data_flow.data_dep_children or data_flow.id in handled_set:
            features_list.append(data_flow.name)
        # else: the node name will be added while calling traverse_pdg
        if data_flow.id not in handled_set:
            handled_set.add(data_flow.id)
            handled_features_set.add(data_flow.id)  # Store id from features
            get_ast_features(data_flow, features_list, handled_features_set)  # Once
            traverse_pdg(data_flow, features_list, handled_set, handled_features_set)


def get_pdg_features_with_cfg(pdg, features_list, handled_set_pdg, handled_features_pdg_set,
                              handled_set_cfg, handled_features_cfg_set):
    """ Follows both data and control flow, alternative traaversal. """

    get_pdg_features(pdg, features_list, handled_set_pdg, handled_features_pdg_set)
    get_cfg_features(pdg, features_list, handled_set_cfg, handled_features_cfg_set)


def get_pdg_features_with_cfg_ast(pdg, features_list):
    """ Follows both data and control flow and AST nodes not handled yet. """

    handled_features_pdg_set, handled_features_cfg_set = set(), set()
    get_pdg_features_with_cfg(pdg, features_list, set(), handled_features_pdg_set,
                              set(), handled_features_cfg_set)

    handled_set = set(list(handled_features_pdg_set) + list(handled_features_cfg_set))
    get_ast_features(pdg, features_list, handled_set)  # Only nodes not handled yet


def get_pdg_features_with_ast(pdg, features_list):
    """ Follows both data flow and AST nodes not handled yet. """

    handled_features_pdg_set = set()
    get_pdg_features(pdg, features_list, set(), handled_features_pdg_set)
    get_ast_features(pdg, features_list, handled_features_pdg_set)  # Only nodes not handled yet


def extract_syntactic_features(pdg_path, level):
    """
        Given an input JavaScript file, create a list containing the esprima syntactic
        units present in the file.
        The order of the units stored in the previous list resembles a tree traversal using
        the depth-first algorithm post-order.

        -------
        Parameters:
        - pdg: str
            Path of the PDG of the file to be analysed.
        - level: str
            Either 'tokens', 'ast', 'cfg', or 'pdg' depending on the units you want to extract.

        -------
        Returns:
        - List
            Contains the esprima syntactic units present in the input file.
        - or None if the file either is no JS or malformed.
    """

    logging.info('Analysis of %s', pdg_path)
    try:
        if os.stat(pdg_path).st_size < 10000000:  # Avoids handling PDGs over 10MB for perf reasons
            pdg = pickle.load(open(pdg_path, 'rb'))
            if pdg is not None:  # Not sure if it can be None
                features_list = list()
                if level == 'ast':
                    if not pdg.children:
                        print(pdg_path + ': ' + 'benign (benign) _ EMPTY AST')
                    else:
                        get_ast_features(pdg, features_list=features_list, handled_set=set())
                elif level == 'cfg':
                    get_cfg_features(pdg, features_list=features_list, handled_set=set(),
                                     handled_features_set=set())
                elif level == 'pdg-dfg':
                    get_pdg_features(pdg, features_list=features_list, handled_set=set(),
                                     handled_features_set=set())
                elif level == 'pdg':
                    get_pdg_features_with_cfg(pdg, features_list=features_list,
                                              handled_set_pdg=set(), handled_set_cfg=set(),
                                              handled_features_pdg_set=set(),
                                              handled_features_cfg_set=set())
                elif level == 'pdg-cfg-ast':
                    get_pdg_features_with_cfg_ast(pdg, features_list=features_list)
                elif level == 'pdg-ast':
                    get_pdg_features_with_ast(pdg, features_list=features_list)
                else:
                    logging.error('Expected \'ast\' or \'cfg\' or \'pdg-dfg\' or \'pdg\''
                                  + ', got %s instead', level)
                return features_list, os.stat(pdg_path).st_size
        return None, os.stat(pdg_path).st_size
    except:
        logging.error('The PDG of %s could not be loaded', pdg_path)
    return None, None


def extract_features(file_repr, level):
    """
        Convert a list of syntactic units in their corresponding numbers
        (as indicated in the corresponding units dictionary).

        -------
        Parameters:
        - file_repr: str
            File representation: path of the PDG of the file to be analysed (cases ast, cfg and pdg)
            or path of the file (case tokens).
        - level: str
            Either 'tokens', 'ast', 'cfg', or 'pdg' depending on the units you want to extract.

        -------
        Returns:
        - List
            Contains the Integers which correspond to the units given in tokens_list.
        - or None if tokens_list is empty (cases where the JS file considered either is no JS,
        malformed or empty).
    """

    pdg_size = None

    if level == 'ast' or level == 'cfg' or level == 'pdg-dfg' or level == 'pdg':
        dico_features = parser_esprima.ast_units_dico
        # List of syntactic units linked by parents, control or data flow
        features_list, pdg_size = extract_syntactic_features(file_repr, level)
    elif level == 'tokens':
        dico_features = tokenizer_esprima.tokens_dico
        features_list = get_tokens_features(file_repr)  # List of lexical units (tokens)
    else:
        features_list = None
        logging.error('Expected \'tokens\' or \'ast\' or \'cfg\' or \'pdg-dfg\' or \'pdg\''
                      + ', got %s instead', level)
    # print(features_list)

    if features_list is not None and features_list != []:
        return list(map(lambda x: dico_features[x], features_list)), pdg_size
    return None, pdg_size
