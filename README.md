# ConstraintNetwork-FactValidation

## Data
The data is stored in the folder 0.Data and is split into a zip file, to unzip you have to run the following commands in the 0.Data folder :
unzip Data.zip
The data is then organised following per class with the following hierarchy :

data.quintuplet : the full positive data non split
train_cst_knowledge.quintuplet : the training positive data to discover the Contraints and used a the description of entities
train_ML.quintuplet : the training postive/negative data for the ML algorithm
train_ML.gt : the ground truth for the train_ML data
valid.quintuplet
valid.gt
test.quintuplet
test.gt

The data can be generated for a new class through the use of a HDT file and a query script such as Sparql.jar. All the script are under the folder 1.DataGeneration and a general script can launch the process with 0.1.GenData.py.

> Don't forget to use the `building_graph` parameter of the 5.RulesDiscovery scripts to enable the building and saving of the constraint networks.
> To generate constraint network compatible with GEQCA put the `geqca` to True.

## Runable experiment
To run the experiment first create a environment following the `requirements.txt`.
### Constraint discovery
Afterward, you can run the temporal constraint discovery:

`python discovery.py --cons_net_folder constraint_networks`

To get the full list of options of the script use the `--help` option.
You can also change the amount of data use for the experiment (line 61 of `discovery.py`).
### Evaluation
To compute the evaluation, run the `testing.py` script:

`python testing.py --cons_net_folder constraint_networks`

You can see the other options using the `--help` option.
You can also change the amount of data use for the experiment (line 264 of `testing.py`).
