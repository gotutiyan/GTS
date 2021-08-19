from scripts import infobox
from tqdm import tqdm

def chunk_scorer(gold_chunks: list, system_chunks: list) -> list:
    for system_id, each_system_chunk in enumerate(system_chunks):
        for gold_chunk, system_chunk in zip(gold_chunks, each_system_chunk):
            update_evaluation(gold_chunk, system_chunk, system_id)
    return gold_chunks

def update_evaluation(gold_chunk: list, system_chunk: list, system_id: int) -> None:
    for gchunk in gold_chunk:
        for schunk in system_chunk:
            judge = gchunk.compare(schunk)
            if judge == "equal":
                eval_info = infobox.EvalInfo(is_modified=schunk.is_modified,
                                             is_correct=True,
                                             judge=judge)
                try:
                    gchunk.sys2eval[system_id] = eval_info
                except IndexError:
                    gchunk.sys2eval.append(eval_info)
                break
            elif judge == "not-equal":
                eval_info = infobox.EvalInfo(is_modified=schunk.is_modified,
                                             is_correct=False,
                                             judge=judge)
                try:
                    gchunk.sys2eval[system_id].is_modified |= schunk.is_modified
                except IndexError:
                    gchunk.sys2eval.append(eval_info)
            elif judge == "pass":
                pass
                
        if len(gchunk.sys2eval) < system_id+1:
            eval_info = infobox.EvalInfo(is_modified=False,
                                         is_correct=(False if gchunk.is_modified else True),
                                         judge="pass")
            gchunk.sys2eval.append(eval_info)
    return

def calculate_system_score(weighted_gold_chunks: list, max_system_id: int, no_weight=False) -> list:
    scores = [infobox.Score(sys_id=i) for i in range(max_system_id)]
    for gold_chunks in weighted_gold_chunks: # Each sentence
        for gchunk in gold_chunks: # Each chunk in a sentence
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
            if eval_info.is_correct: # If modification is correct
                scores[system_id].TN += (1 if no_weight else gchunk.weight)
            else:
                scores[system_id].FN += (1 if no_weight else gchunk.weight)
    return scores        