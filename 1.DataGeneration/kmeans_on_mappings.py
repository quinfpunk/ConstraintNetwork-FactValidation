import pickle
import sklearn
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np
from sklearn.metrics.pairwise import pairwise_distances_argmin
if __name__ == "__main__":
    # WARNING: You should save the X from dsicovery to use this script !
    """
        KMeans on the mapping. Maybe it would be fun to do some histogram
        to see what our average mapping looks like
    """
    with open("data.pkl", "rb") as f:
        X = pickle.load(f)
    # print(X)
    for k in X:
        inertias = []
        tmp_X = np.array(X[k])
        for c in range(1, 5):

            reduced_X = PCA(n_components=2).fit_transform(tmp_X)
            kmeans = KMeans(n_clusters=c, random_state=0, n_init="auto").fit(reduced_X)
            n_clusters = kmeans.n_clusters
            k_means_cluster_centers = kmeans.cluster_centers_

            k_means_labels = pairwise_distances_argmin(tmp_X, k_means_cluster_centers)
            import matplotlib.pyplot as plt

            fig = plt.figure(figsize=(8, 3))
            fig.subplots_adjust(left=0.02, right=0.98, bottom=0.05, top=0.9)
            colors = ["#4EACC5", "#FF9C34", "#4E9A06"]

            # KMeans
            ax = fig.add_subplot(1, 3, 1)
            for k, col in zip(range(n_clusters), colors):
                my_members = k_means_labels == k
                cluster_center = k_means_cluster_centers[k]
                ax.plot(tmp_X[my_members, 0], tmp_X[my_members, 1], "w", markerfacecolor=col, marker=".")
                ax.plot(
                    cluster_center[0],
                    cluster_center[1],
                    "o",
                    markerfacecolor=col,
                    markeredgecolor="k",
                    markersize=6,
                )
            ax.set_title("KMeans")
            ax.set_xticks(())
            ax.set_yticks(())
            plt.text(-3.5, 1.8, "train time: %.2fs\ninertia: %f" % (0, kmeans.inertia_))
            plt.show()
            inertias.append(kmeans.inertia_)
        print(inertias)
        plt.plot(inertias)
        plt.show()
