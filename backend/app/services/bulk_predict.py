BATCH_SIZE = 256


def chunks(items, size):
    """Cuts a list into pieces of at most 'size' items."""
    if size < 1:
        raise ValueError("size must be at least 1")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def predict_in_batches(predictor, reports, batch_size=BATCH_SIZE):
    """Runs the model piece by piece, so a big list does not use too much memory.

    reports: [{"id": ..., "text": ..., "project": ...}]
    Returns [(report_id, result), ...] in the same order.
    """
    pairs = []
    for batch in chunks(reports, batch_size):
        results = predictor.predict([r["text"] for r in batch], [r["project"] for r in batch])
        pairs.extend((report["id"], result) for report, result in zip(batch, results))
    return pairs
