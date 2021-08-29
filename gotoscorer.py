import argparse
import os
import random
from operator import itemgetter
from scripts import chunker, alignmenter, toolbox, heatmap, w_file, infobox

def main(args):
    print('Generating chunks...')
    gold_chunks = chunker.generate_chunk_from_m2(args.ref, annotator_id=args.ref_id)
    if gold_chunks == -1:
        raise ValueError('The -ref_id is invalid.')
    system_chunks = chunker.generate_system_chunks(args.hyp)
    assert(len(gold_chunks) == len(system_chunks[0]))
    # print('Number of sentences: {}'.format(len(gold_chunks)))
    print('Number of systems: {}'.format(len(system_chunks)))
    print('Scoring systems...')
    scored_gold_chunk = alignmenter.evaluate(gold_chunks, system_chunks)
    if args.w_file:
        weighted_gold_chunks = w_file.set_weight(gold_chunks, args.w_file, args.a, args.b, args.c)
    else:
        weighted_gold_chunks = calculate_weight(scored_gold_chunk, args.a, args.b, args.c)
    scores = calculate_system_score(weighted_gold_chunks, len(system_chunks), args.no_weight)
    show_score(scores, args)

    if args.heat_map:
        heatmap.generate_heatmap(weighted_gold_chunks, args.heat_map)
    if args.gen_w_file:
        w_file.export_w_file(weighted_gold_chunks, args.gen_w_file)
    if args.chunk_visualizer:
        toolbox.chunk_visualizer(weighted_gold_chunks, args.chunk_visualizer)
    if args.cat:
        try: 
            assert(1 <= args.cat <= 3)
            toolbox.show_categories_difficulty(weighted_gold_chunks, args.cat)
        except AssertionError:
            raise('Please set args.cat from {1,2,3}')

    return


def calculate_system_score(weighted_gold_chunks: list, max_system_id: int, no_weight=False) -> list:
    scores = [infobox.Score(sys_id=i) for i in range(max_system_id)]
    for gold_chunks in weighted_gold_chunks:
        for gchunk in gold_chunks:
            scores = update_scores(scores, gchunk, no_weight)
    for score in scores:
        score.get_PRFA()
    return scores


def update_scores(scores: list, gchunk: list, no_weight: bool) -> list:
    for system_id, eval_info in enumerate(gchunk.sys2eval):
        scores[system_id].all_weight += (1 if no_weight else gchunk.weight)
        if eval_info.is_modified: # If system modified
            if eval_info.is_correct: # If modification is correct
                scores[system_id].TP += (1 if no_weight else gchunk.weight)
            else:
                scores[system_id].FP += (1 if no_weight else gchunk.weight)
                if gchunk.is_modified:
                    scores[system_id].FN += (1 if no_weight else gchunk.weight)
        else: # If the system didn't modify
            if eval_info.is_correct:
                scores[system_id].TN += (1 if no_weight else gchunk.weight)
            else:
                scores[system_id].FN += (1 if no_weight else gchunk.weight)
    return scores


def calculate_weight(scored_gold_chunks: list, a: float, b: float, c: float) -> list:
    for scored_gold_chunk in scored_gold_chunks:# Sentence loop
        for chunk in scored_gold_chunk: # Chunk loop
            chunk.calc_weight(a, b, c)
    return scored_gold_chunks


def show_score(scores: list, args) -> None:
    sys_name = args.sys_name.split(',') if args.sys_name else None
    if sys_name:
        max_name_length = max([len(s) for s in sys_name] + [len('Sys_name')])
    else:
        max_name_length = len('Sys_name')
    space = lambda s: abs(len(s) - max_name_length) * ' '
    title = "Non-Weighted Scores" if args.no_weight else "Weighted Scores"
    print('-----', title, '-----')
    print('Sys_name'+space('Sys_name'), end='\t')
    if args.verbose:
        print("{:8}\t{:8}\t{:8}\t{:8}\t".format("TP","FP","FN","TN"), end="")
    print("Prec.","Recall","F","F0.5","Accuracy", sep="\t")
    if args.sort:
        scores = sorted(scores, key=lambda x:x.F05, reverse=True)
    for score in scores:
        if sys_name:
            print(sys_name[score.sys_id] + space(sys_name[score.sys_id]), end=':\t')
        else:
            print(str(score.sys_id) + space(str(score.sys_id)), end=':\t')
        score.show(args.verbose)
    return


def get_parser() -> None:
    '''Get options
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-ref","--ref", required=True,
        help="A reference M2 file.")
    parser.add_argument(
        "-hyp","--hyp", required=True,
        help="A hypothesis M2 file.")
    parser.add_argument(
        "-name", "-sys_name", "--sys_name",
        help="Names of sysmtems. There names are used in performance output.")
    parser.add_argument(
        "-heat","--heat_map",
        help="Generate heatmap file. The outputs will be two file: .html and .css.")
    parser.add_argument(
        "-cat","--cat",
        type=int,
        choices=[1,2,3],
        help="Output error types performance. The output will be on terminal.\n"
            "1: R,M,U\n"
            "2: e.g. NOUN\n"
            "3: e.g. R:NOUN")
    parser.add_argument(
        "-gen_w_file","--gen_w_file",
        help="Generate weight file. The output will be a specified file.")
    parser.add_argument(
        "-w_file","--w_file",
        help="Evaluate using the specified weight file.")
    parser.add_argument(
        "-cv","-chunk_visualizer","--chunk_visualizer",
        help="Generate chunk_visualizer file. The output will be a specified file.")
    parser.add_argument(
        "-no_weight", "--no_weight", 
        help="Set the weights of all chunks to 1.",
        action='store_true')
    parser.add_argument(
        "-ref_id","--ref_id",
        type=int,
        default=0,
        help="Set the annotator id of the reference M2 file to be used for evaluation.")
    parser.add_argument(
        "-v", "-verbose","--verbose",
        help="Output will be included TP,FP,FN,TN.",
        action='store_true')
    parser.add_argument(
        "-sort","--sort",
        help="Output will be sorted by F_0.5",
        action='store_true')
    parser.add_argument(
        "-a", "--a", type=float,
        default=1,
        help="Set the parameter 'a' to use weight calculation.",)
    parser.add_argument(
        "-b", "--b", type=float,
        default=0,
        help="Set the parameter 'b' to use weight calculation.")
    parser.add_argument(
        "-c", "--c", type=float,
        default=0,
        help="Set the parameter 'c' to use weight calculation.")
    args = parser.parse_args()
    return args
      
if __name__ == "__main__":
    args = get_parser()
    main(args)
    