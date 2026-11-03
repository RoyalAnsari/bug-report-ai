import numpy as np


def normalize_rows(vectors):
    """Har row ki length 1 kar deta hai, taake dot product = cosine similarity ho."""
    vectors = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def top_k_similar(query_emb, corpus_emb, k=5, threshold=0.0, query_indices=None, chunk_size=256):
    """
    Har query ke liye top-k sab se milte julte reports dhoondta hai.

    query_emb, corpus_emb: normalized embeddings (cosine similarity = dot product).
    threshold: isse kam similarity wale candidates nahi aate.
    query_indices: agar query corpus ka hissa hai to uski apni index, taake khud ko match na kare.
    Wapas deta hai: har query ke liye [(corpus_index, cosine_similarity), ...], zyada se kam.
    """
    query_emb = np.asarray(query_emb, dtype=np.float32)
    corpus_emb = np.asarray(corpus_emb, dtype=np.float32)
    k = min(k, len(corpus_emb))
    results = []

    for start in range(0, len(query_emb), chunk_size):
        block = query_emb[start : start + chunk_size]
        sims = block @ corpus_emb.T
        if query_indices is not None:
            for row, index in enumerate(query_indices[start : start + chunk_size]):
                sims[row, index] = -np.inf

        for row in sims:
            if k < len(row):
                top = np.argpartition(-row, k - 1)[:k]
            else:
                top = np.arange(len(row))
            top = top[np.argsort(-row[top])]
            results.append(
                [
                    (int(i), float(row[i]))
                    for i in top
                    if np.isfinite(row[i]) and row[i] >= threshold
                ]
            )
    return results