def categories_counter(gold_chunks):
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