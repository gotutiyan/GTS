import argparse
import os
import random
from operator import itemgetter
import toolbox
import heatmap


##########################################################################PEP79
def main(args):
    ref_m2 = open(args.ref).read().strip().split("\n\n")
    print("start getting gold chunk ...")
    # 誤り箇所だけの正解チャンク列を生成
    error_chunks = generate_error_chunks(ref_m2)
    # ダミーチャンクも含めた、正解のチャンク列を生成
    gold_chunks = generate_all_chunks(error_chunks)
    print("start getting system chunk ...")
    # システムのチャンク列を生成
    systems_chunks = generate_systems_chunks(args)
    print("start getting evaluation ...")
    # 2つのチャンク列を突き合し、B^(s)に当たる情報を獲得
    evaluated_gold_chunks = evaluation_systems(gold_chunks, systems_chunks)
    # B^(s)にあたる情報から、重みを計算
    weighted_gold_chunks = None
    if args.w_file: weighted_gold_chunks = get_weight_from_weight_file(gold_chunks, args.w_file)
    else: weighted_gold_chunks = cluc_weight(evaluated_gold_chunks)
    # debug(weighted_gold_chunks)

    # Compute weighted score
    weighted_evaluations = get_performance(weighted_gold_chunks, True)
    show_score(weighted_evaluations, args, mode="weighted")
    # Compute non-weighted score
    # non_weighted_evaluations = get_performance(weighted_gold_chunks, False)
    # show_score(non_weighted_evaluations, args, mode="non-weighted")
    # generate heat map
    if args.heat:
        heatmap.generate_heatmap_combine(weighted_gold_chunks, args.heat)
    # calculate cat performance 
    if args.cat: 
        calc_cat_performance(weighted_gold_chunks, args.cat, "tsv")
    # generate file which all words are replaced thier weight
    if args.gen_w_file:
        generate_weight_file(weighted_gold_chunks, args.gen_w_file)

def show_score(evaluations, args, mode="weighted"):
    sys_name = args.sys_name.split(',') if args.sys_name else None
    print('-----', mode, 'score -----')
    print('name\t', end='')
    if args.verbose:
        print("TP","FP","FN","TN",sep="\t", end="\t")
    print("Prec.","Recall","F","F0.5","Accuracy",sep="\t")
    for system_id, score in evaluations.items():
        print(sys_name[system_id] if sys_name else str(system_id),
              end=":\t")
        score.show(args.verbose)

# Calcurate performance: precision, recall, F, F0.5, and Accuracy 
# input1: type:dict, shape:{str: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
#         gold(correct) chunk
# input2: type:bool, if True , It compute score by weighted score, otherwise compute normal score 
# output: type:dict, shape:{system_id: Score instance}, each system's score  
def get_performance(gold_chunk, is_weighted = True):
    system_score = dict()
    for sent, systems in gold_chunk.items(): # look each sentence
        for chunk in systems[0]: # look each chunk
            if chunk.cat == "noop": continue
            for system_id, evalinfo in chunk.sys2eval.items(): # look evaluation of each system for chunk
                system_score[system_id] = system_score.get(system_id, Score())

                system_score[system_id] = update_score(chunk, evalinfo, system_score[system_id], is_weighted)
                
    for score in system_score.values():
        score.get_RPFA()
    return system_score

def update_score(chunk, evalinfo, score, is_weighted):
    # 3つのバイナリパラメータを2進数的な表記に変換。
    eval = (int(chunk.is_error), int(evalinfo.is_modefy), int(evalinfo.is_correct))
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


# calculation weight of each chunk
# input: type:dict, shape:{str: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
#        gold chunks
# output: type:dict, shape:{str: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]} 
#         gold chunk which calculated weight of each chunk 
def cluc_weight(gold_chunks):
    for sent, systems in gold_chunks.items():
        for chunk in systems[0]:
            chunk.cluc_weight()
    return gold_chunks

def get_weight_from_weight_file(gold_chunks, file_name):
    weight_file = open(file_name).read().strip().split('\n')
    number_of_sys = int(weight_file[0])
    splited_weighted_data = []
    for line in weight_file[1:]:
        weights = list(map(int, line.split()))
        splited_weighted_data.append(weights)
    
    idx = 0
    for sent, systems in gold_chunks.items():
        for i, chunk in enumerate(systems[0]):
            chunk.weight = chunk.weight_f(splited_weighted_data[idx][i] / number_of_sys)
        idx += 1
    return gold_chunks



