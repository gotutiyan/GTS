import argparse
import os
import random
from operator import itemgetter
import toolbox
import heatmap

def main(args):
    ref_m2 = open(args.ref).read().strip().split("\n\n")
    print("Generating chunks ...")
    # Generate chunks.
    error_chunks = generate_error_chunks(ref_m2)
    basic_chunks = insert_basic_chunks(error_chunks)
    gold_chunks = insert_insert_chunks(basic_chunks)
    systems_chunks = generate_systems_chunks(args)
    print("Evaluating systems ...")
    evaluated_gold_chunks = evaluation_systems(gold_chunks, systems_chunks)
    if args.w_file: weighted_gold_chunks = get_weight_from_weight_file(evaluated_gold_chunks, args.w_file)
    else: weighted_gold_chunks = calc_weight(evaluated_gold_chunks)
    # Compute score
    weighted_evaluations = calc_performance(weighted_gold_chunks, True)
    show_score(weighted_evaluations, args, title="weighted scores")
    if args.heat:
        heatmap.generate_heatmap_combine(weighted_gold_chunks, args.heat)
    if args.cat: 
        calc_cat_performance(weighted_gold_chunks, args.cat, "tsv")
    if args.gen_w_file:
        generate_weight_file(weighted_gold_chunks, args.gen_w_file)
    if args.chunk_visualizer:
        toolbox.chunk_visualizer(gold_chunks, args.chunk_visualizer)
    return

class ChunkInfo:
    def __init__(self):
        self.orig_range = (-1, -1)
        self.orig_sent = ""
        self.gold_range = (-1, -1)
        self.gold_sent = ""
        self.cat = ""
        self.coder_id = -1
        self.is_error = True
        self.sys2eval = dict()
        self.weight = -1

    def equal(self, other) -> str:
        '''Judge myself and input chunk are equal or not.
        Input: other ChunkInfo instance.
        Output: string represented result of comparision.
            "equal": Satisfy two conditions as following: 
                     (i)  all tokens corresponding to the chunks are the same.
                     (ii) the positions of the tokens aligned to the original sentence are the same. 
            "cover": Satisfy only (ii) condition, or overlapping ranges.
            "pass": Any condition are not satisfied.
        '''
        if other.orig_range == self.orig_range:
            if other.gold_sent == self.gold_sent:
                return "equal"
            else:
                return "cover"
        elif self.orig_range[0] == self.orig_range[1]:
            return "pass"
        elif self.orig_range[0] <= other.orig_range[0] < self.orig_range[1]:
                return "cover"
        elif other.orig_range[0] <= self.orig_range[0] < other.orig_range[1]:
                return "cover"
        else: return "pass"

    # calculation weight of its chunk
    def calc_weight(self) -> None:
        correct = 0
        for system_id, evalinfo in self.sys2eval.items():
            if evalinfo.is_correct:
                correct += 1
        correct_ans_rate = (correct) / (len(self.sys2eval) )
        self.weight = self.weight_f(correct_ans_rate)
        return 

    def weight_f(self, correct_ans_rate: float) -> float:
        '''Calcurate correction difficulty based on correction success rate.
        '''
        return 1 - correct_ans_rate

    def get_number_of_system(self) -> int:
        return len(self.sys2eval)

    # debug print
    def show(self,verbose=False) -> None:
        print("orig_range: ",self.orig_range,\
        "\norig_sent: ",self.orig_sent,\
        "\ngold_range: ", self.gold_range,\
        "\ngold_sent: ", self.gold_sent,\
        "\ncat: ",self.cat,\
        "\ncoder_id: ",self.coder_id,\
        "\nis_error: ",self.is_error,\
        "\nweight: ",self.weight,\
        )
        if verbose:
            for system_id, evalinfo in self.sys2eval.items():
                print("system_id: ",system_id)
                evalinfo.show()
        print("\n")
        return
                

class EvalInfo:
    def __init__(self, modify, correct):
        self.is_modify = modify
        self.is_correct = correct

    def show(self) -> None:
        print("modfy: ",self.is_modify, "correct: ",self.is_correct)
        return

