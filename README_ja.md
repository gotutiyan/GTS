# Go-To-Scorer

本リポジトリは，以下の論文のツールである．

* 五藤巧, 永田亮, 三田雅人, 塙一晃．
  “訂正難易度を考慮した文法誤り訂正のための性能評価尺度．”
  言語処理学会第26回年次大会 (2020.3)
* Takumi Gotou, Ryo Nagata, Masato Mita and Kazuaki Hanawa
  “Taking the Correction Difficulty into Account in Grammatical Error Correction Evaluation”
  In Proceedings of the 28th International Conference on Computational Linguistics (COLING 2020) 

### 文法

```bash
python3 gotoscorer.py -ref <ref_m2> -hyp <hyp_m2>
```

`-ref <ref_m2>`は正解の訂正を表すファイル，`-hyp <hyp_m2>`はシステムの訂正を表すファイルである．どちらのファイルも，[ERRANT](https://github.com/chrisjbryant/errant)により生成されるM2形式である．各ファイルの例は，`demo/ref.m2`および`demo/hyp.m2`を参照．

`-ref`， `-hyp` はいずれも必須である．

### その他のオプション

* `-sys_name <sys_1,sys_2,...,sys_N>`

  システムの名前をIDから指定した文字列に変換して出力する．カンマ区切りで指定．

* `-heat <out_file>`

  訂正難易度を可視化するビジュアライザーを生成する．これは論文中の図1に対応する．出力例は，`demo/heat_map.html`および`demo/heat_map.html.css`を参照．

* `-cat <out_file>`

  誤り種類ごとに，訂正難易度の平均と標準偏差を降順で出力する．これは論文中の表3に対応する．出力例は，`demo/error_type_difficulty.txt`を参照．

* `-gen_w_file <out_file>`

  重みファイルを出力する．1行目にシステムの総数，2行目以降に，各チャンクの正解システム数が記述される形式である．また，各行が文に対応している．出力例は，`demo/weight.txt`を参照．

* `-w_file <w_file>`

  重みファイルを用いて性能評価を行う．これはシステムを単一で評価する際に役立つ．

### デモ

`python3 gotoscorer.py -ref demo/ref.m2 -hyp demo/hyp.m2 -sys_name sys1,sys2,sys3` 

出力例：

![output_format](./image/output_format.png)

### 入力ファイルのフォーマットと生成

GTSは`-ref`と`-hyp`の2つのファイルを必須入力としている．いずれもフォーマットは[ERRANT](https://github.com/chrisjbryant/errant)が生成するm2形式である．

**デモデータを用いた例**

* `demo/hyp.m2`の生成例

 `errant_parallel -orig demo/orig.txt -cor demo/sys1.txt demo/sys2.txt demo/sys3.txt -out demo/hyp.m2`

* `demo/ref.m2`の生成例

`errant_parallel -orig demo/orig.txt -cor demo/gold.txt -out demo/ref.m2`

### 訂正難易度のビジュアライザー

本ツールでは，訂正難易度のビジュアライザーを提供している．

誤りに対して色付けされており，濃い色であるほど訂正難易度が高いことを表す．また，赤は訂正すべき単語列（`ref_m2`に記載の誤り），青は訂正すべきでない単語列を表す．また，色付けされた単語列にマウスをかざすことにより，その訂正箇所の詳細が表示される：(i)誤り種類，(ii)正解の訂正，(iii)訂正難易度．

![heat_map](./image/heat_map.gif)