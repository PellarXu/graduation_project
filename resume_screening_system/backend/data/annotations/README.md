# 中文简历标注数据说明

当前目录用于存放中文简历命名实体识别训练数据，供 `ALBERT-BiGRU-CRF` 模型训练使用。

## 标签集合

- `NAME`
- `PHONE`
- `EMAIL`
- `DEGREE`
- `MAJOR`
- `SCHOOL`
- `COMPANY`
- `TITLE`
- `SKILL`
- `PROJECT`
- `EXPERIENCE_YEARS`
- `GENDER`
- `AGE`
- `HOMETOWN`

## 数据格式

- `train.jsonl` 和 `dev.jsonl` 均为 JSON Lines 格式
- 每行一个样本，字段固定为：
  - `text`：中文简历纯文本
  - `entities`：实体列表，包含 `start`、`end`、`label`
- 实体边界使用 Python 切片规则：`start` 包含，`end` 不包含

## 数据来源

- 当前训练数据以手工改写的中文简历样本为主
- 少量表达参考公开招聘场景中的常见写法，但不会直接保留真实个人隐私内容
- 可通过 `training/generate_annotations.py` 重新生成一版基准训练集和验证集
