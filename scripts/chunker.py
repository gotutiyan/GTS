from scripts import toolbox, infobox

# Generate error-only chunk corresponding annotator_id
def generate_chunk_from_m2(m2_path: str, annotator_id: int) -> list:
    origs, edits_list = toolbox.import_m2(m2_path, annotator_id)
    if is_there_no_edit(edits_list):
        return -1
    chunks_list = []
    for orig, edits in zip(origs, edits_list):
        tokens = orig.split(' ')
        erroneous_chunks = make_erroneous_chunks(tokens, edits)
        basic_chunks = add_basic_chunks(tokens, erroneous_chunks)
        chunks = add_insert_chunks(tokens, basic_chunks)
        chunks_list.append(chunks)
    return chunks_list

# First, we make chunk include only errorneous chunk
def make_erroneous_chunks(tokens: list, edits: list) -> list:
    erroneous_chunks = []
    for edit in edits:
        chunk = toolbox.edit_to_chunk(tokens, edit)
        if chunk.cat in ["noop", "UNK", "Um"]:
            continue
        erroneous_chunks.append(chunk)
    return erroneous_chunks

# Second, we add non-errorneous chunk which corresponding a token
def add_basic_chunks(tokens, erroneouse_chunks):
    idx = 0
    basic_chunks = []
    for chunk in erroneouse_chunks:
        for i in range(idx, chunk.orig_range[0]):
            basic_chunk = infobox.ChunkInfo((i,i+1),
                                            ' '.join(tokens[i:i+1]),
                                            ' '.join(tokens[i:i+1]),
                                            False)
            basic_chunks.append(basic_chunk)
        basic_chunks.append(chunk)
        idx = chunk.orig_range[1]
    for i in range(idx, len(tokens)):
        basic_chunk = infobox.ChunkInfo((i,i+1),
                                        ' '.join(tokens[i:i+1]),
                                        ' '.join(tokens[i:i+1]),
                                        False)
        basic_chunks.append(basic_chunk)
    return basic_chunks

# Third, we add non-errorneous chunk which corresponding an insert
def add_insert_chunks(tokens: list, basic_chunks: list):
    chunks = []
    for i, chunk in enumerate(basic_chunks):
        if chunk.is_insert_chunk():
            chunks.append(chunk)
            continue
        if i-1>=0 and basic_chunks[i-1].is_insert_chunk():
            chunks.append(chunk)
            continue
        insert_chunk = infobox.ChunkInfo((chunk.orig_range[0], chunk.orig_range[0]),
                                         '', '', False)
        chunks.append(insert_chunk)
        chunks.append(chunk)
    if not basic_chunks[-1].is_insert_chunk():
        insert_chunk = infobox.ChunkInfo((len(tokens), len(tokens)),
                                         '', '', False)
        chunks.append(insert_chunk)
    return chunks

def is_there_no_edit(edits_list: list) -> bool:
    for edits in edits_list:
        if edits != []:
            return False
    return True

def generate_system_chunks(hyp_path: str) -> list:
    system_chunks = []
    system_id = 0
    while True:
        system_chunk = generate_chunk_from_m2(hyp_path, annotator_id=system_id)
        if system_chunk == -1: # There is no edit corrsponding system_id
            break
        system_chunks.append(system_chunk)
        system_id += 1
    return system_chunks