# GoToScorer

Code for the [paper](https://www.aclweb.org/anthology/2020.coling-main.188/):

Takumi Gotou, Ryo Nagata, Masato Mita and Kazuaki Hanawa
“Taking the Correction Difficulty into Account in Grammatical Error Correction Evaluation”
In Proceedings of the 28th International Conference on Computational Linguistics (COLING 2020)

```
@inproceedings{gotou-etal-2020-taking,
    title = "Taking the Correction Difficulty into Account in Grammatical Error Correction Evaluation",
    author = "Gotou, Takumi  and
      Nagata, Ryo  and
      Mita, Masato  and
      Hanawa, Kazuaki",
    booktitle = "Proceedings of the 28th International Conference on Computational Linguistics",
    month = dec,
    year = "2020",
    address = "Barcelona, Spain (Online)",
    publisher = "International Committee on Computational Linguistics",
    url = "https://aclanthology.org/2020.coling-main.188",
    doi = "10.18653/v1/2020.coling-main.188",
    pages = "2085--2095",
}
```

GoToScorer can evaluate the GEC systems performances considering the difficulty of error correction.

It is confirmed to work with python 3.8.0.

### Usage

```bash
python gotoscorer.py -ref <ref_file> -hyp <hyp_file>
```

`-ref <ref_file>` represents a reference M2 file and `-hyp <hyp_file>` represents a hypothesis M2 file. You can generate both of files by [ERRANT](https://github.com/chrisjbryant/errant). You can see `demo/ref.m2` and `demo/hyp.m2` for an example. 

### Quick Start

```shell
$ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2
```

Output:

```
----- Weighted Scores -----
Sys_name	Prec. 	Recall	F	F0.5	Accuracy
0       :	1.0000	0.4444	0.6154	0.8000	0.5833
1       :	0.2500	0.2222	0.2353	0.2439	0.2500
2       :	0.0000	0.0000	0.0000	0.0000	0.1667
```

### Other options

* `-v`

  The output includes TP, FP, FN and TN.

  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -v
  ```

  ```
  ----- Weighted Scores -----
  Sys_name	  TP      	  FP      	  FN      	  TN      	Prec.	Recall	F	F0.5	Accuracy
  0       :	  1.3333	  0.0000	  1.6667	  1.0000	1.0000	0.4444	0.6154	0.8000	0.5833
  1       :	  0.6667	  2.0000	  2.3333	  0.3333	0.2500	0.2222	0.2353	0.2439	0.2500
  2       :	  0.0000	  2.6667	  3.0000	  0.6667	0.0000	0.0000	0.0000	0.0000	0.1667
  ```

* `-name <sys_1,sys_2,...,sys_N>` 

  Register system names for output to convert id to specified. Separate each name with comma.

  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -name CNN,LSTM,Transformer
  ```

  ```
  ----- Weighted Scores -----
  Sys_name   	Prec.	Recall	F	F0.5	Accuracy
  CNN        :	1.0000	0.4444	0.6154	0.8000	0.5833
  LSTM       :	0.2500	0.2222	0.2353	0.2439	0.2500
  Transformer:	0.0000	0.0000	0.0000	0.0000	0.1667
  ```

* `-cat {1,2,3}`

  Compute mean and standard deviation of each error type difficulty in descending order. `{1,2,3}` is granularity of error type, same behavior of ERRANT.

  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -cat 3
  ```

  ```txt
  ----- Category Difficulty -----
  Category  	Ave.	Std.	Freq.
  U:NOUN    	1.00	0.00	1
  M:VERB    	0.67	0.00	1
  U:PREP    	0.67	0.00	1
  R:VERB    	0.67	0.00	1
  R:PRON    	0.00	0.00	1
  M:DET     	0.00	0.00	1
  ```

* `-heat <output_file>`

  Generate a heat map of error correction difficulty. You can see `demo/heat_map.html` for an example.

  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -heat demo/heat_map.html
  ```

* `-gen_w_file <output_file>`

  Generate a weight-file. Originally, multiple systems outputs are required to calculate the correction difficulty, but a single system can be evaluated by using a pre-made weight-file. You can see `demo/weight.txt` for an example.

  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -gen_w_file demo/weight.txt 
  ```

* `-w_file <weight_file>`

  Evaluate a system using a weight-file. 
  
  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp_1sys.m2 -w_file demo/weight.txt 
  ```
  
  ```
  ----- Weighted Scores -----
  Sys_name	Prec.	Recall	F	F0.5	Accuracy
  0       :	1.0000	0.4444	0.6154	0.8000	0.5833
  ```
  
* `-cv <output_file>`

  Visualize the chunk with weight and error type, as shown in the following example. If you specify `None` as the file path, the output will be on the terminal.

  ```shell
  $ python gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -cv None
  ```
  
  ```
  ----- Chunk Visualizer -----
  orig:   |    |We |         |discussing|   |about |   | its  |   | . |    |
  gold:   |    |We |have been|discussing|   |      |   |  it  |   | . |    |
  weight: |0.33|0.0|  0.67   |   0.33   |0.0| 0.67 |0.0| 0.0  |0.0|0.0|0.33|
  cat:    |    |   | M:VERB  |          |   |U:PREP|   |R:PRON|   |   |    |
  
  orig:   |   | I |   |have been|   |to |     |park|   |tomorrow|   | . |   |
  gold:   |   | I |   |   go    |   |to | the |park|   |        |   | . |   |
  weight: |0.0|0.0|0.0|  0.67   |0.0|0.0| 0.0 |0.0 |0.0|  1.0   |0.0|0.0|0.0|
  cat:    |   |   |   | R:VERB  |   |   |M:DET|    |   | U:NOUN |   |   |   |
  ```

### How to make M2 file

GTS requires reference M2 and hypothesis M2. You can make these files using [ERRANT](https://github.com/chrisjbryant/errant).

**Example for generating M2 files with demo data**

* Generating `demo/hyp.m2`

   ```shell
   $ errant_parallel -orig demo/orig.txt -cor demo/sys1.txt demo/sys2.txt demo/sys3.txt -out demo/hyp.m2
   ```

* Generating `demo/ref.m2`

  ```shell
  $ errant_parallel -orig demo/orig.txt -cor demo/gold.txt -out demo/ref.m2
  ```

  In general, it is unlikely to be generated in this way, since existing correct answer files are used as references.

### Visualizer of error correction difficulty

GTS provides a visualizer of error correction difficulty.
Errors are colored according to the success rate: pale (easier) to deep (harder).  Furthermore, the red indicates errors what should be corrected (TP, FN), and the blue indicates that system has corrected what should not be corrected (FP). If you mouseover colored words, you can see the detail of the correction: an error type, a correct correction, a weight.

![heat_map](./image/heat_map.gif)
