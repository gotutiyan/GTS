def export_w_file(weighted_gold_chunks: list, file_name: str) -> None:
    if '.' not in file_name:
        file_name += '.txt'
    out_fp = open(file_name, "w")
    out_fp.write(str(len(weighted_gold_chunks[0][0].sys2eval)) + '\n')
    for gold_chunk in weighted_gold_chunks:
        weights = []
        for gchunk in gold_chunk:
            weights.append(str(gchunk.n_correct))
        out_fp.write(' '.join(weights) + '\n')
    out_fp.close()
    return


def import_w_file(file_path: str):
    number_of_system, *weights_list\
        = open(file_path).read().rstrip().split('\n')
    number_of_system = int(number_of_system)
    for i in range(len(weights_list)):
        weights_list[i] = list(map(int, weights_list[i].rstrip().split(' ')))
    return weights_list, number_of_system


def set_weight(gold_chunks: list, w_file_path: str, a: float, b: float, c: float) -> list:
    weights_list, number_of_system = import_w_file(w_file_path)
    for sent_id, gold_chunk in enumerate(gold_chunks):
        for chunk_id, gchunk in enumerate(gold_chunk):
            gchunk.n_correct = int(weights_list[sent_id][chunk_id])
            gchunk.weight = gchunk.weight_f(gchunk.n_correct, number_of_system, a, b, c)
    return gold_chunks
