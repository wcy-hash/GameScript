import time
from datetime import datetime
from pathlib import Path
import pyautogui
import utils
from utils import resource_path

# 这个脚本负责抢环球救援。
# 并且启动时，请先将页面切换到 任意关卡的精英模式页面 或者 任意级别环球救援页面
# picture中的图片 是 窗口尺寸为542*1008下截的， 可以根据需求进行设置

# （路径、点击位置偏移中心点(x,y)、匹配置信度）
qianghuan_chat_button = (resource_path("picture/main_button/chat.png"), (0, 0), 0.7)  # 取中心
qianghuan_zhaomu_button = (resource_path("picture/main_button/zhaomu.png"), (0, 0), 0.8)  # 取中心
qianghuan_huan_button = (resource_path("picture/main_button/chat_huan.png"), (0, 0), 0.8)  # 取中心

qianghuan_noperson_state = (resource_path("picture/state_picture/no_person"), None, 0.9)  # 判断 没人、也就是没有入队 的文件夹的图片
qianghuan_youperson_state = (resource_path("picture/state_picture/join_team"), None, 0.8)  # 判断有人了或开局了的文件夹的图片

qianghuan_STOP = False  # 控制是否退出循环


def main(limit_hours, region, limit_cishu):
    utils.cishu = 0
    begin_timestamp = time.time()
    state = 3
    qiang_s = 1
    while not qianghuan_STOP:
        now_timestamp = time.time()
        if now_timestamp-begin_timestamp > 3600*limit_hours or utils.cishu>=limit_cishu:
            break
        elif ((now_timestamp - begin_timestamp) // 1) % 10 == 0:
            print(datetime.fromtimestamp(now_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                  f"状态：{state}", f"完成次数：{utils.cishu}")

        screenshot_pil = utils.jietu_with_save(region=region)  # 截图

        utils.utils(screenshot_pil)  # 通用处理

        if state < 3:
            try:
                # 通过 qianghuan_youperson_state 判断是否已经入队，或者已经在局内了
                p = Path(qianghuan_youperson_state[0])
                if not p.is_dir():
                    print(f"错误：'{qianghuan_youperson_state}' 不是一个有效的文件夹。")
                all_entries = [entry.name for entry in p.iterdir()]  # .name 获取路径的最后一部分（文件名或目录名）
                for f in all_entries:
                    found_loc = utils.find_template_on_screen_pyautogui(qianghuan_youperson_state[0] + "/" + f,
                                                                        screenshot_pil,
                                                                        confidence = qianghuan_youperson_state[2])
                    if found_loc:
                        state = 3
                        break
            except Exception as e:
                print(f"入队判断发生错误: {e}")
        else:
            # -- 选择技能 --
            if utils.choose_ji_neng(screenshot_pil):
                continue

        # -- 没有入队 --
        try:
            p = Path(qianghuan_noperson_state[0])
            if not p.is_dir():
                print(f"错误：'{qianghuan_noperson_state}' 不是一个有效的文件夹。")
            all_entries = [entry.name for entry in p.iterdir()]  # .name 获取路径的最后一部分（文件名或目录名）
            for f in all_entries:
                found_loc = utils.find_template_on_screen_pyautogui(qianghuan_noperson_state[0] + "/" + f,
                                                                    screenshot_pil,
                                                                    confidence=qianghuan_noperson_state[2])
                if found_loc:
                    state = 0
                    break
        except Exception as e:
            print(f"没有入队判断发生错误: {e}")

        if state == 0:
            # --- 点击聊天 --
            found_loc = utils.find_template_on_screen_pyautogui(qianghuan_chat_button[0],
                                                                screenshot_pil,
                                                                confidence=qianghuan_chat_button[2])
            if found_loc:
                try:
                    pyautogui.click(found_loc[0] + found_loc[2]//2 + qianghuan_chat_button[1][0],
                                    found_loc[1] + found_loc[3]//2 + qianghuan_chat_button[1][1],
                                    clicks=1, interval=0, button='left', duration=0)
                    state = 1
                    time.sleep(2)
                except Exception as e:
                    print(f"点击聊天时发生错误: {e}")
        elif state == 1:
            # --- 点击招募 --
            found_loc = utils.find_template_on_screen_pyautogui(qianghuan_zhaomu_button[0],
                                                                screenshot_pil,
                                                                confidence=qianghuan_zhaomu_button[2])
            if found_loc:
                try:
                    pyautogui.click(found_loc[0] + found_loc[2]//2 + qianghuan_zhaomu_button[1][0],
                                    found_loc[1] + found_loc[3]//2 + qianghuan_zhaomu_button[1][1],
                                    clicks=1, interval=0, button='left', duration=0)
                    state = 2
                    time.sleep(2)
                except Exception as e:
                    print(f"点击招募时发生错误: {e}")
        elif state == 2:
            # --- 点击抢票 --
            found_loc_all = utils.find_all_template_on_screen_pyautogui(qianghuan_huan_button[0],
                                                                        screenshot_pil,
                                                                        confidence=qianghuan_huan_button[2])
            if found_loc_all:
                try:
                    for found_loc in found_loc_all:
                        pyautogui.click(found_loc[0] + found_loc[2]//2 + qianghuan_huan_button[1][0],
                                        found_loc[1] + found_loc[3]//2 + qianghuan_huan_button[1][1],
                                        clicks=2, interval=0, button='left', duration=0)
                except Exception as e:
                    print(f"点击抢票时发生错误: {e}")
                qiang_s += 1
            # --- 体力不足退出 --
            if utils.is_end_state(utils.jietu_with_save()):
                break
        elif state == 3:
            qiang_s = 1

        if qiang_s%100 == 0:
            print("抢了100次，休息一会儿，可以趁现在不抢占鼠标，关闭程序！")
            qiang_s = 1
            time.sleep(10)

        time.sleep(0.05)


if __name__ == "__main__":
    limit_hours = 19  # 运行多少个小时候后终止
    region = (0, 0, 600, 1040)  # 支持定义，识别程序页面的位置尺寸，（左上角x,左上角y,宽度,高度）
    limit_cishu = 1000000000  # 限制次数，完后后退出
    main(limit_hours=limit_hours, region=region, limit_cishu=limit_cishu)
