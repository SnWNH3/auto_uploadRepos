import json
import ast

INPUT_JSON = "input.json"
FAIL_LIST = "fail.txt"
OUTPUT_JSON = "failed_upload_repos.json"

# 1. 读取失败仓库列表，解析为Python列表，并统计数量
with open(FAIL_LIST, "r", encoding="utf-8") as f:
    content = f.read().strip()
fail_repos = ast.literal_eval(content)
total_fail_count = len(fail_repos)
print(f"失败列表中总计记录仓库数量：{total_fail_count}")

# 2. 读取原始仓库数据
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    all_repos = json.load(f)

# 3. 筛选：仅保留上传失败的仓库
filtered_repos = [repo for repo in all_repos if repo["repo_id"] in fail_repos]
match_count = len(filtered_repos)
print(f"在 input.json 中匹配到的失败仓库数量：{match_count}")

# 4. 保存筛选结果到新文件
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(filtered_repos, f, ensure_ascii=False, indent=2)