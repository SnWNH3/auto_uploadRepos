# auto_download_upload_repos
主文件 ，输入是input.json，输出是output.txt，执行如下功能
-1 用户注册
-2 登录
-3 仓库创建
-4 标签更新
-5 下载
-6 仓库管理
-7 上传


# input.json
需要上传的仓库的原信息，已加入.gitignore中
```
[
  {
    "repo_id": "liyixuan2026/cobot_magic_code",
    "repo_type": "dataset",
    "endpoint": "modelscope",
    "description": "",
    "tags": {
      "domain": [
        "航空软件"
      ],
      "task": [
        "代码"
      ],
      "license": [
        "apache-2.0"
      ],
      "language": [
        ""
      ]
    }
  }
]
```



# output.txt
本次上传的结果，已加入.gitignore中

```
[02-06 09:51] ==============开始处理[libfive/libfive]===============  
[02-06 09:51] -1 用户注册成功  
[02-06 09:51] -2 登录成功  
[02-06 09:51] -3 仓库创建成功  
[02-06 09:51] -4 标签更新成功  
[02-06 09:51] -5 数据下载开始  
[02-06 09:51] -5 数据下载完成  
[02-06 09:51] -6 仓库初始化完成  
[02-06 09:51] -7 仓库上传完成  
[02-06 09:51] [libfive/libfive]上传成功  
[02-06 09:51] >>>>>>>>>>>>>>>>本次运行结果<<<<<<<<<<<<<<<<<<<  
[02-06 09:51] 上传失败的仓库列表: []  
[02-06 09:51] 上传成功的仓库列表: ['libfive/libfive']  
```

# create_inputjson.py
测试用脚本，用于快速生成input.json


# uploadFailRepos_reUpload.py
从上传失败的仓库列表，重新生成待上传的json文件
输入是同路径下的fail.txt，需要**手动创建**，复制粘贴output.txt中的失败列表
输出是failed_upload_repos.json，再次上传时，需要将其**手动替换**input.json


# modelscope_search_crawler.py
魔搭的爬虫脚本，在搜索框键入关键字，获取的仓库信息列表
保存到 modelscope_repoData.json 中

# modelscopeData_to_inputJson.py
将魔搭返回的仓库信息，转换成上传脚本所需的格式
同时筛选掉大小大于100GB的仓库

# github_search_crawler.py
github的爬虫脚本，在搜索框键入关键字，获取的仓库信息列表
保存到 github_repoData.json 中

# githubData_to_inputJson.py
将魔搭返回的仓库信息，转换成上传脚本所需的格式
同时筛选掉大小大于100GB的仓库