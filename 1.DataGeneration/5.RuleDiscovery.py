import sys
import numpy as np
import pickle
import networkx as nx
from collections import Counter
from tqdm import tqdm
import itertools

sys.path.append("./..")
import TimePackage as tp
import create_network
import os

# INPUT :
#   Type

temporal_granularity = "D"
today = np.datetime64("2023-12-31", temporal_granularity)
root_data = "./../0.Data/"


def to_common_uri(uri_relation):
    namespace_common = "http://www.wikidata.org/prop/P"
    namespace_direct = "http://www.wikidata.org/prop/direct/P"
    if uri_relation[: len(namespace_direct)] == namespace_direct:
        return namespace_common + uri_relation[len(namespace_direct) :]
    else:
        return uri_relation


def processing_date_unknown_allowed(date_raw) -> np.datetime64:
    if date_raw == "None":
        return None
    else:
        return np.datetime64(date_raw, temporal_granularity)


# Find the relation that appears globally
def find_global_appiration(relation_seen, entities):

    first_appearance_of_r = {}
    ent_per_r = {}

    for r in relation_seen:
        first_appearance_of_r[r] = {}
        ent_per_r[r] = set()

        for entity in entities.values():

            timeline_r = entity.get_triples_with_r(r)
            if timeline_r != None:
                ent_per_r[r].add(entity)
                first_date = tp.ordered_timeline_of_r_mono_value_per_int(entity, r)[0][
                    1
                ]
                if not first_date in first_appearance_of_r[r]:
                    first_appearance_of_r[r][first_date] = 0
                first_appearance_of_r[r][first_date] += 1

    mini_appearance = 10
    threshold_global = 0.95

    global_relation = set()

    for r in first_appearance_of_r:

        nb_apparition = 0
        date_first = np.datetime64("2050", "Y")

        for date in first_appearance_of_r[r]:

            if date_first > date:
                nb_apparition = first_appearance_of_r[r][date]
                date_first = date

        if nb_apparition != 0:

            total_ent_alive_at_the_moment = 0

            for ent in ent_per_r[r]:
                if ent.get_lifespan().get_start() <= date_first:
                    total_ent_alive_at_the_moment += 1

        if nb_apparition > mini_appearance:
            if nb_apparition / total_ent_alive_at_the_moment > threshold_global:
                global_relation.add(r)

    return global_relation


def find_multivaluation_temporal(entities):
    multi_r = set()
    multi_r_count_kept = {}
    count_per_r = {}
    count_v_per_r = {}
    # threhsold value to allow multivaluation for a value V
    # threshold_value = 10

    for ent in entities.values():

        for r in ent.triples_per_r:

            if not r in count_v_per_r:
                count_v_per_r[r] = {}
                if not r in multi_r_count_kept:
                    multi_r_count_kept[r] = 0
                multi_r_count_kept[r] += 1

            if not r in count_per_r:
                count_per_r[r] = 0
                multi_r_count_kept[r] = 0

            count_per_r[r] += 1

            seq = tp.TimeSequence(tp.ordered_time_sequence_first_start(ent, r))
            if seq.multi_valuation_temporal:
                multi_r_count_kept[r] += 1

            for t in ent.triples_per_r[r]:
                v = t.value

                if not v in count_v_per_r[r]:
                    count_v_per_r[r][v] = 0

                count_v_per_r[r][v] += 1

    for r in count_per_r:
        if multi_r_count_kept[r] * (1 - seuil) >= count_per_r[r]:
            multi_r.add(r)

    rxv_allowed = set()
    for r in count_v_per_r:
        for v in count_v_per_r[r]:
            uri_name = "http://www.wikidata.org/entity/Q"
            if (type(v) == str) and (v[: len(uri_name)] == uri_name):
                if count_v_per_r[r][v] > mini_entity:
                    rxv_allowed.add((r, v))

    for ent in entities.values():
        ent.generate_triples_per_r_and_rxv(rxv_allowed)

    return multi_r


def generate_rules(couple, property, error_percent, coverage):

    first = None
    first_precision = None
    if type(couple[0]) == tuple:
        first = couple[0][0]
        first_precision = couple[0][1]
    else:
        first = couple[0]

    second = None
    second_precision = None
    if type(couple[1]) == tuple:
        second = couple[1][0]
        second_precision = couple[1][1]
    else:
        second = couple[1]

    if property[0] == "A":
        return tp.TemporalRule(
            first,
            first_precision,
            property[2:-2],
            second,
            second_precision,
            error_percent,
            coverage,
        )
    else:
        return tp.TemporalRule(
            second,
            second_precision,
            property[2:-2],
            first,
            first_precision,
            error_percent,
            coverage,
        )


