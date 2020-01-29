# Go-To-Scorer
本リポジトリは，「訂正難易度を考慮した文法誤り訂正のための性能評価尺度」（言語処理学会第26回年次大会）のツールである．

### 実行要件

python 3.6 以上

### 文法

```bash
python3 gotoscorer.py -ref <ref_m2> -hyp <hyp_m2> -sys_name sys_1,sys_2,...,sys_N 
```

`-ref`， `-hyp` ，`-sys_name`は必須である．

`<ref_m2>`の例を`demo/ref.m2`に，`<hyp_m2>`の例を`demo/hyp.m2`に示している．

他には，以下のオプションを提供している．

* `-heat <out_file>`

  重みを表すヒートマップ を出力する．これは論文中の図1に対応する．htmlファイルと，それに対応するcssファイルが得られる．出力例は，`demo/heat_map.html`および`demo/heat_map.html.css`を参照．

* `-cat <out_file>`

  誤りの種類ごとに，訂正難易度の平均と標準偏差を昇順で出力する．これは論文中の表3のようなものである．出力例は，`demo/error_type_difficulty.txt`を参照．

* `-gen_w_file <out_file>`

  重みファイルを出力する．重みファイルのフォーマットは，1行目にシステムの総数，2行目以降は，チャンクごとの重みが記述されている．また，各行が文に対応している．出力例は，`demo/weight.txt`を参照．

* `-w_file <w_file>`

  重みファイルを用いて性能評価を行う．

### 入力ファイルのフォーマットと生成

本ツールの入力は2つのファイルであり，いずれもフォーマットはm2形式である．また，いずれも[ERRANT](https://github.com/chrisjbryant/errant)の`errant_parallel`，および`errant_m2`を用いて生成する．

**例**

 `errant_parallel -orig demo/orig.txt -cor demo/sys1.txt demo/sys2.txt demo/sys3.txt -out demo/hyp.m2`

`errant_parallel -orig demo/orig.txt -cor demo/gold.txt -out ref.m2`

また，正解の訂正情報がm2形式で既に存在するとき，

`errant_m2 -gold <before_ref_m2_file> -out ref.m2`

を実行する．このようにして得られたファイルを用いて評価を行う．

### ヒートマップ

ヒートマップ は，主に分析を行う上で有用なツールである．

原文に対して，赤および青で色付けが行われており，いずれも色が濃くなるほど訂正難易度が高いことを表す．また，色付けされた単語列にマウスをかざすことにより，その訂正箇所の(i)誤り種類，(ii)正解単語列，(iii)重み，の情報が閲覧できる．

また，赤色は誤り箇所に対するもの，青色はシステムの誤訂正に対するものを表している．

