# 中文简历实体识别训练说明

当前目录用于训练最终版 `ALBERT-BiGRU-CRF` 模型。当前阶段只准备训练框架和样例数据，不启动训练。

## 目录结构

- `configs/train_config.json`：训练配置
- `dataset.py`：JSONL 数据读取与标签对齐
- `train.py`：训练入口
- `validate.py`：验证入口
- `export_artifacts.py`：导出推理所需资源

## 数据格式

训练和验证数据位于 `../data/annotations/`，每行一个 JSON 对象：

```json
{
  "text": "张三，武汉大学本科，2年新媒体运营实习经验，熟悉剪映和Photoshop。",
  "entities": [
    { "start": 0, "end": 2, "label": "NAME" },
    { "start": 3, "end": 7, "label": "SCHOOL" },
    { "start": 7, "end": 9, "label": "DEGREE" },
    { "start": 10, "end": 19, "label": "EXPERIENCE_YEARS" },
    { "start": 22, "end": 24, "label": "SKILL" }
  ]
}
```

## 推荐步骤

1. 继续补充中文技术岗/运营岗简历样本并完成标注。
2. 周末回家后执行训练脚本。
3. 训练完成后运行导出脚本，将权重和 tokenizer 导出到 `../model/artifacts/`。
