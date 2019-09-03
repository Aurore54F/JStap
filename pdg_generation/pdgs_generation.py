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
    Generation and storage of JavaScript PDGs. Possibility for multiprocessing (NUM_WORKERS
    defined in utility_df.py).
"""

import pickle
import psutil
from multiprocessing import Process, Queue

from utility_df import *
from handle_json import *
from build_cfg import *
from build_dfg import *
from var_list import *


GIT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def get_data_flow(input_file, benchmarks, store_pdgs=None, check_var=False):
    """
        Produces the PDG of a given file.

        -------
        Parameters:
        - input_file: str
            Path of the file to study.
        - benchmarks: dict
            Contains the different microbenchmarks. Should be empty.
        - store_pdgs: str
            Path of the folder to store the PDG in.
            Or None to pursue without storing it.
        check_var: bool
            Build PDG just to check if our malicious variables are undefined. Default: False.

        -------
        Returns:
        - Node
            PDG of the file
        - or None.
    """

    start = timeit.default_timer()
    esprima_json = input_file.replace('.js', '.json')
    extended_ast = get_extended_ast(input_file, esprima_json)
    if extended_ast is not None:
        benchmarks['got AST'] = timeit.default_timer() - start
        start = micro_benchmark('Successfully got Esprima AST in', timeit.default_timer() - start)
        ast = extended_ast.get_ast()
        # beautiful_print_ast(ast, delete_leaf=[])
        ast_nodes = ast_to_ast_nodes(ast, ast_nodes=Node('Program'))
        # ast_nodes = search_dynamic(ast_nodes)  # Tried to handle dynamically generated JS
        benchmarks['AST'] = timeit.default_timer() - start
        start = micro_benchmark('Successfully produced the AST in', timeit.default_timer() - start)
        # draw_ast(ast_nodes, attributes=True, save_path=save_path_ast)
        cfg_nodes = build_cfg(ast_nodes)
        benchmarks['CFG'] = timeit.default_timer() - start
        start = micro_benchmark('Successfully produced the CFG in', timeit.default_timer() - start)
        # draw_cfg(cfg_nodes, attributes=True, save_path=save_path_cfg)
        unknown_var = []
        dfg_nodes = df_scoping(cfg_nodes, var_loc=VarList(), var_glob=VarList(),
                               unknown_var=unknown_var, id_list=[], entry=1)[0]
        # draw_pdg(dfg_nodes, attributes=True, save_path=save_path_pdg)
        for unknown in unknown_var:
            logging.warning('The variable ' + unknown.attributes['name'] + ' is not declared')
        if check_var:
            return unknown_var
        benchmarks['PDG'] = timeit.default_timer() - start
        micro_benchmark('Successfully produced the PDG in', timeit.default_timer() - start)
        if store_pdgs is not None:
            store_pdg = os.path.join(store_pdgs, os.path.basename(input_file.replace('.js', '')))
            pickle.dump(dfg_nodes, open(store_pdg, 'wb'))
        return dfg_nodes
    return None


def handle_one_pdg(root, js, store_pdgs):
    """ Stores the PDG of js located in root, in store_pdgs. """

    benchmarks = dict()
    if js.endswith('.js'):
        print(os.path.join(store_pdgs, js.replace('.js', '')))
        get_data_flow(input_file=os.path.join(root, js), benchmarks=benchmarks,
                      store_pdgs=store_pdgs)


def worker(my_queue):
    """ Worker """

    while True:
        try:
            item = my_queue.get(timeout=2)
            # print(item)
            handle_one_pdg(item[0], item[1], item[2])
        except Exception as e:
            break


def store_pdg_folder(folder_js):
    """
        Stores the PDGs of the JS files from folder_js.

        -------
        Parameters:
        - folder_js: str
            Path of the folder containing the files to get the PDG of.
    """

    start = timeit.default_timer()
    ram = psutil.virtual_memory().used
    # benchmarks = dict()

    my_queue = Queue()
    workers = list()

    if not os.path.exists(folder_js):
        logging.exception('The path %s does not exist', folder_js)
        return
    store_pdgs = os.path.join(folder_js, 'Analysis', 'PDG')
    if not os.path.exists(store_pdgs):
        os.makedirs(store_pdgs)

    for root, _, files in os.walk(folder_js):
        for js in files:
            my_queue.put([root, js, store_pdgs])
            # time.sleep(0.1)  # Just enough to let the Queue finish

    for i in range(NUM_WORKERS):
        p = Process(target=worker, args=(my_queue,))
        p.start()
        print("Starting process")
        workers.append(p)

    for w in workers:
        w.join()

    get_ram_usage(psutil.virtual_memory().used - ram)
    micro_benchmark('Total elapsed time:', timeit.default_timer() - start)