class Score:
    def __init__(self):
        self.TP = 0
        self.TN = 0
        self.FP = 0
        self.FN = 0
        self.Precision = 0
        self.Recall = 0
        self.Accuracy = 0
        self.F = 0
        self.F5 =0
        self.all_weight = 0
        self.test = 0

    def get_RPFA(self) -> None:
        try: self.Precision = (self.TP)/(self.TP+self.FP)
        except ZeroDivisionError: self.Precision = 0
        try: self.Recall = (self.TP)/(self.TP+self.FN)
        except ZeroDivisionError: self.Recall = 0
        try: self.F = 2*self.Precision*self.Recall/(self.Precision + self.Recall)
        except ZeroDivisionError: self.F = 0
        try: self.F5 = float(1.25*self.Precision*self.Recall)\
            /(0.25*self.Precision + self.Recall)
        except ZeroDivisionError: self.F5 = 0
        try: self.Accuracy = (self.TP + self.TN) / (self.all_weight)
        except ZeroDivisionError: self.Accuracy = 0
        return

    def show(self, verbose=False) -> None:
        ROUND_DIGIT = 4
        if verbose:
            print("{:.4f}".format(round(self.TP, ROUND_DIGIT)),
                "{:.4f}".format(round(self.FP, ROUND_DIGIT)),
                "{:.4f}".format(round(self.FN, ROUND_DIGIT)),
                "{:.4f}".format(round(self.TN, ROUND_DIGIT)),
                sep='\t', end='\t')
        print("{:.4f}".format(round(self.Precision, ROUND_DIGIT)),
                "{:.4f}".format(round(self.Recall, ROUND_DIGIT)),
                "{:.4f}".format(round(self.F, ROUND_DIGIT)),
                "{:.4f}".format(round(self.F5, ROUND_DIGIT)),
                "{:.4f}".format(round(self.Accuracy, ROUND_DIGIT)),
                sep='\t')
        return

def show_score(evaluations:dict, args, title="weighted scores") -> None:
    sys_name = args.sys_name.split(',') if args.sys_name else None
    print('-----', title, '-----')
    print('name\t', end='')
    if args.verbose:
        print("TP","FP","FN","TN",sep="\t", end="\t")
    print("Prec.","Recall","F","F0.5","Accuracy",sep="\t")
    for system_id, score in evaluations.items():
        print(sys_name[system_id] if sys_name else str(system_id),
              end=":\t")
        score.show(args.verbose)
    return

def calc_performance(gold_chunk: dict, is_weighted=True, target_coder=0) -> dict:
    ''' Calculate performance: precision, recall, F, F0.5, and Accuracy.
    Input1: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    Output: {syste_id: Score()}
    '''
    system_score = dict()
    for sent, coder2chunks in gold_chunk.items():
        for chunk in coder2chunks[target_coder]:
            if chunk.cat == "noop": continue
            for system_id, evalinfo in chunk.sys2eval.items(): # look evaluation of each system for chunk
                system_score[system_id] = system_score.get(system_id, Score())
                system_score[system_id] = update_score(
                    chunk, evalinfo, system_score[system_id], is_weighted)
                
    for score in system_score.values():
        score.get_RPFA()
    return system_score

def update_score(chunk: ChunkInfo, evalinfo: EvalInfo, score: Score, is_weighted: bool) -> Score:
    eval = (int(chunk.is_error), int(evalinfo.is_modify), int(evalinfo.is_correct))
    if eval == (1,1,1): score.TP += chunk.weight if is_weighted else 1.0
    elif eval == (1,0,0): score.FN += chunk.weight if is_weighted else 1.0
    elif eval == (1,1,0):
        score.FP += chunk.weight if is_weighted else 1.0
        score.FN += chunk.weight if is_weighted else 1.0
    elif eval == (0,0,1): score.TN += chunk.weight if is_weighted else 1.0
    elif eval == (0,1,0): score.FP += chunk.weight if is_weighted else 1.0
    score.all_weight += chunk.weight if is_weighted else 1.0
    if chunk.is_error:
        score.test += chunk.weight if is_weighted else 1.0
    return score

def calc_weight(gold_chunks: dict, target_coder=0):
    ''' Caclulate weight of each chunk.
    Input: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    Output: Data structure is same as input.
    '''
    for sent, coder2chunks in gold_chunks.items():
        for chunk in coder2chunks[target_coder]:
            chunk.calc_weight()
    return gold_chunks

def get_weight_from_weight_file(gold_chunks: dict, file_name: str, target_coder=0) -> dict:
    weight_file = open(file_name).read().strip().split('\n')
    number_of_sys = int(weight_file[0])
    splited_weight_data = []
    for line in weight_file[1:]:
        weights = list(map(int, line.split()))
        splited_weight_data.append(weights)
    idx = 0
    for sent, coder2chunks in gold_chunks.items():
        for i, chunk in enumerate(coder2chunks[target_coder]):
            chunk.weight = chunk.weight_f(splited_weight_data[idx][i] / number_of_sys)
        idx += 1
    return gold_chunks