# global variables for constraint networks and geqca compatibility
constraint_networks = []
graph_paths = []
biases = []
inter_comps = []
m = {
    "B": "PrecedesXY",
    "M": "MeetsXY",
    "O": "OverlapsXY",
    "F": "FinishXY",
    "S": "StartsXY",
    "E": "ExactXY",
    "D": "DuringXY",
    "BI": "IsPrecededXY",
    "MI": "IsMetXY",
    "OI": "IsOverlappedXY",
    "FI": "IsFinishedXY",
    "SI": "IsStartedXY",
    "DI": "ContainsXY"
}

# This function is used to compute the constraint networks and save the Time Sequences
def find_rules_only_r(entities, multivaluation_relations, global_relation, building_graph=False, geqca=False, data_analysis=False):

    comparison_per_couple_of_r = {}

    # create only k constraint networks
    k = 0
    for idx, ent in tqdm(enumerate(entities.values())):

        r = list(
            set(ent.triples_per_r.keys())
            .difference(global_relation)
            .difference(multivaluation_relations)
        )

        for i, r_1 in tqdm(enumerate(r), leave=False):
            sequence_r_1 = tp.TimeSequence(
                tp.ordered_time_sequence_first_start(ent, r_1)
            )
            if not sequence_r_1.multi_valuation_temporal:
                for r_2 in tqdm(r[i + 1 :], leave=False):
                    sequence_r_2 = tp.TimeSequence(
                        tp.ordered_time_sequence_first_start(ent, r_2)
                    )
                    # Creation of the constraint network
                    # save the value from entity.triple_per_r.values that gives the property
                    for e in ent.triples_per_r[r_1]:
                        r1_relation = e.relation
                    for e in ent.triples_per_r[r_2]:
                        r2_relation = e.relation
                    if building_graph:
                        constraint_network = create_network.create_cross_sequence_network(
                            sequence_r_1.intervals, sequence_r_2.intervals, r1_relation, r2_relation
                        )
                        # save the time sequences
                        if not os.exists(f"{r1_relation.split("/")[-1]}_TS.pkl"):
                            with open(f"TimeSequences/{r1_relation.split("/")[-1]}_TS.pkl", "w+b") as f:
                                pickle.dump(sequence_r_1, f)
                        if not os.exists(f"TimeSequences/{r2_relation.split("/")[-1]}_TS.pkl"):
                            with open(f"{r2_relation.split("/")[-1]}_TS.pkl", "w+b") as f:
                                pickle.dump(sequence_r_2, f)
                        # earliest in our wikidata taken in 2023
                        earliest = np.datetime64("2024-01-01")
                        latest = np.datetime64("-5000-01-01")
                        for i in sequence_r_1.intervals:
                            start = i.get_start()
                            end = i.get_end()
                            if start < earliest:
                                earliest = start
                            if end > latest:
                                latest = end
                        for i in sequence_r_2.intervals:
                            start = i.get_start()
                            end = i.get_end()
                            if start < earliest:
                                earliest = start
                            if end > latest:
                                latest = end
                        # multiply by 2 because that is what geqca wants as input
                        nb_vars = (len(sequence_r_1) + len(sequence_r_2)) * 2
                        print(f"Number of nodes in this constraint network: {len(constraint_network.edges())}")
                        constraint_networks.append(constraint_network)
                        biases.append((nb_vars, (earliest, latest)))
                        # save constraint networks
                        with open(f"constraint_networks/{k}_constraint_network.pkl", "w+b") as f:
                            pickle.dump(constraint_network, f)
                    k = k + 1
                    if not sequence_r_2.multi_valuation_temporal:
                        relations_between_1_2 = tp.TimeSequenceRelation(
                            r_1, r_2, sequence_r_1, sequence_r_2
                        )
                        if data_analysis:
                            tmp = list(relations_between_1_2.inter_comparison_A_to_B.values())
                            inter_comps.append(tmp)
                        name = relations_between_1_2.get_name()
                        if not name in comparison_per_couple_of_r:
                            comparison_per_couple_of_r[name] = set()
                        comparison_per_couple_of_r[name].add(relations_between_1_2)

    props_per_couple = {}
    for r_1, r_2 in comparison_per_couple_of_r:
        props_per_couple[(r_1, r_2)] = {
            "total": len(comparison_per_couple_of_r[(r_1, r_2)])
        }
        for tsr in comparison_per_couple_of_r[(r_1, r_2)]:
            for props_r_1_o_r_2 in tsr.A_o_B:
                name_props = "A " + props_r_1_o_r_2 + " B"
                if not name_props in props_per_couple[(r_1, r_2)]:
                    props_per_couple[(r_1, r_2)][name_props] = 0
                props_per_couple[(r_1, r_2)][name_props] += 1

            for props_r_1_o_r_2 in tsr.B_o_A:
                name_props = "B " + props_r_1_o_r_2 + " A"
                if not name_props in props_per_couple[(r_1, r_2)]:
                    props_per_couple[(r_1, r_2)][name_props] = 0
                props_per_couple[(r_1, r_2)][name_props] += 1

    rules = set()

    for couple in props_per_couple:
        total = props_per_couple[couple]["total"]

        if total > mini_entity:
            for property in set(props_per_couple[couple].keys()).difference(["total"]):
                if props_per_couple[couple][property] > total * seuil:
                    rules.add(
                        generate_rules(
                            couple,
                            property,
                            props_per_couple[couple][property] / total,
                            total,
                        )
                    )
    return rules


