# 中文简历标注说明

当前阶段先准备中文简历标注数据，不启动训练。建议优先收集并标注技术岗、运营岗、产品岗简历。

## 标签集

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

## 标注建议

1. 文本统一按最终解析后的中文纯文本标注。
2. 起止位置使用 Python 字符串切片规则：`start` 包含，`end` 不包含。
3. 项目描述、实习描述、工作描述中的技能词要单独标出为 `SKILL`。
4. 工作年限、实习年限等可统一标注为 `EXPERIENCE_YEARS`。
