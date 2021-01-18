# JStap: A Static Pre-Filter for Malicious JavaScript Detection

This repository contains the code for the [ACSAC'19 paper: "JStap: A Static Pre-Filter for Malicious JavaScript Detection"](https://swag.cispa.saarland/papers/fass2019jstap.pdf).  
Please note that in its current state, the code is a Poc and not a fully-fledged production-ready API.


## Summary
JStap is a modular static malicious JavaScript detection system. Our detector is composed of ten modules, including five different ways of abstracting code (namely tokens, Abstract Syntax Tree (AST), Control Flow Graph (CFG), Program Dependency Graph considering data flow only (PDG-DFG), and PDG), and two ways of extracting features (leveraging n-grams, or Identifier values). Based on the frequency of these specific patterns, we train a random forest classifier for each module. 

## Setup

```
install python3 version 3.6.7
install python3-pip # (tested with 9.0.1)
pip3 install -r requirements.txt # (tested versions indicated in requirements.txt)

install nodejs # (tested with 8.10.0)
install npm # (tested with 3.5.2)
cd pdg_generation
npm install escodegen # (tested with 1.9.1)
cd ../classification
npm install esprima # (tested with 4.0.1)
cd ..
```


## Usage

For the AST, CFG, PDG-DFG, and PDG analyses, you should generate the PDGs of the considered files separately and beforehand. After that, give the folder(s) containing the PDGs as input to the learner or classifier (in the case of an AST-based analysis, for example, we only use the AST information contained in the PDG).
On the contrary for the token-based approach, you should give directly the folder containing the JS files as input to the learner/classifier.


### PDGs Generation

To generate the PDGs of the JS files (.js) from the folder FOLDER\_NAME, launch the following shell command from the ```pdg_generation``` folder location:
```
$ python3 -c "from pdgs_generation import *; store_pdg_folder('FOLDER_NAME')"
```

The corresponding PDGs will be store in FOLDER\_NAME/Analysis/PDG.

Currently, we are using 2 CPUs for the PDGs generation process; this can be changed by modifying the variable NUM\_WORKERS from pdg\_generation/utility\_df.py.


### Learning: Building a Model

To build a model from the folders BENIGN and MALICIOUS, containing JS files (for the token-based analysis) or the PDGs (for the other analyses), use the option --d BENIGN MALICIOUS and add their corresponding ground truth with --l benign malicious.  
Select the features appearing in the training set with chi2 on 2 independent datasets: --vd BENIGN-VALIDATE MALICIOUS-VALIDATE with their corresponding ground truth --vl benign malicious.  
Indicate your analysis level with --level followed by either 'tokens', 'ast', 'cfg', 'pdg-dfg' or 'pdg'.  
Indicate the features that the analysis should use with --features followed by either 'ngrams', 'value'. You can choose where to store the features selected by chi2 with --analysis_path (default JStap/Analysis).  
You can choose the model's name with --mn (default being 'model') and its directory with --md (default JStap/Analysis).

```
$ python3 learner.py --d BENIGN/ MALICIOUS/ --l benign malicious --vd BENIGN-VALIDATE/ MALICIOUS-VALIDATE/ --vl benign malicious --level LEVEL --features FEATURES --mn FEATURES_LEVEL
```


### Classification of Unknown JS Samples
The process is similar for the classification process.  
To classify JS samples from the folders BENIGN2 and MALICIOUS2, use the option --d BENIGN2 MALICIOUS2. To load an existing model FEATURES_LEVEL to be used for the classification process, use the option --m FEATURES_LEVEL. Keep the same analysis level and features as for the classifier's training:

```
$ python3 classifier.py --d BENIGN2/ MALICIOUS2/ --level LEVEL --features FEATURES --m FEATURES_LEVEL
```

If you know the ground truth of the samples you classify and would like to evaluate the accuracy of your classifier, use the option --l with the corresponding ground truth:

```
$ python3 classifier.py --d BENIGN2 MALICIOUS2 --l benign malicious --level LEVEL --features FEATURES --m FEATURES_LEVEL
```


Currently, we are using 2 CPUs for the learning and classification processes; this can be changed by modifying the variable NUM\_WORKERS from classification/utility.py.


### Debug: Graphical AST/CFG/PDG Representations

To generate the graphical representations of the AST (save\_path\_ast), CFG (save\_path\_cfg), and/or PDG (save\_path\_pdg) of one given JS file INPUT\_FILE, we leverage the graphviz library.

To install graphviz:
```
pip3 install graphviz
On MacOS: install brew and then brew install graphviz
On Linux: install graphviz
```

Launch the following python3 commands from the `pdg_generation` folder location and indicate the name under which to store the graph(s):
```
>>> from pdgs_generation import *
>>> pdg = get_data_flow('INPUT_FILE', benchmarks=dict(), save_path_ast='ast', save_path_cfg='cfg', save_path_pdg='pdg')
```

Beware, graphviz may throw an error when the graphs are becoming too big.  
To merely display the graphs without storing them, use the value 'None'. Otherwise and per default, the value is False.


Note: per default, the corresponding PDG will not be stored. To store it in an existing PDG\_PATH folder, add the parameter `store_pdgs='PDG_PATH'` to the previous command.


## Cite this work
If you use JStap for academic research, you are highly encouraged to cite the following [paper](https://swag.cispa.saarland/papers/fass2019jstap.pdf):
```
@inproceedings{fass2019jstap,
    author="Fass, Aurore and Backes, Michael and Stock, Ben",
    title="{\textsc{JStap}: A Static Pre-Filter for Malicious JavaScript Detection}",
    booktitle="Proceedings of the Annual Computer Security Applications Conference~(ACSAC)",
    year="2019"
}
```

### Abstract:

Given the success of the Web platform, attackers have abused its main programming language, namely JavaScript, to mount different types of attacks on their victims. Due to the large volume of such malicious scripts, detection systems rely on static analyses to quickly process the vast majority of samples. These static approaches are not infallible though and lead to misclassifications. Also, they lack semantic information to go beyond purely syntactic approaches.
In this paper, we propose JStap, a modular static JavaScript detection system, which extends the detection capability of existing lexical and AST-based pipelines by also leveraging control and data flow information.
Our detector is composed of ten modules, including five different ways of abstracting code, with differing levels of context and semantic information, and two ways of extracting features. Based on the frequency of these specific patterns, we train a random forest classifier for each module.

In practice, JStap outperforms existing systems, which we reimplemented and tested on our dataset totaling over 270,000 samples. To improve the detection, we also combine the predictions of several modules. A first layer of unanimous voting classifies 93% of our dataset with an accuracy of 99.73%, while a second layer--based on an alternative modules' combination--labels another 6.5% of our initial dataset with an accuracy over 99%. This way, JStap can be used as a precise pre-filter, meaning that it would only need to forward less than 1% of samples to additional analyses. For reproducibility and direct deployability of our modules, we make our system publicly available.


## License

This project is licensed under the terms of the AGPL3 license which you can find in ```LICENSE```.
