# 实际验证记录

日期：2026-10-01。环境：Windows，Python 3.13.5。

在本作品目录运行：

```powershell
python -m unittest -v test_csv_cleaner.py
```

结果：12 项测试全部通过，`Ran 12 tests`、`OK`。测试使用临时目录，不改变交付示例。

示例生成命令：

```powershell
python csv_cleaner.py input.csv example-result --trim name --trim email --required name --required email
```

实际输出：

```text
Saved 5 rows to example-result; removed 1 duplicates, changed 6 fields, flagged 2 rows for review.
```

`quality_report.json`：输入 6 行，输出 5 行，发现/删除重复各 1 行，变更 3 行中的 6 个字段，待复核 2 行。五个固定输出文件均已生成。

报告路径审查后，`input_file` 改为只保存 `input.csv`，新增文件名断言并重跑 12 项测试，全部通过。随后在工作临时目录重新运行示例，仅将重新生成的 `quality_report.json` 同步到交付示例；统计保持一致。
