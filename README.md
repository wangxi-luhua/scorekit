# scorekit

从论文表格里抄下来的分数，逐条校验 + 汇总：读 jsonl，每行走两道关（JSON 语法、字段语义），输出合格率与平均分。

用于复现实验时录入 baseline 分数——手抄表格最容易出两类错：**抄错数字**（`-3`、`85.8` 写成字符串）和**抄串行**（多列子表头没对齐）。这个工具把这两类错变成当场报错，而不是等到算平均分时才发现。

## 快速开始

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

跑单个文件：

```bash
python -m scorekit.checker --input data/scores.jsonl
```

一次跑多个文件（并发，每个文件一个线程）：

```bash
python -m scorekit.checker --input data/scores.jsonl data/bad_all.jsonl
```

输出示例（真实运行结果）：

```
INFO - 总共8行数据，6行数据有效
INFO - 逻辑平均分是85.80
INFO - 结构平均分是94.10
INFO - data/scores.jsonl -> 共8行，6行有效，逻辑均分85.80，结构均分94.10
INFO - data/bad_all.jsonl -> 共2行，0行有效，逻辑均分0.00，结构均分0.00
```

可选参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--input` | `data/scores.jsonl` | 输入 jsonl 路径，可传多个 |
| `--level` | `INFO` | 日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `--logfile` | `app.log` | 日志文件路径 |

## 数据格式

每行一个 JSON 对象：

```json
{"method": "PatchCore", "logical": 85.8, "structural": 94.1}
```

三个字段都是必填，`logical` / `structural` 必须是 `0~100` 的数字（`strict` 模式下字符串 `"85.8"` 不认）。

## 行为约定

**两道校验，各管一类错**

| 关 | 检查什么 | 失败时抛 |
|---|---|---|
| 语法 | 这一行是不是合法 JSON | `JSONDecodeError` |
| 语义 | 字段齐不齐、类型对不对、值在不在范围内 | pydantic `ValidationError` |

两个异常都只捕获各自那一种，不用 `except Exception` 兜底——宁可崩，不要让坏数据被静默吞掉。

**两个数字口径不同**

- `total_lines`：文件里有内容的行数，**坏行也计入**（这是数量口径，反映数据规模）
- `valid_count` / 合格率：通过校验的行数（这是质量口径，反映数据质量）

坏行不计入总数，合格率就会虚高——所以两者必须分开。

**退出码有语义**

| 退出码 | 含义 |
|---|---|
| `0` | 所有文件都有有效数据 |
| `1` | 有文件一行有效数据都没有，或文件不存在 |
| `2` | 参数敲错（argparse 自动处理） |

**并发**

`asyncio.gather` + `asyncio.to_thread`：每个文件交给一个后台线程校验，`validate_file` 本身保持同步、不感知并发。调度与校验分层，所以并发改造没有动一行校验逻辑。

## 测试

```bash
python -m pytest -q
```

6 个测试：正常数据、好坏混合、末尾空行、坏 JSON、全坏、文件不存在。覆盖的是口径本身（坏行不许算有效行、空行不许计数、全坏时返回空结果而不是除零、文件缺失要往上抛异常而不是自己退出）。

## 项目结构

```
scorekit/
├── scorekit/
│   ├── __init__.py
│   └── checker.py        # 校验 + CLI
├── tests/
│   └── test_checker.py
├── data/                 # 示例数据（含故意构造的坏行）
├── requirements.txt
└── README.md
```

## 环境

Python 3.13，依赖 `pydantic 2.14`、`pytest 9.2`，见 `requirements.txt`。
