import json

with open('github_repoData.json','r',encoding='utf-8') as f:
    data = json.load(f)

res = []
for repo in data['items']:
    res.append({
        "repo_id": repo.get('full_name',''),
        "repo_type": "dataset",
        "endpoint": "github",
        "description": str(repo.get('description','')).strip(),
        "tags": {
            "domain": ["工业数据分析"],
            "task": ["表面缺陷检测","plh"],
            "license": ["apache-2.0"],
            "language": [""]
        }
    })

with open('input.json','w',encoding='utf-8') as f:
    json.dump(res,f,ensure_ascii=False,indent=2)

print(f"✅ 成功生成了 {len(res)} 条input.json记录")