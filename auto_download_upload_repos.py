import os
from os.path import join
import json
import subprocess
import logging
import requests
import git
import shutil
import stat
from pathlib import Path
from typing import Optional, Dict
from huggingface_hub import snapshot_download as hf_snapshot_download
from modelscope import snapshot_download as ms_snapshot_download
from datetime import datetime, timezone

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s",datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)   # 创建模块级 logger

class RepoUploader:
    def __init__(self, backend_base_url):
        self.backend_base_url = backend_base_url
        self.script_dir = os.path.dirname(os.path.abspath(__file__)) 
        self.input_file = join(self.script_dir, "input.json")
        self.output_file = join(self.script_dir, "output.txt")
        self.default_password = "Password@321" # 老用户password@321
        self.uploadFail_repos = []
        self.uploadSuccess_repos = []
        self.token = self.get_token("SnWNH3")
        self.all_tags = self.fetch_allTags()
        # self.all_repoIDs = self.fetch_allRepoIDs()

    def log_message(self, msg: str):
        with open(self.output_file, "a", encoding="utf-8") as f:
            now = datetime.now().strftime("%m-%d %H:%M")
            timeMsg = f"[{now}] {msg}"
            f.write(f"{timeMsg}\n")
        logger.info(timeMsg)

    def fetch_allTags(self):
        all_tags = []
        headers = {"Authorization": f"Bearer {self.token}"}
        for repo_type in ["dataset","model","code","mcp"]:
            result = self._make_request("GET", "/api/git/repos/tags?scope="+repo_type, headers=headers)
            tag_list = result.get("data", []) # [{'id': 1, 'name': 'EDA',...},]
            all_tags.extend(tag_list)
        return all_tags

    def fetch_allRepoIDs(self):
        all_repoID = set()
        headers = {"Authorization": f"Bearer {self.token}"}
        for repo_type in ["model","dataset","code","mcp"]:
            fetch_api = "/api/git/repos/searchRepository?asset=" + repo_type + "&page=1&pageSize=100000"
            result = self._make_request("GET", fetch_api, headers=headers)
            repoInfo_list = result.get("data", {}).get("data", []) # [{"html_url":...}]
            for repoInfo in repoInfo_list:
                repoID = repoInfo.get("html_url")
                all_repoID.add(repoID)
        return all_repoID
           
    def get_jsonRepoList(self):
        try:
            unique_repo_list = []
            with open(self.input_file, 'r', encoding='utf-8') as f:
                repo_list = json.load(f)
            for repo in repo_list:
                repo_id = repo.get("repo_id")
                if not any(r.get("repo_id") == repo_id for r in unique_repo_list):
                    unique_repo_list.append(repo)
            return unique_repo_list
        except FileNotFoundError:
            self.log_message(f"'{self.input_file}'文件没有找到")
            return []
        except json.JSONDecodeError:
            self.log_message(f"不合法的json文件'{self.input_file}'")
            return []
        
    def _make_request(self, method, endpoint, json_data: Optional[Dict] = None, headers: Optional[Dict] = None):
        endpoint = endpoint.strip("/")
        url = f"{self.backend_base_url}/{endpoint}"
        response = requests.Session().request(method, url, json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def register_user(self, username):
        register_data = {
            "username": username,
            "password": self.default_password,
            "confirmPassword": self.default_password,
            "code": "",
            "uuid": ""}
        
        result = self._make_request("POST", "/register", register_data)
        code = result.get("code", 0)
        msg = result.get("msg", "")

        if code == 200:
            self.log_message(f"-1 用户注册成功")
        elif code == 500 and "注册账号已存在" in msg:
            self.log_message(f"-1 用户注册跳过，已存在")
        else:
            self.log_message(f"-1 用户注册失败: {msg}")

    def get_token(self, username):
        
        login_data = {
            "username": username,
            "password": self.default_password,
            "code": "",
            "uuid": ""}
        result = self._make_request("POST", "/login", login_data)
        code = result.get("code", 0)
        msg = result.get("msg", "")

        if code == 200:
            if not username == "SnWNH3":
                self.log_message(f"-2 登录成功")
        elif code == 500 and "password error" in msg:
            self.log_message(f"-2 登录失败，密码错误")
        else:
            self.log_message(f"-2 登录失败: {msg}")

        return result.get('token')
        
    def create_repo(self, owner, repo_name, repo_type, repo_license, repo_desc, token):

        repo_data = {
                "repoOwner": owner,
                "repoName": repo_name,
                "repoNickname": "",
                "repoLicense": repo_license, 
                "repoDescription": repo_desc,
                "repoType": repo_type,
                "private": False}
        headers = {"Authorization": f"Bearer {token}"}

        self.repoAlreadyExists = False
        result = self._make_request("POST", "/api/git/repos/createRepository", repo_data, headers)
        code = result.get("code", 0)
        msg = result.get("msg", "")

        if code == 200:
            self.log_message(f"-3 仓库创建成功.")
        elif code == 500 and "已存在同名仓库" in msg:
            self.log_message(f"-3 仓库创建跳过，已存在")
            self.repoAlreadyExists = True
        else:
            self.log_message(f"-3 仓库创建失败：{msg}")
        
    def add_tags(self, owner, repo_name, tags, repo_type, token):
        if self.repoAlreadyExists == True:
            self.log_message(f"-4 标签更新跳过，仓库已存在")
            return
        headers = {"Authorization": f"Bearer {token}"}
        now = datetime.now(timezone.utc)
        formatted_time = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        flat_tags = []
        # input.json中tags分为领域、任务、许可证、语言四个类别，每个类别是一个列表["Verilog","代码生成"]
        for category, tag_names in tags.items():
            for tag_name in tag_names:
                for tag in self.all_tags:
                    if tag.get("name") == tag_name and tag.get("scope") == repo_type:
                        flat_tags.append({
                            "id": tag.get("id"),  
                            "name": tag_name,
                            "category": category,
                            "group": "",
                            "built_in": True,
                            "scope": repo_type,
                            "show_name": tag_name,
                            "i18n_key": "",
                            "created_at": formatted_time,
                            "updated_at": formatted_time
                        })
        tag_data = {
            "repoType": repo_type,
            "repoOwner": owner,
            "repoName": repo_name,
            "tags": flat_tags
        }
        result = self._make_request("PUT","api/git/repos/update/tags", tag_data, headers)
        code = result.get("code", 0)
        msg = result.get("msg", 0)
        if code == 200:
            self.log_message(f"-4 标签更新成功")
        else:
            self.log_message(f"-4 标签更新失败，{msg}")

    def download_repo(self, repo_id, repo_type, local_path, endpoint):
        self.log_message(f"-5 数据下载开始")
        if endpoint.lower() == "huggingface":
            # hf_snapshot_download(repo_id=repo_id, repo_type=repo_type, local_dir=local_path) 
            hf_snapshot_download(repo_id=repo_id, repo_type=repo_type, local_dir=local_path, endpoint="https://hf-mirror.com") 

        elif endpoint.lower() == "modelscope":
            ms_snapshot_download(repo_id=repo_id, repo_type=repo_type, local_dir=local_path)
            # 删除.mv和.msc文件
            for file in os.listdir(local_path):
                if file.endswith((".mv", ".msc")):
                    os.remove(os.path.join(local_path, file))
            
        elif endpoint.lower() == "github":
            repo_url = "git@github.com:"+repo_id+".git"
            git.Repo.clone_from(repo_url, local_path)
            
        self.log_message(f"-5 数据下载完成")
    
    def init_gitFolder(self, local_path):
        git_folder_path = os.path.join(local_path, '.git')
        def readonly_handler(func, path, exc_info):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        if os.path.exists(git_folder_path):
            shutil.rmtree(git_folder_path, onexc= readonly_handler)
        
        # 把>10MB的大文件纳入LFS
        local_path = Path(local_path).resolve()
        bigFile_size = 10 * 1024 * 1024
        big_files = []

        for file in local_path.rglob("*"):
            if file.is_file() and file.stat().st_size > bigFile_size :
                big_files.append(file)
        
        # git 操作
        def _exec(cmd):
            subprocess.run(cmd, shell=True, check=True)
        os.chdir(local_path)
        _exec("git init -b main")
        _exec("git lfs install")

        for file in big_files:
            rel_path = file.relative_to(local_path)
            _exec(f'git lfs track "{rel_path.as_posix()}"')
        if big_files:
            _exec("git add .gitattributes")
        _exec("git add .")
        _exec('git commit -m "auto init with lfs"')
        self.log_message(f"-6 仓库初始化完成")

        
    def upload_repo(self, repo_id, repo_type, token):
        # 首先获取远程仓库的url
        headers = {"Authorization": f"Bearer {token}"}
        fetch_repoAPI = f"/api/git/repos/{repo_type}/{repo_id}/fetchRepoDetail"
        try:
            result = self._make_request("GET", fetch_repoAPI, headers = headers)
        except Exception as e:
            self.log_message(f"fetch_repoAPI失败: {e}")
        msg = result.get("msg","")
        repo_info = result.get("data", {})
        if msg.lower() == "ok":
            repoURL = repo_info.get("repository", {}).get("http_clone_url")
            repoURL = repoURL.replace(":8080", "") # 过滤掉返回的URL中的端口号
            print(f"远程仓库URL: {repoURL}")
        else:
            self.log_message(f"获取远程仓库URL失败: {msg}")
        
        # 然后关联本地和远程
        def _exec(cmd):
            subprocess.run(cmd, shell=True, check=True)
        _exec(f"git remote add origin {repoURL}")
        _exec("git push -f origin main")
        self.log_message(f"-7 仓库上传完成")


    def run(self):
        repo_list = self.get_jsonRepoList()
        for repo_info in repo_list:
            repo_id, repo_type, repo_license, repo_desc, tags = repo_info["repo_id"], repo_info["repo_type"], repo_info["tags"]["license"][0], repo_info["description"],  repo_info["tags"]
            owner, repo_name = repo_id.split('/', 1)
            local_path = join(self.script_dir,repo_type,owner,repo_name)
            self.log_message(f"==============开始处理[{repo_id}]===============")
            try:
                self.register_user(owner)                                                            # 1.用户注册
                token = self.get_token(owner)                                                        # 2.登录
                self.create_repo(owner, repo_name, repo_type, repo_license, repo_desc, token)        # 3.仓库创建
                self.add_tags(owner, repo_name, tags, repo_type, token)                              # 4.标签更新
                self.download_repo(repo_id, repo_type, local_path, repo_info["endpoint"])            # 5.下载
                self.init_gitFolder(local_path)                                                      # 6.仓库管理
                self.upload_repo(repo_id, repo_type, token)                                          # 7.上传
                self.log_message(f"[{repo_id}]上传成功")
                self.uploadSuccess_repos.append(repo_id)
            except Exception as e:
                self.log_message(f"{repo_id}上传出错{e}")
                self.uploadFail_repos.append(repo_id)
        self.log_message(f">>>>>>>>>>>>>>>>上传失败的仓库列表: {self.uploadFail_repos}<<<<<<<<<<<<<<<<<<<")
        self.log_message(f">>>>>>>>>>>>>>>>上传成功的仓库列表: {self.uploadSuccess_repos}<<<<<<<<<<<<<<<<<<<")

        
if __name__ == "__main__":
    backend_base_url = "http://172.19.70.30:8080"  # 后端目录
    upload = RepoUploader(backend_base_url)
    upload.run()






