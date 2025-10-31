import pickle
import networkx as nx
import matplotlib.pyplot as plt
import pprint
from tqdm import tqdm
from collections import defaultdict
from testing import test_rule
import os
import argparse


def global_rule_discovery(bij, nb_intervals, accuracy_threshold):
    """
        @brief: Return a rule if the given bij is a global rule
    """
    if len(bij[str(edg[2])][0]) + len(bij[str(edg[2])][1]) == nb_intervals:
        acc = test_rule(train_indices, {str(edg[2]): [(bij[str(edg[2])][0], bij[str(edg[2])][1])]})
        if acc[0] > accuracy_threshold:
            return {str(edg[2]): (bij[str(edg[2])][0], bij[str(edg[2])][1])}
    return None


def merge_graphs_sum_attributes(prop_graph, tmp_graph):
    """
        @brief: Merge the two input graphs and sum their weight attribute
        @params:
            prop_graph: the graph to merge into
            tmp_graph: the graph to merge in
    """
    for n in tmp_graph.nodes().data(True):
        if n[0] in prop_graph.nodes():
            for idx, n_2 in enumerate(prop_graph.nodes().data(True)):
                if n_2[0] == n[0]:
                    attrs = {idx: {"weight": n_2[1]["weight"] + 1, "relation": n_2[1]["relation"]}}
                    nx.set_node_attributes(prop_graph, attrs)
        else:
            try:
                prop_graph.add_node(n[0], weight=n[1]["weight"], relation=n[1]["relation"])
            except Exception:
                pass
    return prop_graph


