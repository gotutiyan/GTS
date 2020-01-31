# デモ

* 性能評価値を出力し，訂正難易度可視化のためのhtmlおよびcss(`-heat`)，誤り種類別の訂正難易度を可視化する(`-cat`)．および，訂正難易度データを生成する(`-gen_w_file`)．

  （実行はこのdemoフォルダ内で行うことを仮定）

```bash
python3 ../gotoscorer.py -ref ./ref.m2 -hyp ./hyp.m2 -sys_name system1,system2,system3 -heat ./heat_map.html -cat ./error_type_difficulty.txt -gen_w_file ./weight.txt
```

出力例

```
,TP,FP,FN,TN,Precision,Recall,F,F0.5,Accuracy
weighted
system1, 1.3333, 0, 1.6667, 1.0, 1.0, 0.4444, 0.6154, 0.8, 0.5833
system2, 0.6667, 2.0, 2.3333, 0.3333, 0.25, 0.2222, 0.2353, 0.2439, 0.25
system3, 0.0, 2.6667, 3.0, 0.6667, 0.0, 0.0, 0, 0, 0.1667
```

* 訂正難易度データを用いて評価を行う．

```bash
python3 ../gotoscorer.py -ref ./ref.m2 -hyp ./w_file_hyp.m2 -sys_name system1 -w_file ./weight.txt
```

出力例

```
,TP,FP,FN,TN,Precision,Recall,F,F0.5,Accuracy
weighted
system1, 1.3333, 0, 1.6667, 1.0, 1.0, 0.4444, 0.6154, 0.8, 0.5833
```

