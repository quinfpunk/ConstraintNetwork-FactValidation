from tqdm import tqdm
import pickle
from collections import defaultdict
from testing import test_rule
import os
from TimePackage import *
from create_network import create_cross_sequence_network

if __name__ == "__main__":
    def insert_and_validate_facts(facts, sequences, rules, test_indices=[i for i in range(10_000)]):
        """
            @brief: For all sequences insert the fact then validate it
        """
        time_sequences = []
        all_time_sequences = []
        all_properties = []
        for filename in os.listdir("TimeSequences"):
            if filename.split("_")[0] in facts["properties"]:
                with open(filename, 'rb') as f:
                    ts = pickle.load(f)
                    time_sequences.append(ts)
            else:
                with open(filename, 'rb') as f:
                    ts = pickle.load(f)
                    all_time_sequences.append(ts)
                    all_properties.append(filename.split("_")[0])
        constraint_networks = []
        for ts in time_sequences:
            # add facts to each time sequence
            fact_interval = Interval(facts["start"], facts["end"])
            # very naive insertion
            ts.intervals.append(fact_interval)
            for idx, second_ts in enumerate(all_time_sequences):
                constraint_network = create_network.create_cross_sequence_network(
                    ts.intervals, second_ts.intervals, facts["properties"], all_properties[idx]
                )
                constraint_networks.append(constraint_network)


        prop_to_idx = defaultdict(list)
        for cons_net in constraint_networks:
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
            if p1 in facts["properties"] or p2 in facts["properties"]:
                prop_to_idx[(p1, p2)].append(cons_net_id)
        return check(constraint_networks, rules)[0]
        # The number should be used as a score (1 -> True) (0 -> False) (other -> score)