def evaluation_systems(gold_chunks: dict, systems_chunks: dict, target_coder=0) -> dict:
    ''' Evaluate output of each system. In other words, we calculate B^(s) of the paper.
    Input: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    Output: Data structure is same as input.
    '''
    for sent, coder2chunks in gold_chunks.items():
        # Loop gold chunks
        for gchunk in coder2chunks[target_coder]:
            if gchunk.cat == "noop": continue
            # Loop systems chunks.
            for system_id, system_chunks in enumerate(systems_chunks[sent]):
                for schunk in system_chunks:
                    if schunk.cat == "noop": continue
                    if gchunk.equal(schunk) == "equal":
                        gchunk.sys2eval[system_id] = EvalInfo(schunk.is_error, True)
                    elif gchunk.equal(schunk) == "cover":
                        if gchunk.sys2eval.get(system_id)\
                            and gchunk.sys2eval[system_id].is_modify:
                            continue
                        gchunk.sys2eval[system_id] = EvalInfo(schunk.is_error, False)
                if gchunk.sys2eval.get(system_id) == None:
                    if gchunk.is_error:
                        # In error chunk correction, not to modify is mistake.
                        gchunk.sys2eval[system_id] = EvalInfo(False, False)
                    else:
                        # In non-error chunk correction, not to modify is correct.
                        gchunk.sys2eval[system_id] = EvalInfo(False, True)
                
    return gold_chunks        

##########################################################################PEP79

def generate_error_chunks(m2_data: list, mode="gold", target_coder='0') -> dict:
    ''' Generate only error chunks from reference.
    Output: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    '''
    error_chunks = dict()
    sent2freq = dict()
    for info in m2_data:
        chunks = list()
        orig_sent, coder_dict = processM2(info)
        if coder_dict:
            for coder, coder_info in sorted(coder_dict.items()):
                gold_edits = coder_info[1]
                if (mode == "gold" and coder == target_coder) or (mode == "system"):
                    for gold_edit in gold_edits:
                    # Um and UNK edits (uncorrected errors) are always preserved.
                        if gold_edit[2] in {"Um", "UNK","noop"}:
                            continue
                        if not gold_edit: continue
                        chunk_info = edit2ChunkInfo(orig_sent, gold_edit+[coder])
                        chunks.append(chunk_info)
        orig_string = ' '.join(orig_sent) # ['a', 'b', 'c'] -> 'a b c'
        if mode == "gold":
            sent2freq[orig_string] = sent2freq.get(orig_string, -1) + 1
            orig_string = orig_string + ' '+ str(sent2freq[orig_string])
        error_chunks[orig_string] = error_chunks.get(orig_string, list())
        error_chunks[orig_string].append(chunks)
    return error_chunks

def insert_basic_chunks(error_chunks: dict) -> dict:
    ''' Generate chunks of exist non-error token in original sentence.
    Input: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    Output: Data structure is same as input.
    '''
    for orig_sent, error_chunk in error_chunks.items():
        for coder, chunks in enumerate(error_chunk):
            orig_tokens = orig_sent.split()
            basic_chunks = list()
            # get BASIC chunk
            prev_pos = 0
            for i, chunk in enumerate(chunks):
                # if index are not consecutive
                if chunk.orig_range[0] != prev_pos:
                    non_error_chunks = generate_non_error_chunks(
                        prev_pos, chunk.orig_range[0], orig_tokens, coder)
                    basic_chunks += non_error_chunks # Combine two list
                prev_pos = chunk.orig_range[1]
                basic_chunks.append(chunk)
            non_error_chunks = generate_non_error_chunks(
                        prev_pos, len(orig_tokens)-1, orig_tokens, coder)
            basic_chunks += non_error_chunks # Combine two list
            error_chunks[orig_sent][coder] = basic_chunks
    return error_chunks

def generate_non_error_chunks(idx_begin: int, idx_end: int, orig_tokens: list, coder: int) -> list:
    non_error_chunks = list()
    for i in range(idx_begin, idx_end):
        non_error_chunks.append(edit2ChunkInfo(
            orig_tokens, 
            [i, i+1, "", orig_tokens[i], None ,None, coder],
            False))
    return non_error_chunks
        
