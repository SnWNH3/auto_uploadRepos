from typing import Optional, Dict
from tqdm import tqdm
import requests
import json
import pandas as pd
import re

# 搜索特定标签仓库
# 删除空仓库
# 将资源表格转换成上传格式的JSON
# 将平台资源保存为excel表格

class RepoManager:
    def __init__(self,repo_type):
        self.repo_type = repo_type
        self.backend_base_url ="http://172.19.70.30:8080" 
        self.token = self._get_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _make_request(self, method, endpoint, json_data: Optional[Dict] = None, headers: Optional[Dict] = None):
        endpoint = endpoint.strip("/")
        url = f"{self.backend_base_url}/{endpoint}"
        response = requests.Session().request(method, url, json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()

    def _get_token(self):
        login_data = {
            "username": "admin",
            "password": "admin123",
            "code": "",
            "uuid": ""}
        result = self._make_request("POST", "/login", login_data)
        token = result.get("token")
        return token
     
    # 返回特定标签仓库名称
    def search_repos(self, task=None, domain=None):
        url = f"api/git/repos/searchRepository?asset={self.repo_type}&task={task}&domain={domain}&page=1&pageSize=128"
        result = self._make_request("GET", url, None, self.headers)
        repos_json = result["data"]["data"]
        repos_list = []
        for repo in repos_json:
            repos_list.append(repo["html_url"])
        print("repos_json的长度是：", len(repos_json))
        with open("repos_json.json", "w", encoding="utf-8") as f:
            json.dump(repos_json, f, ensure_ascii=False, indent=4)
        return repos_list
        # ['observerw/ChiseLLM-Completion','henryen/origen_dataset_debug'...]

    # 删除所有空仓库
    def delete_empty_repos(self):
        url = f"api/git/repos/fetchRepoList?repoType={self.repo_type}"
        result = self._make_request("GET", url, None, self.headers)
        repo_list = result["data"]
        # [{'repo_type': 'DATASET', 'repo_id': 'shailja/Verilog_GitHub', 'clone_url': 'http://172.19.70.30:3001/shailja/Verilog_GitHub.git'},...]

        for repo in tqdm(repo_list, desc="检查仓库", unit="个"):
            repo_id = repo["repo_id"]
            # 获取仓库文件列表
            url = f"api/git/repos/{self.repo_type}s/{repo_id}/refs/main/tree/?cursor=&limit=500"
            result = self._make_request("GET", url, None, self.headers)
            file_list = result["data"]["files"]
            # 删除仓库
            if len(file_list) == 1 and file_list[0]["name"] == "README.md":
                self._make_request("DELETE", f"/api/git/repos/delete/{repo_id}", None, self.headers)
                tqdm.write(f"已删除空仓库: {repo_id}")
            else:
                tqdm.write(f"仓库{repo_id}非空")
        return file_list

    # 将资源表格转换成上传格式的JSON
    def excel_to_json(self, excel_path="资源列表.xlsx", json_path="input.json"):
        df = pd.read_excel(excel_path)
        data, seen = [], set()

        for idx, r in df.iterrows():
            # 重复校验
            repo_id = r["仓库ID"]
            if repo_id in seen:
                print(f"第{idx+2}行发现重复: repo_id={repo_id}")
                continue
            seen.add(repo_id)
            data.append({
                "repo_id": repo_id,
                "repo_type": r["资源类型"],
                "endpoint": r["来源"],
                "description": r["描述"],
                "tags": {
                    "domain": [r["领域"]],
                    "task": [i.strip() for i in re.split(r"[，,、]", str(r["任务支持"])) if i.strip()],
                    "license": [r["证书"]],
                    "language": [r["语言"]]
                }
            })
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已生成 {json_path} ，共 {len(data)} 条数据")    

    # 将平台资源保存为excel表格
    def save_excel(self, excel_path = "资源列表.xlsx"):
        url = f"api/git/repos/searchRepository?asset={self.repo_type}&page=1&pageSize=1000000"
        result = self._make_request("GET", url, None, self.headers)
        repos_json = result["data"]["data"]
        rows = []
        for repo in tqdm(repos_json, desc="导出资源"):
            
            # 处理标签
            tags = repo.get("tags", [])
            domains = [t["name"] for t in tags if t["category"] == "domain"]
            tasks = [t["name"] for t in tags if t["category"] == "task"]
            licences = [t["name"] for t in tags if t["category"] == "licence"]
            languages = [t["name"] for t in tags if t["category"] == "language"]

            row = {
                "资源类型": self.repo_type,
                "来源": "",
                "仓库ID": repo.get("html_url", ""),
                "领域": ",".join(domains),
                "任务支持": ",".join(tasks),
                "描述": repo.get("description", ""),
                "证书": ",".join(licences),
                "链接": "",
                "语言": ",".join(languages),
                "备注": "",
                "负责人": ""
            }
            rows.append(row)
        df = pd.DataFrame(rows)
        df.to_excel(excel_path, index=False)
        print(f"已生成 {excel_path} ，共 {len(rows)} 条资源")

if __name__ == "__main__":
    manager = RepoManager(repo_type="model")
    result = manager.save_excel(excel_path = "模型资源列表.xlsx")

