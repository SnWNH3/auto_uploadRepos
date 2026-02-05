import requests
import json
import time

base_url = "https://www.modelscope.cn/api/v1/dolphin/datasets"

# 初始参数
params = {
    "PageSize": 30,
    "PageNumber": 1,
    "Target": "",
    "Query": "code"
}

# 先获取第一页，确定总页数
response = requests.get(base_url, params=params, timeout=10)
response.raise_for_status()

first_page = response.json()
total_count = first_page.get("TotalCount", 0)

# 计算总页数（向上取整）
page_size = params["PageSize"]
total_pages = (total_count + page_size - 1) // page_size

print(f"总数据量: {total_count}, 总页数: {total_pages}")

# 收集所有数据
all_data = []
all_data.extend(first_page.get("Data", []))

# 获取剩余页
for page in range(2, total_pages + 1):
    params["PageNumber"] = page
    
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    
    page_data = response.json()
    all_data.extend(page_data.get("Data", []))
    
    print(f"已获取第 {page}/{total_pages} 页，累计 {len(all_data)} 条数据")
    
    # 避免请求过快，添加简单延迟
    time.sleep(0.1)
    
# 保存到文件
with open("modelscope_all_data.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"\n数据获取完成！共 {len(all_data)} 条记录")
print(f"已保存到 modelscope_all_data.json")

