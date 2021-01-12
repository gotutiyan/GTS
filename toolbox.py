def categories_counter(gold_chunks: dict) -> dict:
    cat2weight_list = dict()
    for _, systems in gold_chunks.items():
        for system in systems:
            for chunk in system:
                if chunk.is_error:
                    cat = chunk.cat.split(':')
                    cat2weight_list[cat[0]] = cat2weight_list.get(cat[0], list())
                    cat2weight_list[cat[0]].append(chunk.weight)
                    cat2weight_list[':'.join(cat[1:])] = \
                        cat2weight_list.get(':'.join(cat[1:]), list())
                    cat2weight_list[':'.join(cat[1:])].append(chunk.weight)
    return cat2weight_list

def debug(chunks: dict, target_coder=0) -> None:
    for sent, coder2chunks in chunks.items():
        print('-----',sent,'-----')
        for chunk in coder2chunks[target_coder]:
            chunk.show(True)
    return

def chunk_visualizer(gold_chunks: dict, file_name: str, target_coder=0) -> None:
    space = lambda x: ' '*x
    if file_name != None and file_name != 'None':
        out_fp = open(file_name, 'w')
    else:
        print('----- chunk visualizer -----')
    for sent, coder2chunks in gold_chunks.items():
        orig_str = '|'
        gold_str = '|'
        for chunk in coder2chunks[target_coder]:
            max_leng = max(len(chunk.orig_sent), len(chunk.gold_sent))
            orig_space_num = (max_leng - len(chunk.orig_sent)) // 2
            orig_str += space(orig_space_num)\
                        + chunk.orig_sent\
                        + space(orig_space_num + (max_leng - len(chunk.orig_sent))%2)\
                        + '|'
            gold_space_num = (max_leng - len(chunk.gold_sent)) // 2
            gold_str += space(gold_space_num)\
                        + chunk.gold_sent\
                        + space(gold_space_num + (max_leng - len(chunk.gold_sent))%2)\
                        + '|'
        if file_name == None or file_name == 'None':
            print('orig: '+orig_str)
            print('gold: '+gold_str)
            print()
        else:
            out_fp.write('orig: '+orig_str+'\n')
            out_fp.write('gold: '+gold_str+'\n')
            out_fp.write('\n')

            

