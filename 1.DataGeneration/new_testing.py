import pickle
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from pprint import pprint
import sys

def verify_constraint_noise(seq, cons, noise_ratio=0.35):
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

def check(constraints_network, rules):
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
    nb_inervals = 0
    for cons_net in constraints_network:
        nb_intervals = len(cons_net.nodes())
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
                    # split by underscore and take the number part,
                    # this will allow us to compare sequences for partial values
                    bij[key][i][j] = string.split("_")[1]
    # TODO: check that this is working properly
    done = False
    for b in bij:
        charac = bij[b]
        if b not in rules.keys():
            continue
        p1, p2 = bij[b][0], bij[b][1]
        rule = rules[b]
        for r in rule:
            # print("p1", p1)
            # print("r", r[0])
            if len(p1) != 0 and verify_constraint_noise(p1, r[0], noise_ratio=0.05): # and p1 == r[0]: 
                if len(p2) != 0 and verify_constraint_noise(p2, r[1], noise_ratio=0.05): #  and p2 == r[1]:  
                    # if ''.join(p2) in ''.join(r[1]):
                    # print(f"{b} {r}")
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
    if prop != "":
        if accuracy == 0:
            print(f"For {prop} accuracy: {accuracy} no rules has been extracted")
        else:
            print(f"For {prop} accuracy is: {accuracy}")
    # accuracies[(p1, p2)] = accuracy
    return accuracy, coverage, rules_usage

def test_rule(test_indices, rules, prop="", accuracy=True, coverage=False):
    """
       brief: for a given rule test it on the provided indices
    """
    verified = 0
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
        with open(f"{cons_net_id}_constraint_network.pkl", "rb") as f:
            cons_net = pickle.load(f)
            nb_intervals = len(cons_net.nodes())
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
                        # split by underscore and take the number part,
                        # this will allow us to compare sequences for partial values
                        bij[key][i][j] = string.split("_")[1]
        # TODO: check that this is working properly
        done = False
        for b in bij:
            charac = bij[b]
            if b not in rules.keys():
                continue
            p1, p2 = bij[b][0], bij[b][1]
            rule = rules[b]
            for r in rule:
                # print("p1", p1)
                # print("r", r[0])
                if ''.join(p1) in ''.join(r[0]):
                    if ''.join(p2) in ''.join(r[1]):
                        if len(r[0]) >= 2:
                            # print(f"{b} {r}")
                            verified += 1
                            done = True
                            break
            if done:
                break
    accuracy = verified / len(test_indices)
    if prop != "":
        if done:
            return accuracy
            # print(f"For {prop} accuracy is: {verified / len(test_indices)}")
        else:
            # print(f"For {prop} accuracy no rules has been extracted")
            if accuracy:
                return accuracy
            else:
                return 0
    # accuracies[(p1, p2)] = accuracy
    return accuracy

def benchmark(rule_dir: str, prop_to_idx):
    accuracies = []
    coverages = []
    bad_accuracies = []
    bad_coverages = []
    old_test_indices = []
    for prop in prop_to_idx:
        test_indices = prop_to_idx[prop]
        rules = {}
        try:
            with open(f'{rule_dir}/{prop}_rules.pkl', "rb") as f:
                rules = pickle.load(f)
        except Exception:
            print(f"No rule exist for {prop}")
            continue
        acc = test_rule(test_indices, rules, prop)
        if acc != 0:
            accuracies.append(acc)
        cov = test_rule(test_indices, rules, prop, accuracy=False, coverage=True)
        coverages.append(cov)
        if len(old_test_indices) != 0:
            bad_acc = test_rule(old_test_indices, rules, "bad" + str(prop))
            if bad_acc != 0:
                bad_accuracies.append(bad_acc)
            bad_cov = test_rule(old_test_indices, rules, "bad" + str(prop), accuracy=False, coverage=True)
            bad_coverages.append(bad_cov)
        old_test_indices = test_indices
    print(f"| Mean Accuracies {np.mean(np.array(accuracies))}+-{np.std(np.array(accuracies))}", end=" | ")
    print(f"Mean Coverage {np.mean(np.array(coverages))}+-{np.std(np.array(coverages))}", end=" | ")
    print(f"Mean bad Accuracies {np.mean(np.array(bad_accuracies))}+-{np.std(np.array(bad_accuracies))}", end=" | ")
    print(f"Mean bad Coverage {np.mean(np.array(bad_coverages))}+-{np.std(np.array(bad_coverages))}", end=" |\n")

if __name__ == "__main__":

    accuracy_threshold = 0.8
    test_indices = [i for i in range(2000)]
    prop_to_idx = defaultdict(list)
    for idx, cons_net_id in tqdm(enumerate(test_indices), leave=False):
        with open(f"{cons_net_id}_constraint_network.pkl", "rb") as f:
            cons_net = pickle.load(f)
            nodes = list(cons_net.nodes())
            if len(nodes) == 0:
                print("empty")
                continue
            p1 = nodes[0].split("/")[-1].split('_')[0]
            # if not ('P' in p1 or 'Q' in p1):
            #     print(p1)
            #     print(test_indices[idx])
            #     continue
            p2 = None
            for n in nodes:
                t = n.split("/")[-1].split('_')[0]
                if t != p1 and ('P' in t or 'Q' in t):
                    p2 = t
                    break
            if p2 is None:
                continue
            prop_to_idx[(p1, p2)].append(cons_net_id)
    if sys.argv[1] == "bench":
        benchmark("rules", prop_to_idx)
        exit()
    for prop in tqdm(prop_to_idx):
        verified_rule = {
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
        test_indices = prop_to_idx[prop]
        rules = {}
        try:
            with open(f'rules/{prop}_candidate.pkl', "rb") as f:
                rules = pickle.load(f)
        except Exception:
            continue
        for r in rules:
            for cand in rules[r]:
                acc = test_rule(test_indices, {r: [cand]}, prop)
                if acc > accuracy_threshold:
                    verified_rule[r].append(cand)
    with open(f"rules_final/{prop}_rules.pkl", "w+b") as f:
        if sum([len(i) for i in verified_rule.values()]) != 0:
            pickle.dump(verified_rule, f)



