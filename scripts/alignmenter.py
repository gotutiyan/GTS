from scripts import infobox
from tqdm import tqdm


def evaluate(gold_chunks: list, system_chunks: list) -> list:
    for system_id, each_system_chunk in enumerate(system_chunks):
        for gold_chunk, system_chunk in zip(gold_chunks, each_system_chunk):
            update_evaluation(gold_chunk, system_chunk, system_id)
    return gold_chunks


def update_evaluation(gold_chunk: list, system_chunk: list, system_id: int) -> None:
    for gchunk in gold_chunk:
        for schunk in system_chunk:
            judge = gchunk.compare(schunk)
            if judge == "equal":
                eval_info = infobox.EvalInfo(
                    is_modified=schunk.is_modified,
                    is_correct=True,
                    judge=judge)
                try:
                    gchunk.sys2eval[system_id] = eval_info
                except IndexError:
                    gchunk.sys2eval.append(eval_info)
                break
            elif judge == "not-equal":
                eval_info = infobox.EvalInfo(
                    is_modified=schunk.is_modified,
                    is_correct=False,
                    judge=judge)
                try:
                    gchunk.sys2eval[system_id].is_modified |= schunk.is_modified
                except IndexError:
                    gchunk.sys2eval.append(eval_info)
            elif judge == "pass":
                pass
                
        if len(gchunk.sys2eval) < system_id+1:
            eval_info = infobox.EvalInfo(
                is_modified=False,
                is_correct=(False if gchunk.is_modified else True),
                judge="pass")
            gchunk.sys2eval.append(eval_info)
    return

