import pickle
from tqdm import tqdm
from collections import defaultdict
import numpy as np
import argparse
import os

def verify_constraint_noise(seq, cons, noise_ratio=0.05):
    """
       @brief: Verify that the seq in input is equal to the cons allowing
           noise
       @params:
           seq: a list of intervals
           cons: a list of intervals
           noise_ratio: the allowed ratio of noise
    """
    i = 0
    j = 0
    noise = 0
    while (i < len(seq) and j < len(cons)):
        if seq[i] == cons[j]:
            i += 1
            j += 1
        else:
            i += 1
            noise += 1
    noise = noise / len(seq)
    if noise > noise_ratio:
        return False
    return True


def check(constraints_network, rules, prop="", noise_ratio=0, inclusive=False):
    """
        @brief: used for validation this function takes a list of constraint networks (with the added fact (s,p,o,t))
            and check that the mappings are found (allowing some noise or not)
        @params:
            constraint_networks: list of constraint networks (in the current usage it is expected that they have an added fact)
            rules: dictionary of mappings found during discovery
            inclusive: boolean to allow inclusion
    """
    at_least_one = 0
    tmp_acc = 0
    cov = len(test_indices)
    verified = 0
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
    # save bij for further comparison between each other for partial validation
    # and rule inference from number of occurence
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
    for cons_net in constraints_network:
        for edg in tqdm(cons_net.edges().data("constraint", default=""), leave=False):
            if edg[0].split('_')[0] == edg[1].split('_')[0]:
                continue
            else:
                p1 = edg[0].split('/')[-1].split('_')[0]
                p2 = edg[1].split('/')[-1].split('_')[0]
            m[str(edg[2])].append((edg[0], edg[1]))
            if p1 in edg[0]:
                A_term = edg[0].split('/')[-1]
                B_term = edg[1].split('/')[-1]
            else:
                A_term = edg[1].split('/')[-1]
                B_term = edg[0].split('/')[-1]
            bij[str(edg[2])][0].append(A_term)
            bij[str(edg[2])][1].append(B_term)
        # replace values to only their numbers
        for key in bij:
            for i, sublist in enumerate(bij[key]):
                for j, string in enumerate(sublist):
                    # split by underscore and take the number part
                    bij[key][i][j] = string.split("_")[1]
    done = False
    for b in bij:
        if b not in rules.keys():
            continue
        p1, p2 = bij[b][0], bij[b][1]
        rule = rules[b]
        for r in rule:
            if not inclusive:
                if len(p1) != 0 and verify_constraint_noise(p1, r[0], noise_ratio=noise_ratio): 
                    if len(p2) != 0 and verify_constraint_noise(p2, r[1], noise_ratio=noise_ratio):
                        verified += 1
                        if not done:
                            at_least_one += 1
                        done = True
            else:
                if ''.join(p1) in ''.join(r[0]):
                    if ''.join(p2) in ''.join(r[1]):
                        verified += 1
                        if not done:
                            at_least_one += 1
                        done = True
        if len(rule):
            tmp_acc += verified / len(rules[b])
    tmp_acc /= len(list(rules.keys()))
    if not done:
        cov -= 1

    rules_usage = tmp_acc / len(constraints_network)
    coverage = cov / len(constraints_network)
    accuracy = at_least_one / len(constraints_network)
    # prop should always be defined
    if accuracy == 0:
        print(f"For {prop} accuracy: {accuracy} no rules has been extracted")
    else:
        print(f"For {prop} accuracy is: {accuracy}")
    # In validation accuracy is the truthfulness score
    return accuracy, coverage, rules_usage