def insert_insert_chunks(basic_chunks: dict) -> dict:
    ''' Generate chunks corresponds insert.
    Input: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    Output: Data structure is same as input.
    '''
    for orig_sent, basic_chunk in basic_chunks.items():
        for coder, chunks in enumerate(basic_chunk):
            gold_chunks = list()
            orig_tokens = orig_sent.split()
            # get INSERT chunk
            for i, chunk in enumerate(chunks):
                # Already exist chunk correspond insert
                if chunk.orig_range[0] == chunk.orig_range[1]:
                    gold_chunks.append(chunk)
                    continue
                if i-1 >= 0 and chunks[i-1].orig_range[0] == chunks[i-1].orig_range[1]:
                    gold_chunks.append(chunk)
                    continue
                insert_chunk = edit2ChunkInfo(
                    orig_sent,
                    [chunk.orig_range[0], chunk.orig_range[0], "INSERT", "", None, None, coder],
                    False)
                gold_chunks.append(insert_chunk)
                gold_chunks.append(chunk)
            if gold_chunks[-1].orig_range[0] != gold_chunks[-1].orig_range[1]:
                insert_chunk = edit2ChunkInfo(
                    orig_sent,
                    [len(orig_tokens)-1, len(orig_tokens)-1, "INSERT", "", None, None, coder],
                    False)
                gold_chunks.append(insert_chunk)
            basic_chunks[orig_sent][coder] = gold_chunks
    return basic_chunks

def generate_systems_chunks(args) -> dict:
    ''' Generate system chunks from -hyp file.
    Output: {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    '''
    systems_chunks = dict()
    sent2num = dict()
    with open(args.hyp) as fp:
        orig_sent = ""
        id2edit = list()
        for line in fp:
            if line == "\n":
                hyp_m2 = list()
                for edits in id2edit:
                    hyp_m2.append('\n'.join(edits))
                error_chunks = generate_error_chunks(hyp_m2, "system")
                basic_chunks = insert_basic_chunks(error_chunks)
                system_chunks = insert_insert_chunks(basic_chunks)
                systems_chunks[orig_sent[2:]] = system_chunks[orig_sent[2:]]
            elif line[0] == "S":
                orig_sent = line.rstrip()
                sent2num[orig_sent] = sent2num.get(orig_sent,-1) + 1
                orig_sent = orig_sent + " " + str(sent2num[orig_sent])
                id2edit = list()
            elif line[0] == "A":
                index = int(line.rstrip().split('|||')[-1])
                if index >= len(id2edit):
                    id2edit.append(list())
                    id2edit[-1].append(orig_sent.rstrip())
                id2edit[index].append(line.rstrip())
            else:
                break
    return systems_chunks

