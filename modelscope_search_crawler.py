import requests
import json
import time

# ===================== 仅保留4个核心配置项 =====================
SEARCH_QUERY = "code"                  # 魔搭检索关键词
MAX_RESULTS = 2                        # 最大获取数据量
DOMAIN_TAGS = ["工业数据分析"]          # domain标签
TASK_TAGS = ["化工", "plh"]             # task标签
# =================================================================

BASE_URL = "https://www.modelscope.cn/api/v1/dolphin/datasets"
params = {
    "PageSize": 80,
    "PageNumber": 1,
    "Target": "",
    "Query": SEARCH_QUERY
}
all_raw_data = []
SIZE_LIMIT = 100 * 1024 ** 3  # 固定100GB过滤（原脚本逻辑）

# 1. 分页获取魔搭数据
while True:
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    page_data = response.json()
    current_items = page_data.get("Data", [])

    if not current_items:
        break
    all_raw_data.extend(current_items)
    
    if len(all_raw_data) >= MAX_RESULTS:
        all_raw_data = all_raw_data[:MAX_RESULTS]
        break
    
    params["PageNumber"] += 1
    time.sleep(0.2)

# 2. 过滤+转换为input.json格式
result = []
for item in all_raw_data:
    namespace = item.get("Namespace", "")
    # 过滤含code的Namespace+超100GB数据（原脚本逻辑）
    if "code" in namespace.lower() or item.get("StorageSize", 0) > SIZE_LIMIT:
        continue
    
    result.append({
        "repo_id": f"{namespace}/{item.get('Name', '')}",
        "repo_type": "dataset",
        "endpoint": "modelscope",
        "description": str(item.get("Description", "")).strip(),
        "tags": {
            "domain": DOMAIN_TAGS,
            "task": TASK_TAGS,
            "license": ["apache-2.0"],
            "language": [""]
        }
    })

# 3. 保存文件（保留原始数据文件，和你原脚本一致）
with open("modelscope_repoData.json", "w", encoding="utf-8") as f:
    json.dump(all_raw_data, f, ensure_ascii=False, indent=2)
with open("input.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# 极简输出提示
print(f"✅ 数据获取完成：{len(all_raw_data)} 条原始数据")
print(f"✅ input.json生成完成：{len(result)} 条有效数据")