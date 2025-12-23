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
       
    def get_jsonRepoList(self):
        input_file = join(self.script_dir, "hu_input.json")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"'{input_file}'文件没有找到")
            return []
        except json.JSONDecodeError:
            logger.error(f"不合法的json文件'{input_file}'")
            return []
                      
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
       
    def run(self):
        # 0.获取仓库列表
        repo_list = self.get_jsonRepoList()
        for repo_info in repo_list:
            repo_id, repo_type, repo_license, repo_desc, tags = repo_info["repo_id"], repo_info["repo_type"], repo_info["tags"]["license"][0], repo_info["description"],  repo_info["tags"]
            owner, repo_name = repo_id.split('/', 1)
            local_path = join(script_dir,repo_type,owner,repo_name)
            logger.info(f"====开始处理[{repo_id}]====")
        
        # 5.下载
            download_success = self.download_repo(repo_id, repo_type, local_path, repo_info["endpoint"])
            if not download_success:
                self.record_fail(repo_id, "下载资源失败")
                continue
        
if __name__ == "__main__":
    backend_base_url = "http://172.19.70.30:8080"  # 后端目录
    script_dir = os.path.dirname(os.path.abspath(__file__)) 
    upload = RepoUploader(backend_base_url, script_dir)
    upload.run()






