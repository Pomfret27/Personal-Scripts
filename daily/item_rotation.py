from datetime import date

def get_item(start_date: date, target_date: date, item_list: list, tomorrow: bool):
    interval = (target_date - start_date).days  # 计算日期间隔
    if tomorrow:                                # 判断今日明日
        interval += 1                           # 明日间隔加一
    cycle_num = len(item_list)                  # 获取轮转周期
    item_index = interval % cycle_num           # 计算物品序号
    return item_list[item_index]

if __name__ == "__main__":

    cycle_start_date = date(2026, 3, 9)         # 轮转开始日期

    # 物品列表格式：[["物品名称"], ["特征名称"], ["特征值"]]
    item_a = [["内裤"], ["颜色"], ["灰-1", "浅蓝", "黑色", "深蓝", "灰-2"]]
    item_b = [["袜子"], ["颜色"], ["白色", "浅灰", "蓝色", "深灰", "黑色"]]

    today_date = date.today()                   # 获取今日日期

    # 获取今日物品特征值
    today_a = get_item(cycle_start_date, today_date, item_a[2], False)
    today_b = get_item(cycle_start_date, today_date, item_b[2], False)

    # 获取明日物品特征值
    tomorrow_a = get_item(cycle_start_date, today_date, item_a[2], True)
    tomorrow_b = get_item(cycle_start_date, today_date, item_b[2], True)

    # 输出格式："物品名称""特征名称"："特征值"
    print(f"今日{item_a[0][0]}{item_a[1][0]}：{today_a}\n今日{item_b[0][0]}{item_b[1][0]}：{today_b}\n")
    print(f"明日{item_a[0][0]}{item_a[1][0]}：{tomorrow_a}\n明日{item_b[0][0]}{item_b[1][0]}：{tomorrow_b}\n")
