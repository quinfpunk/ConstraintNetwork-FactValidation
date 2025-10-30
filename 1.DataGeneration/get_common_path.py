from collections import Counter
import os
import pickle

if __name__ == "__main__":
    graph_paths = []
    for i in range(50):
        if os.path.exists(f"{i}_graph_path.pkl"):
            with open(f"{i}_graph_path.pkl", "rb") as f:
                graph_paths.append(pickle.load(f))
    # all_graph_paths = [ i[0] for i in graph_paths]
    all_graph_paths = graph_paths
    occ_dict = {}
    print(all_graph_paths[0])
    for a in all_graph_paths:
        if str(a) in occ_dict.keys():
            occ_dict[str(a)] += 1
        else:
            occ_dict[str(a)] = 1
        # for i in a:
        #     try:
        #         occ_dict[i[0]] += 1
        #     except Exception:
        #         occ_dict[i[0]] = 1
    print(occ_dict)
    # print(tuple(all_graph_paths))
    c = Counter((all_graph_paths))
    print(f"number of graph path that are repeated: {c.total()}")
    with open("graph_path_counter.txt", "w+") as f:
        f.write(f"number of graph path that are repeated: {c.total()}")