if __name__ == "__main__":
    # Parameters:
    parser = argparse.ArgumentParser(
                    prog='Constraint network fact temporal constraint discovery',
                    description='Discover constraints from constraint networks and save in the associated folder',
                    epilog='Contact Timothée Strouk <timothee.strouk@student-cs.fr> for any questions ;)')
    parser.add_argument("--cons_net_folder")
    parser.add_argument("--constraints_folder", default="rules")
    parser.add_argument("--noise_ratio", default=str(0.05))
    parser.add_argument("--inclusive", default=str(False))
    parser.add_argument("--accuracy_threshold", default=str(0.95))
    parser.add_argument("--enable_weighted_mapping", default=str(True))
    args = parser.parse_args()
    # End of parameters
    validate = 0
    total = 0
    # TODO: Test on more data, not in parameter because it should always be full dataset except in development
    train_indices = [i for i in range(2000)]

    # REFACTO: should be put in a function
    """
        @brief: Discover constraint from the constraint network in the train indices
    """
    prop_to_idx = defaultdict(list)
    for cons_net_id in tqdm(train_indices, leave=False):
        with open(f"{cons_net_id}_constraint_network.pkl", "rb") as f:
            cons_net = pickle.load(f)
            nodes = list(cons_net.nodes())
            # we shouldn't have empty networks
            if len(nodes) == 0:
                print("empty")
                continue
            p1 = nodes[0].split("/")[-1].split('_')[0]
            for n in nodes:
                t = n.split("/")[-1].split('_')[0]
                if t != p1 and ('P' in t or 'Q' in t):
                    p2 = t
                    break
            prop_to_idx[(p1, p2)].append(cons_net_id)

    whole_candidates = {}
    candidates = {
            "B": [],
            "M": [],
            "O": [],
            "F": [],
            "S": [],
            "E": [],
            "D": [],
            "BI": [],
            "MI": [],
            "OI": [],
            "FI": [],
            "SI": [],
            "DI": []
    }
    # list of weighted mappings
    prop_graphs = []
    # can be saved to do some data science on
    X = {
            "B": [],
            "M": [],
            "O": [],
            "F": [],
            "S": [],
            "E": [],
            "D": [],
            "BI": [],
            "MI": [],
            "OI": [],
            "FI": [],
            "SI": [],
            "DI": []
    }
    for prop in tqdm(prop_to_idx):
        train_indices = prop_to_idx[prop]
        prop_graph = nx.DiGraph()
        for cons_net_id in tqdm(train_indices, leave=False):

            m = {
                "B": [],
                "M": [],
                "O": [],
                "F": [],
                "S": [],
                "E": [],
                "D": [],
                "BI": [],
                "MI": [],
                "OI": [],
                "FI": [],
                "SI": [],
                "DI": []
            }
            # list of all mappings
            global_bij = []
            # bij is a mapping
            bij = {
                "B": [[], []],
                "M": [[], []],
                "O": [[], []],
                "F": [[], []],
                "S": [[], []],
                "E": [[], []],
                "D": [[], []],
                "BI": [[], []],
                "MI": [[], []],
                "OI": [[], []],
                "FI": [[], []],
                "SI": [[], []],
                "DI": [[], []]
            }
            nb_inervals = 0
            tmp_graph = nx.DiGraph()
            old_A_term = None
            old_B_term = None
            with open(f"{cons_net_id}_constraint_network.pkl", "rb") as f:
                cons_net = pickle.load(f)
                nb_intervals = len(cons_net.nodes())
                for edg in tqdm(cons_net.edges().data("constraint", default=""), leave=False):
                    # split to get only {number} associated with the interval
                    if edg[0].split('_')[0] == edg[1].split('_')[0]:
                        continue
                    else:
                        p1 = edg[0].split('/')[-1].split('_')[0]
                        p2 = edg[1].split('/')[-1].split('_')[0]
                    m[str(edg[2])].append((edg[0], edg[1]))

                    if p1 in edg[0]:
                        A_term = edg[0].split('/')[-1].split("_")[1]
                        B_term = edg[1].split('/')[-1].split("_")[1]
                    else:
                        A_term = edg[1].split('/')[-1].split("_")[1]
                        B_term = edg[0].split('/')[-1].split("_")[1]
                    bij[str(edg[2])][0].append(A_term)
                    bij[str(edg[2])][1].append(B_term)
                    # For each term add a node in the graph
                    # Create a link between this node and the previous one
                    # Nodes have a weight property
                    if old_A_term is not None:
                        tmp_graph.add_edge("A_" + old_A_term + " B_" + old_B_term, "A_" + A_term + "B_" + B_term)
                    tmp_graph.add_node("A_" + A_term + " B_" + B_term, weight=0, relation=str(edg[2]))
                    old_A_term = A_term
                    old_B_term = B_term

                global_bij.append(bij)
                # cheking for mapping repetition
                for partial_rule in global_bij:
                    for key_cand in partial_rule:
                        candidate = partial_rule[key_cand]
                        for bij in global_bij:
                            for key_other in bij:
                                other_bij = bij[key_other]
                                # potential constraint because of repetition
                                if ''.join(candidate[0]) == ''.join(other_bij[0]) \
                                   and ''.join(candidate[1]) == ''.join(other_bij[1]) \
                                   and (candidate[0], candidate[1]) not in candidates[key_cand] \
                                   and key_cand == key_other: 
                                        candidates[key_cand].append((candidate[0], candidate[1]))

            prop_graph = merge_graphs_sum_attributes(prop_graph, tmp_graph)
        prop_graphs.append(prop_graph)
        # Process weighted mappings to build new mapping based on the big weights
        if bool(args.enable_weighted_mapping):
            max = 0
            core_sequence = []
            curr_relation = ""
            core_relation = ""
            for n in prop_graph.nodes(data=True):
                name = n[0]
                try:
                    w = n[1]['weight']
                    relation = n[1]['relation']
                except Exception:
                    continue
                if w >= max:
                    max = w
                    core_sequence = ([n[0].split(" ")[0].split("_")[1]], [n[0].split(" ")[1].split("_")[1]])
                    core_relation = relation
                if w == max and curr_relation == relation:
                    core_sequence[0].append(n[0].split(" ")[0].split("_")[1])
                    core_sequence[1].append(n[0].split(" ")[1].split("_")[1])

            candidates[core_relation].append(core_sequence)
        whole_candidates[prop] = candidates

    # REFACTO: it deserves it own function
    print("Starting filtering...")
    for prop in tqdm(prop_to_idx):
        selected = {
                    "B": [],
                    "M": [],
                    "O": [],
                    "F": [],
                    "S": [],
                    "E": [],
                    "D": [],
                    "BI": [],
                    "MI": [],
                    "OI": [],
                    "FI": [],
                    "SI": [],
                    "DI": []
            }
        train_indices = prop_to_idx[prop]
        try:
            candidates = whole_candidates[prop]
        except Exception:
            continue
        for k in tqdm(candidates, leave=False):
            for elt in candidates[k]:
                # selected candidates are those above the accuracy threshold
                if test_rule(train_indices, {str(k): [(elt[0], elt[1])]}, noise_ratio=float(args.noise_ratio), inclusive=bool(args.inclusive))[0] > float(args.accuracy_threshold):
                    selected[str(k)].append((elt[0], elt[1]))
        constraint_filename = os.path.join(args.constraint_folder, f"{prop}_rules.pkl")
        with open(constraint_filename, "w+b") as f:
            pickle.dump(selected, f)
