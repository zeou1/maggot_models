import json

import numpy as np
import pandas as pd

from graspy.simulations import p_from_latent, sample_edges, sbm


def hardy_weinberg(theta):
    """
    Maps a value from [0, 1] to the hardy weinberg curve.
    """
    hw = [theta ** 2, 2 * theta * (1 - theta), (1 - theta) ** 2]
    return np.array(hw).T


def gen_hw_graph(n_verts):
    thetas = np.random.uniform(0, 1, n_verts)
    latent = hardy_weinberg(thetas)
    p_mat = p_from_latent(latent, rescale=False, loops=False)
    graph = sample_edges(p_mat, directed=True, loops=False)
    return (graph, p_mat)


def compute_rss(estimator, graph):
    """Computes RSS, matters whether the estimator is directed
    
    Parameters
    ----------
    estimator : graspy estimator object
        [description]
    graph : nparray
        [description]
    
    Returns
    -------
    [type]
        [description]
    """
    graph = graph.copy()
    p_mat = estimator.p_mat_.copy()
    if not estimator.directed:
        inds = np.triu_indices_from(p_mat)
        p_mat = p_mat[inds]
        graph = graph[inds]
    diff = (p_mat - graph) ** 2
    rss = np.sum(diff)
    return rss


def compute_mse(estimator, graph):
    """
    Matters whether the estimator is directed
    """
    rss = compute_rss(estimator, graph)
    if not estimator.directed:  # TODO double check that this is right
        size = graph.shape[0] * (graph.shape[0] - 1) / 2
    else:
        size = graph.size - graph.shape[0]
    return rss / size


def compute_log_lik(estimator, graph, c=0):
    """This is probably wrong right now"""
    p_mat = estimator.p_mat_.copy()
    graph = graph.copy()
    inds = np.triu_indices(graph.shape[0])
    p_mat = p_mat[inds]
    graph = graph[inds]

    p_mat[p_mat < c] = c
    p_mat[p_mat > 1 - c] = 1 - c
    successes = np.multiply(p_mat, graph)
    failures = np.multiply((1 - p_mat), (1 - graph))
    likelihood = successes + failures
    return np.sum(np.log(likelihood))


def _n_to_labels(n):
    n_cumsum = n.cumsum()
    labels = np.zeros(n.sum(), dtype=np.int64)
    for i in range(1, len(n)):
        labels[n_cumsum[i - 1] : n_cumsum[i]] = i
    return labels


def gen_B(n_blocks, a=0.1, b=0.2, assortivity=4):
    B_mat = np.random.uniform(a, b, size=(n_blocks, n_blocks))
    B_mat -= np.diag(np.diag(B_mat))
    B_mat += np.diag(np.random.uniform(assortivity * a, assortivity * b, size=n_blocks))
    return B_mat


def gen_sbm(n_verts, n_blocks, B_mat):
    ps = np.array(n_blocks * [1 / n_blocks])
    n_vec = np.random.multinomial(n_verts, ps)
    graph = sbm(n_vec, B_mat, directed=False, loops=False)
    labels = _n_to_labels(n_vec)
    return graph, labels


def run_to_df(file_path):
    out = get_json(file_path)
    result = out["result"]
    if "py/tuple" in result:
        dfs = []
        for elem in result["py/tuple"]:
            df = pd.DataFrame.from_dict(elem["values"])
            dfs.append(df)
        return dfs
    else:
        return pd.DataFrame.from_dict(result["values"])


def get_json(file_path):
    f = open(str(file_path), mode="r")
    out = json.load(f)
    f.close()
    return out