# システムを評価し、論文中のB^(s)を獲得する
# input1: chunks of gold  {str:[[ChunkInfo,,,ChunkInfo],,,[ChunkInfo,,,ChunkInfo]]}
# input2: chunks of systems 
def evaluation_systems(gold_chunks, systems_chunks):
    for sent, systems in gold_chunks.items():
        for gchunk in systems[0]:
            if gchunk.cat == "noop": continue
            for system_id, system_chunks in enumerate(systems_chunks[sent]):
                for schunk in system_chunks:
                    if schunk.cat == "noop": continue
                    # チャンクが一致していれば、そのチャンクは（誤りチャンクかを問わず）正解
                    if gchunk.equal(schunk) == "equal":
                        gchunk.sys2eval[system_id] = EvalInfo(schunk.is_error, True)
                    # チャンクが一致していないが、一方がもう一方をカバーしていれば、（誤りチャンクかを問わず）不正解
                    elif gchunk.equal(schunk) == "cover":
                        if gchunk.sys2eval.get(system_id)\
                            and gchunk.sys2eval[system_id].is_modefy:
                            continue
                        gchunk.sys2eval[system_id] = EvalInfo(schunk.is_error, False)
                if gchunk.sys2eval.get(system_id) == None:
                    if gchunk.is_error:
                        gchunk.sys2eval[system_id] = EvalInfo(False, False)
                    else:
                        gchunk.sys2eval[system_id] = EvalInfo(False, True)
                
    return gold_chunks        

##########################################################################PEP79
# get ERROR chunk
# input1: type:string, m2形式のデータ
# input2: type:bool, 
# output: {str: [[ChunkInfo,...,ChunkInfo],...,[ChunkInfo,...,ChunkInfo]]}
#               各文に対するチャンク列のリスト
def generate_error_chunks(m2_file, mode="gold"):
    all_edit = dict()
    # each sentence
    sent2num = dict()
    for info in m2_file:
        chunks = list()
        orig_sent, coder_dict = processM2(info)
        if coder_dict:
			# Save marked up or 
            proc_orig = ""
			# Loop through the  
            for coder, coder_info in sorted(coder_dict.items()):
                cor_sent = coder_info[0]
                gold_edits = coder_info[1]
                if (mode == "gold" and coder == "0") or (mode == "system"):
                    for gold_edit in gold_edits:
                    # Um and UNK edits (uncorrected errors) are always preserved.
                        if gold_edit[2] in {"Um", "UNK","noop"}:
                            continue
                        if not gold_edit: continue
                        chunk_info = edit2ChunkInfo(orig_sent, gold_edit+[coder])
                        chunks.append(chunk_info)
        # 同じ文が出現した時の対処として、文末にIDをつける
        if mode == "gold":
            sent2num[' '.join(orig_sent)] = sent2num.get(' '.join(orig_sent),-1) + 1
            orig_sent = orig_sent + [str(sent2num[' '.join(orig_sent)])]
        all_edit[' '.join(orig_sent)] = all_edit.get(' '.join(orig_sent),list())
        all_edit[' '.join(orig_sent)].append(chunks)
    return all_edit

# 全てのチャンクを生成する
# input1: string, original sentence
# input2: list of ChunkInfo's instance, ERROR chunks
def generate_all_chunks(error_chunks):
    for_all_chunks = dict()
    for sent, system_chunk in error_chunks.items():
        for coder,chunks in enumerate(system_chunk):
            orig_sent = sent.split()
            basic_chunk = list()
            # get BASIC chunk
            prev_pos = 0
            for i,chunk in enumerate(chunks):
                # ERROR chunk
                if chunk.orig_range[0] == prev_pos:
                    prev_pos = chunk.orig_range[1]
                    basic_chunk.append(chunk)
                # NO ERROR chunk
                else :
                    for j in range(prev_pos, chunks[i].orig_range[0]):
                        no_error_chunk = edit2ChunkInfo(orig_sent,\
                            [j, j+1,"",orig_sent[j],None,None,coder],False)
                        basic_chunk.append(no_error_chunk)
                    basic_chunk.append(chunk)
                    prev_pos = chunk.orig_range[1]
            for j in range(prev_pos,len(orig_sent)-1):
                no_error_chunk = edit2ChunkInfo(orig_sent,\
                    [j,j+1,"",orig_sent[j],None,None,coder],False)
                basic_chunk.append(no_error_chunk)
        
            all_chunks = list()
            # get INSERT chunk
            for i, chunk in enumerate(basic_chunk):
                # Already exit insert chunk
                if chunk.orig_range[0] == chunk.orig_range[1]:
                    all_chunks.append(chunk)
                    continue
                if i-1 >= 0 and basic_chunk[i-1].orig_range[0] == basic_chunk[i-1].orig_range[1]:
                    all_chunks.append(chunk)
                    continue
                insert_chunk = edit2ChunkInfo(orig_sent,\
                    [chunk.orig_range[0], chunk.orig_range[0], "INSERT", "",None,None,chunk.coder_id],False)
                all_chunks.append(insert_chunk)
                all_chunks.append(chunk)
            if all_chunks[-1].orig_range[0] != all_chunks[-1].orig_range[1]:
                insert_chunk = edit2ChunkInfo(orig_sent,\
                    [len(orig_sent)-1, len(orig_sent)-1, "INSERT", "",None,None,chunk.coder_id],False)
                all_chunks.append(insert_chunk)
            for_all_chunks[sent] = for_all_chunks.get(sent, list())
            for_all_chunks[sent].append(all_chunks)
    return for_all_chunks

