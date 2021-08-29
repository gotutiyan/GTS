class ChunkInfo:
    def __init__(self, orig_range: tuple, orig_sent: str, gold_sent: str, is_modified: bool):
        self.orig_range = orig_range # tuple: (start, end)
        self.orig_sent = orig_sent # str
        self.gold_sent = gold_sent # str
        self.cat = ""
        self.coder_id = -1
        self.is_modified = is_modified
        self.sys2eval = []
        self.weight = -1
        self.n_correct = 0
    
    def is_insert_chunk(self) -> bool:
        return self.orig_range[0] == self.orig_range[1]

    def compare(self, other) -> str:
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
                '''
                         "aaa"
                self:  |-------|
                         "aaa"
                other: |-------|
                '''
                return "equal"
            else:
                '''
                         "aaa"
                self:  |-------|
                         "bbb"
                other: |-------|
                '''
                return "not-equal"
        elif self.orig_range[0] == self.orig_range[1]:
            return "pass"
        elif self.orig_range[0] <= other.orig_range[0] < self.orig_range[1]:
            '''
            self:  |-------|
                    
            other: |-----|
            other: |---------|
            other:   |---|
            other:   |-------|
            '''
            return "not-equal"
        elif other.orig_range[0] <= self.orig_range[0] < other.orig_range[1]:
            '''
            self:     |-------|
                    
            other:    |---------|
            other:    |----|
            other: |-----|
            other: |--------------|
            '''
            return "not-equal"
        else:
            return "pass"

    def calc_weight(self, a: float, b: float, c: float) -> None:
        n_correct = 0
        for eval_info in self.sys2eval:
            if eval_info.is_correct:
                n_correct += 1
        self.n_correct = n_correct
        self.weight = self.weight_f(n_correct, len(self.sys2eval), a, b, c)
        return 

    def weight_f(self, n_i: int, N: int, a: float, b: float, c: float) -> float:
        '''Calcurate correction difficulty based on correction success rate.
        '''
        return a - (n_i + b) / (N + c)

    def get_number_of_system(self) -> int:
        return len(self.sys2eval)

    def show(self, verbose=False) -> None:
        print("orig_range: ", self.orig_range,\
        "\norig_sent:", self.orig_sent,\
        "\ngold_sent:", self.gold_sent,\
        "\ncat:", self.cat,\
        "\ncoder_id:", self.coder_id,\
        "\nis_modified:", self.is_modified,\
        "\nweight:", self.weight,\
        "\nn_correct:", self.n_correct)
        if verbose:
            for system_id, evalinfo in enumerate(self.sys2eval):
                print("system_id:", system_id, end="| ")
                evalinfo.show()
        print("\n")
        return
                

class EvalInfo:
    def __init__(self, is_modified: bool, is_correct: bool, judge: bool):
        self.is_modified = is_modified
        self.is_correct = is_correct
        self.judge = judge

    def show(self) -> None:
        print("is_modified: {}, is_correct: {}, judge: {}".format(
            self.is_modified,
            self.is_correct,
            self.judge))
        return


class Score:
    def __init__(self, sys_id):
        self.sys_id = sys_id
        self.TP = 0
        self.TN = 0
        self.FP = 0
        self.FN = 0
        self.all_weight = 0
        self.Precision = 0
        self.Recall = 0
        self.Accuracy = 0
        self.F = 0
        self.F05 = 0
        self.test = 0

    def get_PRFA(self) -> None:
        try:
            self.Precision = (self.TP)/(self.TP+self.FP)
        except ZeroDivisionError:
            self.Precision = 0
        try:
            self.Recall = (self.TP)/(self.TP+self.FN)
        except ZeroDivisionError:
            self.Recall = 0
        try:
            self.F = 2*self.Precision*self.Recall/(self.Precision + self.Recall)
        except ZeroDivisionError:
            self.F = 0
        try:
            self.F05 = float(1.25*self.Precision*self.Recall)\
            / (0.25*self.Precision + self.Recall)
        except ZeroDivisionError:
            self.F5 = 0
        try:
            self.Accuracy = (self.TP + self.TN) / self.all_weight
        except ZeroDivisionError:
            self.Accuracy = 0
        return

    def show(self, verbose=False) -> None:
        if verbose:
            print("{:8.4f}".format(self.TP),
                "{:8.4f}".format(self.FP),
                "{:8.4f}".format(self.FN),
                "{:8.4f}".format(self.TN),
                sep='\t', end='\t')
        print("{:.4f}".format(self.Precision),
                "{:.4f}".format(self.Recall),
                "{:.4f}".format(self.F),
                "{:.4f}".format(self.F05),
                "{:.4f}".format(self.Accuracy),
                sep='\t')
        return
