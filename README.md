# ExcelMonitor

## 功能说明

读取表格，依据配置文件预设好的筛选条件进行计数，单日多次执行只保留最新结果，理论上可以直接用结果来生成变化曲线

main.py 条件筛选主程序，内有路径适配逻辑，可直接使用pyinstaller打包成单文件

```
pyinstaller -F main.py
```

graph_drawer.py 折线图绘制程序，暂时不可打包成单文件，需要使用python运行，生成html格式的折线图

## 文件说明

### config.json

路径：`./config/config.json`

用于记录配置，详情如下

```json
{
  "path_url": "./示例文档.xlsx",
  "sheet_name": "人员信息",
  "filter_groups": [
    {
      "tag": "已在职的男性员工",
      "conditions": {
        "是否在职": ["是"],
        "性别": ["男"]
      }
    },
    {
      "tag": "已在职的女性员工",
      "conditions": {
        "是否在职": ["是"],
        "性别": ["女"]
      }
    }
  ]
}
```

| 键            | 含义             | 类型   |
| ------------- | ---------------- | ------ |
| path_url      | 读取表格路径     | string |
| sheet_name    | 子表名称         | string |
| filter_groups | 筛选条件记录列表 | list   |
| tag           | 备注             | string |
| conditions    | 条件，支持多选   | list   |

### filter_result.json

路径`./result/filter_result.json`

示例结果如下

```json
[
  {
    "path_url": "./示例文档.xlsx",
    "sheet_name": "人员信息",
    "date": "2025-08-11",
    "tag": "已在职的男性员工",
    "filter_conditions": {
      "是否在职": [
        "是"
      ],
      "性别": [
        "男"
      ]
    },
    "matched_count": 3
  },
  {
    "path_url": "./示例文档.xlsx",
    "sheet_name": "人员信息",
    "date": "2025-08-11",
    "tag": "已在职的女性员工",
    "filter_conditions": {
      "是否在职": [
        "是"
      ],
      "性别": [
        "女"
      ]
    },
    "matched_count": 3
  }
]
```

| 键                | 含义         | 类型   |
| ----------------- | ------------ | ------ |
| path_url          | 读取表格路径 | string |
| sheet_name        | 子表名称     | string |
| filter_conditions | 筛选条件记录 | list   |
| tag               | 备注         | string |
| matched_count     | 匹配数量     | int    |
| date              | 数据获取日期 | date   |