def get_parser():
    '''get options by argparse
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-ref", required=True)
    parser.add_argument("-hyp", required=True)
    parser.add_argument("-sys_name")
    parser.add_argument("-heat")
    parser.add_argument("-cat")
    parser.add_argument("-gen_w_file")
    parser.add_argument("-w_file")
    parser.add_argument("-chunk_visualizer")
    parser.add_argument("-verbose", action='store_true')
    
    args = parser.parse_args()
    return args

def edit2ChunkInfo(orig_tokens: list, edit: list, is_error=True) -> ChunkInfo:
    ''' Convert edit information to ChunkInfo instance.
    Input1: list of tokens.
    Input2: list represented edit information. [int, int, string, string, int, int, int]
    '''
    info = ChunkInfo()
    info.cat = edit[2]
    info.orig_range = (edit[0], edit[1])
    if info.cat == "noop":
        info.is_error = False
        return info
    info.orig_sent = ' '.join(orig_tokens[edit[0]:edit[1]])
    info.gold_range = (edit[4],edit[5])
    info.gold_sent = edit[3]
    info.coder_id = edit[6]
    info.is_error = is_error

    return info

def calc_cat_performance(gold_chunks: dict, out_file_name: str, print_mode = "tsv") -> dict:
    ''' Calculate performance of each error type.
    Input1: dict, {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
    Output: dict, {error_type: [sum, average, SD, freq]}
    '''
    cat2weight_list = toolbox.categories_counter(gold_chunks)
    cat2score = dict() # {cat : [sum, average, SD, freq]}
    for cat, weight_list in cat2weight_list.items():
        cat2score[cat] = cat2score.get(cat, [0, 0, 0, 0])
        cat2score[cat][3] = len(weight_list)
        # sum
        cat2score[cat][0] = sum(cat2weight_list[cat])
        # average
        cat2score[cat][1] = cat2score[cat][0] / len(weight_list)
        # standard deviation
        dispersion = 0
        for weight in weight_list:
            dispersion += (weight - cat2score[cat][1]) ** 2
        try: cat2score[cat][2] = (dispersion / (len(weight_list) - 1)) ** 0.5
        except ZeroDivisionError: cat2score[cat][2] = 0
    
    buff = list()
    for cat, score in cat2score.items():
        buff.append([score[1],cat,score[2],score[3]])
    buff = sorted(buff,reverse = True, key=lambda x: x[0])

    if print_mode == "tsv":
        out_fp = open(out_file_name,"w")
        out_fp.write('Code\tAv.\tSD\tFleq.\n')
        for bu in buff:
            out_fp.write("{}\t{}\t{}\t{}\n".format(bu[1],str(round(bu[0],2))\
                +' ',str(round(bu[2],2))+' ',str(bu[3])))
        out_fp.close()
    # for a paper's figure
    elif print_mode == "tex":
        tex = open(out_file_name,"w")
        tex.write("\\begin{center}\n\\begin{tabular}{c|ccc}\\hline\n")
        tex.write("Code&Av.&SD&Fleq. \\\\ \\hline\n")
        for bu in buff:
            tex.write("{} & {} & {} & {} \\\\ \n".format(bu[1],str(round(bu[0],3))\
                +' ',str(round(bu[2],3))+' ',str(bu[3])))
        tex.write("\\hline\end{tabular}\n\end{center}")
    return cat2score

##########################################################################PEP79

def generate_weight_file(gold_chunks: dict, file_name: str) -> None:
    ''' Generate weight-file.
    Input1: dict, {original_sentence: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}    
    '''
    out = open(file_name,"w")
    is_written_number_of_system = True
    for sent, coder2chunks in gold_chunks.items():
        for chunks in coder2chunks:
            weight_list = list()
            for gchunk in chunks:
                if is_written_number_of_system:
                    out.write(str(gchunk.get_number_of_system())+'\n')
                    is_written_number_of_system = False
                n_i = 0
                for evalinfo in gchunk.sys2eval.values():
                    n_i += int(evalinfo.is_correct)
                weight_list.append(str(round(n_i)))
            out.write(' '.join(weight_list)+'\n')
    out.close()
    return
        

# Copyright (c) 2017 Christopher Bryant, Mariano Felice
# Input: A sentence + edit block in an m2 file.
# Output 1: The original sentence (a list of tokens)
# Output 2: A dictionary; key is coder id, value is a tuple. 
# tuple[0] is the corrected sentence (a list of tokens), tuple[1] is the edits.
# Process M2 to extract sentences and edits.
def processM2(info):
	info = info.split("\n")
	orig_sent = info[0][2:].split() # [2:] ignore the leading "S "
	all_edits = info[1:]
	# Simplify the edits and group by coder id.
	edit_dict = processEdits(all_edits)
	out_dict = {}
	# Loop through each coder and their edits.
	for coder, edits in edit_dict.items():
		# Copy orig_sent. We will apply the edits to it to make cor_sent
		cor_sent = orig_sent[:]
		gold_edits = []
		offset = 0
		# Sort edits by start and end offset only. If they are the same, do not reorder.
		edits = sorted(edits, key=itemgetter(0)) # Sort by start offset
		edits = sorted(edits, key=itemgetter(1)) # Sort by end offset
		for edit in edits:
			# Do not apply noop or Um edits, but save them
			if edit[2] in {"noop", "Um"}: 
				gold_edits.append(edit+[-1,-1])
				continue
			orig_start = edit[0]
			orig_end = edit[1]
			cor_toks = edit[3].split()
			# Apply the edit.
			cor_sent[orig_start+offset:orig_end+offset] = cor_toks
			# Get the cor token start and end positions in cor_sent
			cor_start = orig_start+offset
			cor_end = cor_start+len(cor_toks)
			# Keep track of how this affects orig edit offsets.
			offset = offset-(orig_end-orig_start)+len(cor_toks)
			# Save the edit with cor_start and cor_end
			gold_edits.append(edit+[cor_start]+[cor_end])
		# Save the cor_sent and gold_edits for each annotator in the out_dict.
		out_dict[coder] = (cor_sent, gold_edits)
	return orig_sent, out_dict

# Copyright (c) 2017 Christopher Bryant, Mariano Felice
# Input: A list of edit lines for a sentence in an m2 file.
# Output: An edit dictionary; key is coder id, value is a list of edits.
def processEdits(edits):
	edit_dict = {}
	for edit in edits:
		edit = edit.split("|||")
		span = edit[0][2:].split() # [2:] ignore the leading "A "
		start = int(span[0])
		end = int(span[1])
		cat = edit[1]
		cor = edit[2]
		id = edit[-1]
		# Save the useful info as a list
		proc_edit = [start, end, cat, cor]
		# Save the proc edit inside the edit_dict using coder id.
		if id in edit_dict.keys():
			edit_dict[id].append(proc_edit)
		else:
			edit_dict[id] = [proc_edit]
	return edit_dict
      
if __name__ == "__main__":
    args = get_parser()
    main(args)
    