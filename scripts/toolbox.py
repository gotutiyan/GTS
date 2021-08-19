from scripts import infobox
from scripts.infobox import ChunkInfo
import statistics as stat

def category_difficulty(gold_chunks: list, mode: int) -> list:
    cat2weight_list = dict()
    for gold_chunk in gold_chunks:
        for gchunk in gold_chunk:
            if not gchunk.is_modified:
                continue
            cat = gchunk.cat
            if mode == 1: # Consider only {M,R,U}
                cat = cat.split(':')[0] 
            elif mode == 2: # Consider only {VERB, NOUN, etc.}
                cat = ':'.join(cat.split(':')[1:]) 
            cat2weight_list[cat]\
                = cat2weight_list.get(cat, [])
            cat2weight_list[cat].append(gchunk.weight)
    cat = list(cat2weight_list.keys())
    weight_list = list(cat2weight_list.values())
    cat_diffs = [[0]*4 for _ in range(len(cat))] # [[mean, stdev, #, cat], ...]
    for i in range(len(cat)):
        cat_diffs[i][0] = stat.mean(weight_list[i])
        try:
            cat_diffs[i][1] = stat.stdev(weight_list[i])
        except stat.StatisticsError:
            cat_diffs[i][1] = 0
        cat_diffs[i][2] = len(weight_list[i])
        cat_diffs[i][3] = cat[i]
    # Sort by mean
    cat_diffs = sorted(cat_diffs, key=lambda x:x[0], reverse=True)
    return cat_diffs

def show_categories_difficulty(weighted_gold_chunks: list, mode: int) -> None:
    cat_diffs = category_difficulty(weighted_gold_chunks, mode)
    print('----- Category Difficulty -----')
    print('{:10}\tAve.\tStd.\tFreq.'.format("Category"))
    for diff in cat_diffs:
        print('{:10}\t{:.2f}\t{:.2f}\t{}'\
            .format(diff[3], diff[0], diff[1], diff[2]))
    return

def debug(chunks: list, verbose=False) -> None:
    for chunk in chunks:
        chunk.show(verbose)
    print('-----')
    return

def chunk_visualizer(gold_chunks: list, file_name: str) -> None:
    if file_name != "None":
        out_fp = open(file_name, 'w')
    else:
        print('----- Chunk Visualizer -----')
    for gold_chunk in gold_chunks:
        orig_str = '|'
        gold_str = '|'
        weight_str = '|'
        cat_str = '|'
        for chunk in gold_chunk:
            str_weight = str(round(chunk.weight, 2))
            max_leng = max(len(chunk.orig_sent), len(chunk.gold_sent), len(str_weight), len(chunk.cat))
            # max_leng = max(len(chunk.orig_sent), len(chunk.gold_sent))
            orig_str += str_helper_for_visualizer(chunk.orig_sent, max_leng)
            gold_str += str_helper_for_visualizer(chunk.gold_sent, max_leng)
            weight_str += str_helper_for_visualizer(str(round(chunk.weight, 2)), max_leng)
            cat_str += str_helper_for_visualizer(chunk.cat, max_leng)
        if file_name == "None":
            print('orig:   ' + orig_str)
            print('gold:   ' + gold_str)
            print('weight: ' + weight_str)
            print('cat:    ' + cat_str + '\n')
        else:
            out_fp.write('orig  : ' + orig_str + '\n')
            out_fp.write('gold  : ' + gold_str + '\n')
            out_fp.write('weight: ' + weight_str + '\n')
            out_fp.write('cat   : ' + cat_str + '\n\n')

def str_helper_for_visualizer(string: str, max_leng: int) -> str:
    '''
    >>> str_helper_for_visualizer("aaa", 5)
    " aaa |"
    >>> str_helper_for_visualizer("aa", 5)
    "  aa |"
    '''
    space = lambda x: ' '*x
    space_num = (max_leng - len(string)) // 2
    ret_str = space(space_num)\
                + string\
                + space(space_num + (max_leng - len(string))%2)\
                + '|'
    return ret_str

def import_m2(m2_path: str, coder_id=0):
    m2s = open(m2_path).read().split('\n\n')
    origs = []
    gold_edits = []
    for m2 in m2s:
        orig, *edits = m2.split('\n')
        if orig == '': continue
        origs.append(orig[2:]) # Eliminate "S "
        edits_of_orig = []
        for edit in edits:
            if edit == '': continue
            if int(edit[-1]) != coder_id: continue
            edits_of_orig.append(edit[2:]) # Eliminate "A "
        gold_edits.append(edits_of_orig)
    return origs, gold_edits

def edit_to_chunk(tokens: list, edit: str) -> ChunkInfo:
    edit = edit.split('|||')
    start_idx = int(edit[0].split(' ')[0])
    end_idx = int(edit[0].split(' ')[1])
    chunk = infobox.ChunkInfo((start_idx, end_idx),
                              ' '.join(tokens[start_idx:end_idx]),
                              edit[2],
                              True)
    chunk.cat = edit[1]
    return chunk