def verify_comparison_allowed(r_1, r_2):
    if (type(r_1) == type("")) and (type(r_2) == type("")):
        return r_1 != r_2
    elif type(r_1) == type(""):
        return r_1 != r_2[0]
    elif type(r_2) == type(""):
        return r_1[0] != r_2
    else:
        return (r_1[0] != r_2[0]) or (r_1[1] != r_2[1])


def find_rules_r_and_rxv(entities, multivaluation_relations, global_relation):
    comparison_per_couple_of_r = {}

    for ent in entities.values():
        # print(ent)

        r = list(
            set(ent.triples_per_r_and_rxv.keys())
            .difference(global_relation)
            .difference(multivaluation_relations)
        )

        for i, r_1 in enumerate(r):
            # print(r_1)
            sequence_r_1 = tp.TimeSequence(
                tp.ordered_time_sequence_first_start_with_rxv(ent, r_1)
            )
            if not sequence_r_1.multi_valuation_temporal:
                for r_2 in r[i + 1 :]:
                    if verify_comparison_allowed(r_1, r_2):
                        sequence_r_2 = tp.TimeSequence(
                            tp.ordered_time_sequence_first_start_with_rxv(ent, r_2)
                        )

                        if not sequence_r_2.multi_valuation_temporal:
                            relations_between_1_2 = tp.TimeSequenceRelation(
                                str(r_1), str(r_2), sequence_r_1, sequence_r_2
                            )
                            name = relations_between_1_2.get_name()
                            if not name in comparison_per_couple_of_r:
                                comparison_per_couple_of_r[name] = set()
                            comparison_per_couple_of_r[name].add(relations_between_1_2)

    props_per_couple = {}
    for r_1, r_2 in comparison_per_couple_of_r:
        props_per_couple[(r_1, r_2)] = {
            "total": len(comparison_per_couple_of_r[(r_1, r_2)])
        }
        for tsr in comparison_per_couple_of_r[(r_1, r_2)]:
            for props_r_1_o_r_2 in tsr.A_o_B:
                name_props = "A " + props_r_1_o_r_2 + " B"
                if not name_props in props_per_couple[(r_1, r_2)]:
                    props_per_couple[(r_1, r_2)][name_props] = 0
                props_per_couple[(r_1, r_2)][name_props] += 1

            for props_r_1_o_r_2 in tsr.B_o_A:
                name_props = "B " + props_r_1_o_r_2 + " A"
                if not name_props in props_per_couple[(r_1, r_2)]:
                    props_per_couple[(r_1, r_2)][name_props] = 0
                props_per_couple[(r_1, r_2)][name_props] += 1

    rules = set()

    for couple in props_per_couple:
        total = props_per_couple[couple]["total"]

        if total > mini_entity:
            for property in set(props_per_couple[couple].keys()).difference(["total"]):
                if props_per_couple[couple][property] > total * seuil:
                    rules.add(
                        generate_rules(
                            couple,
                            property,
                            props_per_couple[couple][property] / total,
                            total,
                        )
                    )

    return rules


