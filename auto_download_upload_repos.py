import os
os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"

from os.path import join
import json
import subprocess
import logging
import requests
import git
import shutil
from pathlib import Path
from typing import Optional, Dict
from huggingface_hub import snapshot_download as hf_snapshot_download
from modelscope import snapshot_download as ms_snapshot_download
from datetime import datetime, timezone

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s",datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)   # 创建模块级 logger

class RepoUploader:
    def __init__(self, backend_base_url, script_dir):
        self.backend_base_url = backend_base_url
        self.script_dir = script_dir
        
        self.input_file = join(script_dir, "input.json")
        self.upload_result = {"success": [], "failed": []}
        self.default_password = "Password@321" # 老用户password@321 新用户Password@321
        self.token = self.get_token("SnWNH3")
        self.all_tags = self.fetch_allTags()
        self.all_repoIDs = self.fetch_allRepoIDs()

    def record_fail(self, repo_id, msg):            # 记录上传失败原因
        self.upload_result["failed"].append({"repo_id": repo_id, "msg": msg})

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
            with open(self.input_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"'{self.input_file}'文件没有找到")
            return []
        except json.JSONDecodeError:
            logger.error(f"不合法的json文件'{self.input_file}'")
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
        
        try:
            result = self._make_request("POST", "/register", register_data)
        except Exception as e:
            logger.error(f"'{username}' 注册请求发送失败: {e}")
            return False
        
        code = result.get("code", 0)
        msg = result.get("msg", "")

        if code == 200:
            logger.info(f"用户'{username}'创建成功")
            return True
        elif code == 500 and "注册账号已存在" in msg:
            logger.info(f"用户'{username}'已存在,跳过创建")
            return True
        else:
            logger.error(f"用户 '{username}' 创建失败: {msg}")
            return False

    def get_token(self, username):
        login_data = {
            "username": username,
            "password": self.default_password,
            "code": "",
            "uuid": ""}
        try:
            result = self._make_request("POST", "/login", login_data)
        except Exception as e:
            logger.error(f"用户 '{username}' 登录请求失败: {e}")
            return False
        
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
        
        try:
            result = self._make_request("POST", "/api/git/repos/createRepository", repo_data, headers)
        except Exception as e:
            logger.error(f"创建仓库请求失败'{owner}/{repo_name}': {e}")
            return False
        
        code = result.get("code", 0)
        msg = result.get("msg", "")

        if code == 200:
            logger.info(f"仓库'{owner}/{repo_name}'创建成功.")
            return True
        elif code == 500 and "已存在同名仓库" in msg:
            logger.info(f"仓库'{owner}/{repo_name}'已存在，跳过创建")
            return True
        else:
            logger.error(f"仓库'{owner}/{repo_name}'创建失败：{msg}")
            return False
        
    def add_tags(self, owner, repo_name, tags, repo_type, token):
        headers = {"Authorization": f"Bearer {token}"}
        now = datetime.now(timezone.utc)
        formatted_time = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        flat_tags = []
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
        try:
            result = self._make_request("PUT","api/git/repos/update/tags", tag_data, headers)
        except Exception as e:
            logger.error(f"标签更新失败: {e}")
            return False
        code = result.get("code", 0)
        msg = result.get("msg", 0)
        if code == 200:
            logger.info(f"tags添加成功")
            return True
        else:
            logger.info(f"添加tags失败 '{owner}/{repo_name}'. Error:{msg}")
            return False

    def download_repo(self, repo_id, repo_type, local_path, endpoint):
        logger.info(f"数据下载中")
        if endpoint.lower() == "huggingface":
            try:
                hf_snapshot_download(repo_id=repo_id, repo_type=repo_type, local_dir=local_path)
                return True
            except Exception as e:
                logger.error(f"huggingface_数据下载出错: {e}")
                return False
            
        elif endpoint.lower() == "modelscope":
            try:
                ms_snapshot_download(repo_id=repo_id, repo_type=repo_type, local_dir=local_path)
                return True
            except Exception as e:
                logger.error(f"modelscope_数据下载出错: {e}")
                return False
            
        elif endpoint.lower() == "github":
            try:
                repo_url = "https://github.com/"+repo_id+".git"
                git.Repo.clone_from(repo_url, local_path)
                return True
            except Exception as e:
                logger.error(f"github_数据下载出错: {e}")
                return False
            
        elif endpoint.lower() == "localdownload":
            if os.path.exists(local_path):
                logger.info(f"本地仓库存在: {local_path}")
                return True
            else:
                logger.error(f"本地仓库不存在: {local_path}")
                return False

        else:
            logger.eror(f"endpoint未被定义")
            return False

    def init_gitFolder(self, local_path):
        logger.info(f"仓库初始化")
        git_folder_path = os.path.join(local_path, '.git')
        if os.path.exists(git_folder_path):
            shutil.rmtree(git_folder_path)
        
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
        return True
        
    def upload_repo(self, repo_id, repo_type, token):
        logger.info(f"仓库上传中")
        # 首先获取远程仓库的url
        headers = {"Authorization": f"Bearer {token}"}
        fetch_repoAPI = f"/api/git/repos/{repo_type}/{repo_id}/fetchRepoDetail"
        try:
            result = self._make_request("GET", fetch_repoAPI, headers = headers)
        except Exception as e:
            logger.error(f"fetch_repoAPI失败: {e}")
            return False
        msg = result.get("msg","")
        repo_info = result.get("data", {})
        if msg.lower() == "ok":
            repoURL = repo_info.get("repository", {}).get("http_clone_url")
            repoURL = repoURL.replace(":8080", "") # 过滤掉返回的URL中的端口号
            print(f"远程仓库URL: {repoURL}")
        else:
            logger.error(f"获取远程仓库URL失败: {msg}")
            return False
        
        # 然后关联本地和远程
        def _exec(cmd):
            subprocess.run(cmd, shell=True, check=True)
        _exec(f"git remote add origin {repoURL}")
        _exec("git push -f origin main")
        return True

    def run(self):
        # 0.获取仓库列表
        repo_list = self.get_jsonRepoList()
        for repo_info in repo_list:
            repo_id, repo_type, repo_license, repo_desc, tags = repo_info["repo_id"], repo_info["repo_type"], repo_info["tags"]["license"][0], repo_info["description"],  repo_info["tags"]

            owner, repo_name = repo_id.split('/', 1)
            local_path = join(script_dir,repo_type,owner,repo_name)
            logger.info(f"====开始处理[{repo_id}]====")
        # 1.用户注册
            if not self.register_user(owner):
                self.record_fail(repo_id, "用户注册账号失败")
                continue
        # 2.登录
            token = self.get_token(owner)
            if not token:
                self.record_fail(repo_id, "用户登录失败")
                continue
        # 3.创建仓库
            if not self.create_repo(owner, repo_name, repo_type, repo_license, repo_desc, token):
                self.record_fail(repo_id, "创建仓库失败")
                continue
        # 4.更新标签
            if not self.add_tags(owner, repo_name, tags, repo_type, token):
                self.record_fail(repo_id, "标签更新失败")
                continue
        # 5.下载
            download_success = self.download_repo(repo_id, repo_type, local_path, repo_info["endpoint"])
            if not download_success:
                self.record_fail(repo_id, "下载资源失败")
                continue
        # 6.仓库管理
            if not self.init_gitFolder(local_path):
                self.record_fail(repo_id, "初始化git仓库失败")
                continue
        # 8.上传
            if not self.upload_repo(repo_id, repo_type, token):
                self.record_fail(repo_id, "仓库上传失败")
                continue
        # 9.记录成功
            self.upload_result["success"].append({"repo_id": repo_id, "msg": "上传成功"})
        # 写入上传结果
        output_file = join(self.script_dir, "output.json")   
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.upload_result, f, ensure_ascii=False, indent=4)
        
if __name__ == "__main__":
    backend_base_url = "http://172.19.70.30:8080"  # 后端目录
    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    upload = RepoUploader(backend_base_url, script_dir)
    upload.run()






