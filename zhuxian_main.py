from datetime import datetime

import pyautogui
import time
from pathlib import Path
import utils
from utils import resource_path

# 这个脚本负责循环打精英主线关卡。
# 并且启动时，请先将页面切换到 任意关卡的精英模式页面
# picture 和 zhuxian_picture 中的图片 是 窗口尺寸为542*1008下截的， 可以根据需求进行设置

# （路径、点击位置偏移中心点(x,y)、匹配置信度）
zhuxian_pause_button = (resource_path("zhuxian_picture/main_button/pause_button.png"), (0, 0), 0.7)  # 取中心
zhuxian_exit_button = (resource_path("zhuxian_picture/main_button/exit_button.png"), (0, 0), 0.9)  # 取中心
zhuxian_begin_button = (resource_path("zhuxian_picture/main_button/zhuxiang_begin.png"), (0, 0), 0.9)  # 取中心
zhuxian_joingame_state = (resource_path("zhuxian_picture/state_picture/join_game"), None, 0.8)  # 判断 已经成功开局 的文件夹的图片


zhuxian_STOP = False  # 控制是否退出循环


def main(limit_hours, region, limit_cishu, maximum_time_one_round):
    utils.cishu = 0
    begin_timestamp = time.time()
    state = 0
    stamp_time1 = 0
    while not zhuxian_STOP:
        now_timestamp = time.time()
        if now_timestamp-begin_timestamp > 3600*limit_hours or utils.cishu>=limit_cishu:
            break
        elif ((now_timestamp - begin_timestamp) // 1) % 10 == 0:
            print(datetime.fromtimestamp(now_timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                  f"状态：{state}", f"完成次数：{utils.cishu}")

        screenshot_pil = utils.jietu_with_save(region=region)  # 截图

        utils.utils(screenshot_pil)  # 通用处理

        if state < 1:
            try:
                # 通过 zhuxian_joingame_state 判断是否已经在局内了
                p = Path(zhuxian_joingame_state[0])
                if not p.is_dir():
                    print(f"错误：'{zhuxian_joingame_state}' 不是一个有效的文件夹。")
                all_entries = [entry.name for entry in p.iterdir()]  # .name 获取路径的最后一部分（文件名或目录名）
                for f in all_entries:
                    found_loc = utils.find_template_on_screen_pyautogui(zhuxian_joingame_state[0] + "/" + f,
                                                                        screenshot_pil,
                                                                        confidence = zhuxian_joingame_state[2])
                    if found_loc:
                        state = 1
                        stamp_time1 = time.time()
                        break
            except Exception as e:
                print(f"主线是否开局进入游戏判断发生错误: {e}")
        else:
            # -- 选择技能 --
            if utils.choose_ji_neng(screenshot_pil):
                continue

        if state == 0:
            # --- 点击开始 --
            found_loc = utils.find_template_on_screen_pyautogui(zhuxian_begin_button[0],
                                                                screenshot_pil,
                                                                confidence=zhuxian_begin_button[2])
            if found_loc:
                try:
                    pyautogui.click(found_loc[0] + found_loc[2]//2 + zhuxian_begin_button[1][0],
                                    found_loc[1] + found_loc[3]//2 + zhuxian_begin_button[1][1],
                                    clicks=1, interval=0, button='left', duration=0)
                    state = 1
                    stamp_time1 = time.time()
                except Exception as e:
                    print(f"点击主线开始时发生错误: {e}")
            # --- 体力不足退出 --
            if utils.is_end_state(utils.jietu_with_save()):
                break
        elif state == 1:
            # --- 自动结束，点击返回 --
            # 前面的 utils.utils(screenshot_pil) 会点击返回
            found_loc = utils.find_template_on_screen_pyautogui(zhuxian_begin_button[0],
                                                                screenshot_pil,
                                                                confidence=zhuxian_begin_button[2])
            if found_loc:
                state = 0
                continue
            # --- 超时暂停，点击暂停 --
            if time.time()-stamp_time1 > maximum_time_one_round:
                found_loc = utils.find_template_on_screen_pyautogui(zhuxian_pause_button[0],
                                                                    screenshot_pil,
                                                                    confidence=zhuxian_pause_button[2])
                if found_loc:
                    try:
                        pyautogui.click(found_loc[0] + found_loc[2] // 2 + zhuxian_pause_button[1][0],
                                        found_loc[1] + found_loc[3] // 2 + zhuxian_pause_button[1][1],
                                        clicks=1, interval=0, button='left', duration=0)
                        time.sleep(2)
                        screenshot_pil = utils.jietu_with_save(region=region)  # 截图
                        found_loc_all = utils.find_all_template_on_screen_pyautogui(zhuxian_exit_button[0],
                                                                                    screenshot_pil,
                                                                                    confidence=zhuxian_exit_button[2])
                        if found_loc_all:
                            state = 2
                    except Exception as e:
                        print(f"点击暂停时发生错误: {e}")
        elif state == 2:
            # --- 暂停时，点击退出 --
            found_loc_all = utils.find_all_template_on_screen_pyautogui(zhuxian_exit_button[0],
                                                                        screenshot_pil,
                                                                        confidence=zhuxian_exit_button[2])
            if found_loc_all:
                try:
                    for found_loc in found_loc_all:
                        pyautogui.click(found_loc[0] + found_loc[2]//2 + zhuxian_exit_button[1][0],
                                        found_loc[1] + found_loc[3]//2 + zhuxian_exit_button[1][1],
                                        clicks=2, interval=0, button='left', duration=0)
                        break
                except Exception as e:
                    print(f"点击抢票时发生错误: {e}")
                state = 0
            try:
                assert state == 0
            except Exception as e:
                print(f"超时暂停退出不起作用，更换一下退出按钮的图片: {e}")

        time.sleep(3)


if __name__ == "__main__":
    limit_hours = 19  # 运行多少个小时候后终止
    region = (0, 0, 600, 1040)  # 支持定义，识别程序页面的位置尺寸，（左上角x,左上角y,宽度,高度）
    limit_cishu = 1000000000  # 限制次数，完后后退出
    maximum_time_one_round = 60 * 10  # 一局最长能接受的时间
    main(limit_hours=limit_hours, region=region, limit_cishu=limit_cishu, maximum_time_one_round=maximum_time_one_round)

