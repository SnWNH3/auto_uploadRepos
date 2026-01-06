import json

# 使用三引号的多行字符串
repo_list_text = """
AI-ModelScope/multimodal_textbook
OpenDataLab/K12textbook
MedRAG/textbooks
deepmath/mp-textbooks
HuggingFaceTB/cosmopedia_web_textbooks
"""

# 分割成列表，过滤空行
repo_ids = [line.strip() for line in repo_list_text.strip().split('\n') if line.strip()]

# 生成JSON
json_data = []
for repo_id in repo_ids:
    json_data.append({
        "repo_id": repo_id,
        "repo_type": "dataset",
        "endpoint": "modelscope",
        "description": "",
        "tags": {
            "domain": ["通用数据"],
            "task": ["教育"],
            "license": ["apache-2.0"],
            "language": [""]
        }
    })

# 写入文件
with open("input.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print(f"✅ 成功生成了 {len(json_data)} 条记录")