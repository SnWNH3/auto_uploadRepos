import requests
import json
import time

# ===================== 可配置项=====================================
SEARCH_QUERY = "in:description CNC"  # GitHub搜索关键词
MAX_RESULTS = 25              # 最大获取仓库数量
DOMAIN_TAGS = ["CAD"]                  # domain标签
TASK_TAGS = ["CNC加工","plh"]             # task标签
# ==================================================================

# GitHub API基础配置
base_url = "https://api.github.com/search/repositories"
params = {
    "q": SEARCH_QUERY,
    "per_page": 100,
    "page": 1,
    "sort": "stars",
    "order": "desc"
}
headers = {"User-Agent": "My-CAD-Search-Tool"}
all_repos = []

# 1. 调用GitHub API获取仓库数据
while True:
    response = requests.get(base_url, params=params, headers=headers)
    data = response.json()
    current_items = data.get("items", [])
    all_repos.extend(current_items)

    # 终止条件
    if not current_items or len(all_repos) >= MAX_RESULTS:
        all_repos = all_repos[:MAX_RESULTS]
        break

    print(f"已获取第 {params['page']} 页，累计 {len(all_repos)} 条仓库数据")
    params["page"] += 1
    time.sleep(0.2)

# 2. 转换为input.json格式
input_data = []
for repo in all_repos:
    input_data.append({
        "repo_id": repo.get('full_name', ''),
        "repo_type": "model",
        "endpoint": "github",
        "description": str(repo.get('description', '')).strip(),
        "tags": {
            "domain": DOMAIN_TAGS,
            "task": TASK_TAGS,
            "license": ["apache-2.0"],
            "language": [""]
        }
    })

# 3. 保存input.json
with open('input.json', 'w', encoding='utf-8') as f:
    json.dump(input_data, f, ensure_ascii=False, indent=2)

# 输出结果提示
print(f"\n ✅数据抓取完成：共获取 {len(all_repos)} 条仓库数据")
print(f"✅ 成功生成input.json：包含 {len(input_data)} 条记录")