# Generate chunk list of each system
# input: args
# output: chunk list of each system
def generate_systems_chunks(args):
    system_chunk = dict()
    sent2num = dict()
    with open(args.hyp) as fp:
        orig_sent = ""
        id2edit = list()
        for line in fp:
            if line == "\n":
                hyp_m2 = list()
                for edits in id2edit:
                    hyp_m2.append('\n'.join(edits))
                error_chunks = generate_error_chunks(hyp_m2,"system")
                all_chunks = generate_all_chunks(error_chunks)
                system_chunk[orig_sent[2:]] = all_chunks[orig_sent[2:]]
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
    return system_chunk
                    
# input1: list of string, original_sentence
# input2: list, shape of [int,int,string,string,int,int,int]
# input3: bool, is this error edit, True is default
def edit2ChunkInfo(sent, edit, error=True):
    info = ChunkInfo()
    info.cat = edit[2]
    info.orig_range = (edit[0], edit[1])
    if info.cat == "noop":
        info.is_error = False
        return info
    info.orig_sent = ' '.join(sent[edit[0]:edit[1]])
    info.gold_range = (edit[4],edit[5])
    info.gold_sent = edit[3]
    info.coder_id = edit[6]
    info.is_error = error

    return info

# get infomation by argparse 
def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ref", required=True)
    parser.add_argument("-hyp", required=True)
    parser.add_argument("-sys_name")
    parser.add_argument("-heat")
    parser.add_argument("-cat")
    parser.add_argument("-gen_w_file")
    parser.add_argument("-w_file")
    parser.add_argument("-verbose", action='store_true')
    
    args = parser.parse_args()
    return args
    
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

    # input: other ChunkInfo instance
    # output: judgement their are equal or not .
    def equal(self, other):
        if other.orig_range == self.orig_range:
            if other.gold_sent == self.gold_sent:
                return "equal"
            else:
                return "cover"
        elif self.orig_range[0] == self.orig_range[1]:
            return "true insert"
        elif self.orig_range[0] <= other.orig_range[0] < self.orig_range[1]:
                return "cover"
        elif other.orig_range[0] <= self.orig_range[0] < other.orig_range[1]:
                return "cover"
        else: return "pass"
    # calculation weight of its chunk
    def cluc_weight(self):
        correct = 0
        for system_id, evalinfo in self.sys2eval.items():
            if evalinfo.is_correct:
                correct += 1
        correct_ans_rate = (correct) / (len(self.sys2eval) )
        self.weight = self.weight_f(correct_ans_rate)
        return 

    def weight_f(self, correct_ans_rate):
        return 1 - correct_ans_rate

    def get_number_of_system(self):
        return len(self.sys2eval)
            

    # debug print
    def show(self,verbose=False):
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
                

class EvalInfo:
    def __init__(self, modefy, correct):
        self.is_modefy = modefy
        self.is_correct = correct

    def show(self):
        print("modfy: ",self.is_modefy, "correct: ",self.is_correct)

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

    def get_RPFA(self):
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
        pass

    def show(self, verbose = False):
        if verbose:
            print("{:.4f}".format(round(self.TP, 3)),
                "{:.4f}".format(round(self.FP, 3)),
                "{:.4f}".format(round(self.FN, 3)),
                "{:.4f}".format(round(self.TN, 3)),
                sep='\t', end='\t')
        print("{:.4f}".format(round(self.Precision, 3)),
                "{:.4f}".format(round(self.Recall,3 )),
                "{:.4f}".format(round(self.F, 3)),
                "{:.4f}".format(round(self.F5, 3)),
                "{:.4f}".format(round(self.Accuracy, 3)),
                sep='\t')
##########################################################################PEP79
def calc_cat_performance(gold_chunks, out_file_name, print_mode = "tsv"):
    # {cat : list()}
    cat2weight_list = toolbox.categories_counter(gold_chunks)
    cat2score = dict() # {cat : [sum, average, SD, size]}
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

def generate_weight_file(gold_chunks, file_name):
    out = open(file_name,"w")
    is_written_number_of_system = True
    for sent, systems_chunks in gold_chunks.items():
        for chunks in systems_chunks:
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


def debug(chunks):
    for sent, systems in chunks.items():
        for system in systems:
            for chunk in system:
                chunk.show(True)
      
if __name__ == "__main__":
    args = get_parser()
    main(args)
    