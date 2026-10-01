# CSV 清理工具演示

[English guide](./README_EN.md)

这是一个 **AI 辅助制作的普通开发作品演示**，用于展示需求边界、可追溯处理和基本交付质量。它不是客户项目经历、客户评价或收入证明。示例全部是合成数据；邮箱使用 `.test` 域名，不含客户隐私。

## 能做什么

- 只对通过 `--trim` 明确指定的列去掉首尾空白，保留内部空格。
- 对清理后完整的一行做精确去重，保留第一次出现的行；大小写不同或任一字段不同都会保留。可以关闭去重。
- 全程使用字符串，保留 `0007` 这样的 ID 前导零；不猜日期、金额，不填补缺失值。
- 把 `--required` 指定列中的空字符串或纯空白标记为待复核；这些记录仍保留在 `cleaned.csv` 中。正常去重规则仍适用。
- 读取 UTF-8 或 UTF-8 BOM 的逗号分隔 CSV。输出 CSV 采用 UTF-8 BOM。
- 拒绝空表头、空列名、重复列名（比较时忽略首尾空白）、未知列名、字段数量不符及解析器识别出的 CSV 语法错误。完全空白的物理记录会因字段数量不符而拒绝。
- 只有输入完整验证通过后才创建新的输出目录；任何已存在的输出目录都会拒绝，避免覆盖。

这是 CSV 专用小工具，不读取 XLSX，也不自动识别编码或分隔符。单列 CSV 合法，无法仅凭内容可靠区分单列 CSV 与其他分隔格式；指定所需列可验证结构。输入有表头，列名区分大小写并按原样匹配。不做类型转换、模糊去重或跨文件合并。CSV 保留文本前导零；电子表格软件自行推断类型可能改变显示，应通过文本导入指定 ID 为文本。

## 运行

需要 Python 3.9 或更新版本，无第三方依赖。在此目录打开终端：

```powershell
python csv_cleaner.py input.csv my-result --trim name --trim email --required name --required email
```

`my-result` 必须不存在。重复运行时换一个目录名，例如 `my-result-2`。参数可重复，含空格的列名加引号。默认 `--encoding utf-8-sig` 同时接受带 BOM 和不带 BOM 的 UTF-8。

保留重复记录：

```powershell
python csv_cleaner.py input.csv result-all --trim name --trim email --required email --keep-duplicates
```

查看帮助或运行测试：

```powershell
python csv_cleaner.py --help
python -m unittest -v test_csv_cleaner.py
```

错误时返回退出码 2，并给出原因；不会以猜测的方式修补错误。写文件期间磁盘/权限错误可能留下不完整的新目录，应检查后换一个新目录重试。输入文件只读。

## 固定输出文件

| 文件 | 内容 |
| --- | --- |
| `cleaned.csv` | 原始表头和保留的完整记录，保持原有顺序 |
| `removed_duplicates.csv` | 被移除行的源文件起始行号、首次保留行号、清理后的完整记录 JSON 数组 |
| `changes.csv` | 所有输入记录逐字段的旧值、新值和源行号，包含随后被去重的记录 |
| `quality_report.json` | 输入/输出记录数、发现/删除重复数、变更记录/字段数、待复核记录数及规则 |
| `review.csv` | 保留记录的源行号、缺失列名 JSON 数组、完整记录 JSON 数组 |

证据 CSV 使用固定元数据列及 JSON 数组，避免与输入列名冲突。JSON 数组字段的顺序与输入表头相同。源行号为原文件物理行号，表头通常是第 1 行；带引号的多行字段以记录开始行计数。`review_rows` 是最终保留记录中的待复核数。`duplicate_rows` 在关闭去重时仍统计发现的重复数，`removed_rows` 为实际删除数。空报告仍带表头。

报告的 `input_file` 仅记录输入文件名，不包含本机目录路径。

## 已附的示例结果

`input.csv` 包含 6 条合成记录：相同 ID 的清理后重复记录、缺失邮箱、缺失姓名/邮箱、中文、带逗号的字段、多种日期/金额文本以及同名不同 ID。

附带 `example-result/` 是用以下命令实际生成的：

```powershell
python csv_cleaner.py input.csv example-result --trim name --trim email --required name --required email
```

实际结果：读取 6 行，保留 5 行，移除 1 条重复，修改 6 个字段，标记 2 行待复核。ID、日期、金额、备注中的原始空白均保持原样。示例结果目录已存在，不能直接覆盖；复现时把输出名称换成新的目录。

测试覆盖 ID 与文本格式保留、选择性 trim、完整行去重/关闭去重、缺失记录保留、非法结构/编码拒绝、文件保护、UTF-8 BOM、多行记录行号及空数据报告。