def test_rule(test_indices, rules, prop="", noise_ratio=0.05, inclusive=False):
    """
        @brief: used for validation this function takes a list of indices
            and check that the mappings are found (allowing some noise or not)
        @params:
            test_indices: list of indices corresponding to constraint networks files
            rules: dictionary of mappings found during discovery
            prop: The pair of properties being tested
            noise_ratio: the allowed noise ratio
            inclusive: boolean to allow inclusion
    """
    # prepare the variables to compute the metrics
    verified = 0
    at_least_one = 0
    tmp_acc = 0
    cov = len(test_indices)
    for cons_net_id in tqdm(test_indices, leave=False):
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
        # save bij for further comparison between each other for partial validation
        # and rule inference from number of occurence
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
        # get the constraint network associated with the indice
        with open(f"{cons_net_id}_constraint_network.pkl", "rb") as f:
            cons_net = pickle.load(f)
            nb_intervals = len(cons_net.nodes())
            for edg in tqdm(cons_net.edges().data("constraint", default=""), leave=False):
                # Split the terms to have only the properties identifiers
                if edg[0].split('_')[0] == edg[1].split('_')[0]:
                    continue
                else:
                    p1 = edg[0].split('/')[-1].split('_')[0]
                    p2 = edg[1].split('/')[-1].split('_')[0]
                m[str(edg[2])].append((edg[0], edg[1]))
                if p1 in edg[0]:
                    A_term = edg[0].split('/')[-1]
                    B_term = edg[1].split('/')[-1]
                else:
                    A_term = edg[1].split('/')[-1]
                    B_term = edg[0].split('/')[-1]
                bij[str(edg[2])][0].append(A_term)
                bij[str(edg[2])][1].append(B_term)
            # replace values to only their numbers
            for key in bij:
                for i, sublist in enumerate(bij[key]):
                    for j, string in enumerate(sublist):
                        # split by underscore and take the number part,
                        # this will allow us to compare sequences for partial values
                        bij[key][i][j] = string.split("_")[1]
        done = False
        for b in bij:
            if b not in rules.keys():
                continue
            p1, p2 = bij[b][0], bij[b][1]
            rule = rules[b]
            for r in rule:
                if not inclusive:
                    if len(p1) != 0 and verify_constraint_noise(p1, r[0], noise_ratio=noise_ratio): 
                        if len(p2) != 0 and verify_constraint_noise(p2, r[1], noise_ratio=noise_ratio):
                            verified += 1
                            if not done:
                                at_least_one += 1
                            done = True
                else:
                    if ''.join(p1) in ''.join(r[0]):
                        if ''.join(p2) in ''.join(r[1]):
                            verified += 1
                            if not done:
                                at_least_one += 1
                            done = True
            if len(rule):
                tmp_acc += verified / len(rules[b])
        tmp_acc /= len(list(rules.keys()))
        if not done:
            cov -= 1

    rules_usage = tmp_acc / len(test_indices)
    coverage = cov / len(test_indices)
    accuracy = at_least_one / len(test_indices)
    # prop should always be defined
    if accuracy == 0:
        print(f"For {prop} accuracy: {accuracy} no rules has been extracted")
    else:
        print(f"For {prop} accuracy is: {accuracy}")
    return accuracy, coverage, rules_usage


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Constraint network fact validation testing',
                    description='Test the constaint discovered and saved in the associated folder',
                    epilog='Contact Timothée Strouk <timothee.strouk@student-cs.fr> for any questions ;)')
    parser.add_argument("--cons_net_folder")
    parser.add_argument("--constraints_folder")
    parser.add_argument("--noise_rate")
    parser.add_argument("--inclusive")
    args = parser.parse_args()
    # TODO: Test on more data, not in parameter because it should always be full dataset except in development
    test_indices = [i for i in range(2000, 4000)]
    prop_to_idx = defaultdict(list)
    for idx, cons_net_id in tqdm(enumerate(test_indices), leave=False):
        cons_net_filename = os.path.join(args.cons_net_folder, f"{cons_net_id}_constraint_network.pkl")
        with open(cons_net_filename, "rb") as f:
            cons_net = pickle.load(f)
            nodes = list(cons_net.nodes())
            if len(nodes) == 0:
                print("empty")
                continue
            p1 = nodes[0].split("/")[-1].split('_')[0]
            p2 = None
            for n in nodes:
                t = n.split("/")[-1].split('_')[0]
                if t != p1 and ('P' in t or 'Q' in t):
                    p2 = t
                    break
            if p2 is None:
                continue
            prop_to_idx[(p1, p2)].append(cons_net_id)

    # metrics we compute
    accuracies = []
    coverages = []
    bad_accuracies = []
    bad_coverages = []
    # Rules usage is the ratio of rules that are validated by a fact
    # (ideally all rules should be validated by a constraint networks with the same associated properties)
    rules_usages = []
    bad_rules_usages = []
    old_test_indices = test_indices
    for prop in prop_to_idx:
        test_indices = prop_to_idx[prop]
        rules = {}
        try:
            constraint_filename = os.path.join(args.constraints_folder, f"{prop}_rules.pkl")
            with open(constraint_filename, "rb") as f:
                rules = pickle.load(f)
        except Exception:
            continue
        acc, cov, rules_usage = test_rule(test_indices, rules, prop, noise_ratio=float(args.noise_ratio), inclusive=bool(args.inclusive))
        if acc != 0:
            accuracies.append(acc)
        coverages.append(cov)
        rules_usages.append(rules_usage)
        if len(old_test_indices) != 0:
            other_prop_indices = []
            for i in old_test_indices:
                if i not in test_indices:
                    other_prop_indices.append(i)
            # Test the rules on all other indices to see if rules validate constraint networks
            # that do not match their associated properties
            bad_acc, bad_cov, rules_usage = test_rule(other_prop_indices, rules, "bad" + str(prop), noise_ratio=float(args.noise_ratio), inclusive=bool(args.inclusive))
            if bad_acc != 0:
                bad_accuracies.append(bad_acc)
            bad_coverages.append(bad_cov)
            bad_rules_usages.append(rules_usage)
    # This printing format allow to copy past to markdown easily (a wrapper might be interesting)
    print(f"| Mean Accuracies {np.mean(np.array(accuracies))}+-{np.std(np.array(accuracies))}", end=" | ")
    print(f"Mean Coverage {np.mean(np.array(coverages))}+-{np.std(np.array(coverages))}", end=" | ")
    print(f"Mean Rule usage {np.mean(np.array(coverages))}+-{np.std(np.array(coverages))}", end=" | ")
    print(f"Mean bad Accuracies {np.mean(np.array(bad_accuracies))}+-{np.std(np.array(bad_accuracies))}", end=" | ")
    print(f"Mean bad Coverage {np.mean(np.array(bad_coverages))}+-{np.std(np.array(bad_coverages))}", end=" |\n")
    print(f"Mean bad Rule usage {np.mean(np.array(coverages))}+-{np.std(np.array(coverages))}", end=" | ")
    print(f"Max bad Accuracies {np.max(np.array(bad_accuracies))}", end=" | ")
    print(f"Max bad Coverage {np.max(np.array(bad_coverages))}", end=" |\n")