if __name__ == "__main__":

    type_entity = sys.argv[1]
    percentage_entity = int(sys.argv[2])
    seuil = float(sys.argv[3])
    building_graph = bool(sys.argv[4])
    geqca = bool(sys.argv[5])
    data_analysis = bool(sys.argv[6])
    entities = {}
    relation_seen = set()

    with open(
        f"{root_data}{type_entity}/train_cst_knowledge.quintuplet",
        "r",
        encoding="UTF-8",
    ) as f_read:
        for line in f_read.readlines():
            head, relation, value, start, end = line[:-1].split("\t")

            relation = to_common_uri(relation)

            if not head in entities:
                entities[head] = tp.Entity(head, today, temporal_granularity)

            entities[head].add_triple(
                tp.Triple(
                    head,
                    relation,
                    value,
                    tp.Interval(
                        processing_date_unknown_allowed(start),
                        processing_date_unknown_allowed(end),
                    ),
                )
            )

            relation_seen.add(relation)

    mini_entity = max(1, len(entities) * (int(percentage_entity) / 100))

    global_relation = set()  # find_global_appiration(relation_seen, entities)

    multivaluation_relations = find_multivaluation_temporal(entities)

    rules_r = find_rules_only_r(entities, multivaluation_relations, global_relation, building_graph)
    rules_clean = tp.remove_useless_complex_rules(rules_r)
    # with open(f"{root_data}{type_entity}/Rules_R_{percentage_entity}_{seuil}.txt", "w", encoding="UTF-8") as f:
    #     for rule in rules_clean:
    #         f.write(str(rule)+"\n")

    with open(
        f"{root_data}{type_entity}/Rules_R_{percentage_entity}_{seuil}.tsv",
        "w",
        encoding="UTF-8",
    ) as f:
        for rule in rules_clean:
            f.write(rule.to_tsv() + "\n")

    rules_r_and_rxv = find_rules_r_and_rxv(
        entities, multivaluation_relations, global_relation
    )
    rules_clean = tp.remove_useless_complex_rules(rules_r_and_rxv)
    # with open(f"{root_data}{type_entity}/Rules_RxV_{percentage_entity}_{seuil}.txt", "w", encoding="UTF-8") as f:
    #     for rule in rules_clean:
    #         f.write(str(rule)+"\n")

    with open(
        f"{root_data}{type_entity}/Rules_RxV_{percentage_entity}_{seuil}.tsv",
        "w",
        encoding="UTF-8",
    ) as f:
        for rule in rules_clean:
            f.write(rule.to_tsv() + "\n")

    # X is meant to perform data analysis on the matrics of relations between sequences
    X = np.array(inter_comps)
    with open("inter_dist.pkl", "w+b") as f:
        pickle.dump(X, f)
    m = {
        "B": "PrecedesXY",
        "M": "MeetsXY",
        "O": "OverlapsXY",
        "F": "FinishXY",
        "S": "StartsXY",
        "E": "ExactXY",
        "D": "DuringXY",
        "BI": "IsPrecededXY",
        "MI": "IsMetXY",
        "OI": "IsOverlappedXY",
        "FI": "IsFinishedXY",
        "SI": "IsStartedXY",
        "DI": "ContainsXY"
    }
    if geqca:
        # Don't forget to delete bias and target before launch !
        for k, constraint_network in enumerate(constraint_networks):
            # with open(f"{k}_constraint_network.pkl", "w+b") as f:
            #     pickle.dump(constraint_network, f)
            gamma = list(m.values())
            index_map = {}
            index = 0
            seen_edges = set()
            for e in constraint_network.edges.data("constraint", default=""):
                # seen_deges to avoid adding mirror edges
                if (e[0], e[1]) in seen_edges or (e[1], e[0]) in seen_edges:
                    continue
                seen_edges.add((e[0], e[1]))
                gamma.add(m[str(e[2])])
                if e[0] in list(index_map.keys()):
                    origin_name = index_map[e[0]]
                else:
                    origin_name = index
                    index_map[e[0]] = index
                    index += 1
                if e[1] in list(index_map.keys()):
                    dest_name = index_map[e[1]]
                else:
                    dest_name = index
                    index_map[e[1]] = index
                    index += 1
                with open(f"constraint_network/{k}_network.target", "a+") as f:
                    f.write(f"{m[str(e[2])]} {origin_name} {dest_name}\n")
            with open(f"constraint_network/{k}_network.bias", "a+") as g:
                g.write(f"nbVars {biases[k][0]}\n")
                nb_days = np.datetime64(biases[k][1][1]) - np.datetime64(biases[k][1][0])
                # getting just the number of day from timedelta type
                nb_days = nb_days / np.timedelta64(1, 'D')
                g.write(f"domainSize 0 {int(nb_days)}\n\n")
                g.write("Gamma\n")
                # TODO: Must put all Allen relations now !
                for i in gamma:
                    g.write(f"{i}\n")
