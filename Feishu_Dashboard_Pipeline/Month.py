from datetime import datetime, timedelta

# 当前日期减15天
target_date = datetime.now() - timedelta(days=15)

# 格式化为 202605 这种 6 位字符串
result = target_date.strftime("%Y%m")

print(result)  # 输出：202605