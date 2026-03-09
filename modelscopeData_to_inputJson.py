import json

# 配置常量
INPUT_PATH = "modelscope_repoData.json"
OUTPUT_PATH = "input.json"
# 100GB 对应的字节数
SIZE_LIMIT = 100 * 1024 ** 3

# 读取原始JSON数据
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

result = []
# 遍历过滤并转换格式
for item in raw_data:
    namespace = item["Namespace"]
    # 过滤条件1：排除包含code/Code的Namespace
    if "code" in namespace.lower():
        continue
    # 过滤条件2：排除超过100GB的数据集
    if item["StorageSize"] > SIZE_LIMIT:
        continue

    # 构造目标格式数据
    converted = {
        "repo_id": f"{namespace}/{item['Name']}",
        "repo_type": "dataset",
        "endpoint": "modelscope",
        "description": item["Description"],
        "tags": {
            "domain": ["航空软件"],
            "task": ["Code"],
            "license": ["apache-2.0"],
            "language": [""]
        }
    }
    result.append(converted)

print(f"✅ 成功生成了 {len(result)} 条记录")

# 保存结果到文件
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)