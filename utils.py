import sys
import cv2
import numpy as np
import pyautogui
import time
from pathlib import Path
import os

def resource_path(relative_path):
    """ 获取打包后资源的绝对路径 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


jieping_save_filename = resource_path("picture/screenshot_pyautogui.png")  # jietu_with_save中保存截图的位置，默认关闭


# 截取屏幕左侧并保存、返回
def jietu_with_save(filename=jieping_save_filename, region=(0, 0, 600, 1040)):
    """
    在屏幕上使用 pyautogui 截图并返回截图对象
    :param filename: 截图存储的位置，开启，可以方便调试。
    :return: 返回截图的对象，否则返回 None。
    """
    try:
        # screenshot = pyautogui.screenshot()
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(filename)
        # print(f"截图已保存到 {filename}")
        return screenshot
    except Exception as e:
        print(f"使用 pyautogui 截图失败 (检查依赖或权限): {e}")


# 获取图上最匹配的点坐标
def find_template_on_screen_pyautogui(template_path, screenshot_pil, confidence=0.9):
    """
    在screenshot_pil图片上并查找模板图片template_path的位置。
    :param template_path: 模板图片的文件路径。
    :param screenshot_pil: 用pyautogui从屏幕上截取的图片，是Image对象。
    :param confidence: 匹配的置信度阈值 (0 到 1)。
    :return: 如果找到，返回匹配区域的 (left, top, width, height) 元组；否则返回 None。
    """
    try:
        # 读取模板图片 (灰度图通常足够且更快)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"错误：无法加载模板图片 '{template_path}'")
            return None
        template_h, template_w = template.shape[:2]  # 获取模板的宽度和高度

        # --- 将 Pillow Image 转换为 OpenCV 格式 (NumPy 数组) ---
        # 1. 将 Pillow Image 转为 NumPy 数组 (格式通常是 RGB)
        screen_img_rgb = np.array(screenshot_pil)
        # 2. 将 RGB 转换为 BGR (OpenCV 内部更常用的顺序，虽然我们马上转灰度)
        # screen_img_bgr = cv2.cvtColor(screen_img_rgb, cv2.COLOR_RGB2BGR) # 如果后续需要彩色处理则用这行
        # 3. 直接将 RGB 转换为灰度图进行匹配
        screen_img_gray = cv2.cvtColor(screen_img_rgb, cv2.COLOR_RGB2GRAY)

        # 使用 TM_CCOEFF_NORMED 方法进行模板匹配，这个方法的结果范围是 0 到 1，1 表示完美匹配
        result = cv2.matchTemplate(screen_img_gray, template, cv2.TM_CCOEFF_NORMED)
        # 找到最佳匹配的位置和置信度
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # print(f"模板 '{template_path}' 的最高匹配度: {max_val:.4f} 在位置 {max_loc}")

        if max_val >= confidence:
            # max_loc 是匹配区域的左上角坐标 (x, y)
            match_left, match_top = max_loc
            # 使用模板的宽度和高度确定匹配区域
            match_rect = (match_left, match_top, template_w, template_h)
            print(f"{template_path} 匹配到区域: {match_rect}，匹配度: {max_val:.4f}")
            return match_rect
        else:
            # print("未找到足够置信度的匹配。")
            return None
    except pyautogui.PyAutoGUIException as e:
        # 处理 pyautogui 可能的异常，例如权限问题 (macOS)
        print(f"PyAutoGUI 截图或操作时发生错误: {e}")
        print("请确保 PyAutoGUI 有必要的屏幕权限 (尤其是在 macOS 上)。")
        return None
    except Exception as e:
        print(f"模板匹配时发生错误: {e}")
        return None


# 获取图上大于confidence的所有点坐标
def find_all_template_on_screen_pyautogui(template_path, screenshot_pil, confidence=0.9):
    """
    在screenshot_pil图片上查找所有匹配度大于confidence的模板图片位置。
    :param template_path: 模板图片的文件路径。
    :param screenshot_pil: 用pyautogui从屏幕上截取的图片，是Image对象。
    :param confidence: 匹配的置信度阈值 (0 到 1)。
    :return: 返回匹配区域列表，每个元素是 (left, top, width, height) 元组；如果没有匹配，返回空列表 []。
    """
    try:
        # 读取模板图片 (灰度图通常足够且更快)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"错误：无法加载模板图片 '{template_path}'")
            return []

        template_h, template_w = template.shape[:2]

        # --- 将 Pillow Image 转换为 OpenCV 格式 (NumPy 数组) ---
        # 1. 将 Pillow Image 转为 NumPy 数组 (格式通常是 RGB)
        screen_img_rgb = np.array(screenshot_pil)
        # 2. 将 RGB 转换为 BGR (OpenCV 内部更常用的顺序，虽然我们马上转灰度)
        # screen_img_bgr = cv2.cvtColor(screen_img_rgb, cv2.COLOR_RGB2BGR) # 如果后续需要彩色处理则用这行
        # 3. 直接将 RGB 转换为灰度图进行匹配
        screen_img_gray = cv2.cvtColor(screen_img_rgb, cv2.COLOR_RGB2GRAY)

        # 模板匹配
        result = cv2.matchTemplate(screen_img_gray, template, cv2.TM_CCOEFF_NORMED)

        # 找到所有匹配度 >= confidence 的位置
        match_locations = np.where(result >= confidence)

        matches = []
        for (y, x) in zip(*match_locations):
            match_rect = (x, y, template_w, template_h)
            matches.append(match_rect)
            print(f"{template_path} 匹配到区域: {match_rect}，匹配度: {result[y, x]:.4f}")

        # if not matches:
        #     print(f"{template_path} 未找到匹配度高于 {confidence} 的区域。")

        return matches

    except pyautogui.PyAutoGUIException as e:
        print(f"PyAutoGUI 截图或操作时发生错误: {e}")
        print("请确保 PyAutoGUI 有必要的屏幕权限 (尤其是在 macOS 上)。")
        return []
    except Exception as e:
        print(f"模板匹配时发生错误: {e}")
        return []


refuse_authorization_button = (resource_path("picture/main_button/return_and_error/refuse_authorization.png"), (-90, 100), 0.7)  #

network_chonglian_button = (resource_path("picture/main_button/return_and_error/chonglian.png"), (110, 120), 0.9)  #
network_duan_button = (resource_path("picture/main_button/return_and_error/duanwang.png"), (90, 95), 0.9)  #
zhandou_jieshu_button = (resource_path("picture/main_button/return_and_error/lian.png"), (0, 95), 0.9)  #

error_huitui_button = (resource_path("picture/main_button/return_and_error/huitui.png"), (-240, 0), 0.95) # 取中心

zhuxian_fanhui_button = (resource_path("picture/main_button/return_and_error/return_button"), (0, 0), 0.95)  # 判断返回， 取中心

cishu = 0  # 统计次数


def utils(screenshot_pil):
    # --- 拒绝授权 --
    found_loc = find_template_on_screen_pyautogui(refuse_authorization_button[0], screenshot_pil, confidence=refuse_authorization_button[2])
    if found_loc:
        try:
            pyautogui.click(found_loc[0] + found_loc[2]//2 + refuse_authorization_button[1][0],
                            found_loc[1] + found_loc[3]//2 + refuse_authorization_button[1][1],
                            clicks=1, interval=0, button='left', duration=0)
            time.sleep(1)
        except Exception as e:
            print(f"点击拒绝授权时发生错误: {e}")

    # --- 返回按钮 --
    try:
        p = Path(zhuxian_fanhui_button[0])
        if not p.is_dir():
            print(f"错误：'{zhuxian_fanhui_button}' 不是一个有效的文件夹。")
        all_entries = [entry.name for entry in p.iterdir()]  # .name 获取路径的最后一部分（文件名或目录名）
        for f in all_entries:
            found_loc = find_template_on_screen_pyautogui(zhuxian_fanhui_button[0] + "/" + f,
                                                          screenshot_pil,
                                                          confidence=zhuxian_fanhui_button[2])
            if found_loc:
                time.sleep(10)
                pyautogui.click(found_loc[0] + found_loc[2]//2 + zhuxian_fanhui_button[1][0],
                                found_loc[1] + found_loc[3]//2 + zhuxian_fanhui_button[1][1],
                                clicks=1, interval=0, button='left', duration=0)
                global cishu
                cishu += 1
                print("cishu =", cishu)
                time.sleep(5)
                break
    except Exception as e:
        print(f"返回判断发生错误: {e}")

    # --- 回退按钮 --
    found_loc = find_template_on_screen_pyautogui(error_huitui_button[0],
                                                  screenshot_pil,
                                                  confidence=error_huitui_button[2])
    if found_loc:
        try:
            pyautogui.click(found_loc[0] + found_loc[2]//2 + error_huitui_button[1][0],
                            found_loc[1] + found_loc[3]//2 + error_huitui_button[1][1],
                            clicks=1, interval=0, button='left', duration=0)
            time.sleep(1)
        except Exception as e:
            print(f"点击回退按钮时发生错误: {e}")

    # --- 断网重连 --
    found_loc = find_template_on_screen_pyautogui(network_duan_button[0],
                                                  screenshot_pil,
                                                  confidence=network_duan_button[2])
    if found_loc:
        try:
            pyautogui.click(found_loc[0] + found_loc[2]//2 + network_duan_button[1][0],
                            found_loc[1] + found_loc[3]//2 + network_duan_button[1][1],
                            clicks=1, interval=0, button='left', duration=0)
            time.sleep(1)
        except Exception as e:
            print(f"点击断网重连1时发生错误: {e}")
    found_loc = find_template_on_screen_pyautogui(network_chonglian_button[0],
                                                  screenshot_pil,
                                                  confidence=network_chonglian_button[2])
    if found_loc:
        try:
            pyautogui.click(found_loc[0] + found_loc[2]//2 + network_chonglian_button[1][0],
                            found_loc[1] + found_loc[3]//2 + network_chonglian_button[1][1],
                            clicks=1, interval=0, button='left', duration=0)
            time.sleep(1)
        except Exception as e:
            print(f"点击断网重连2时发生错误: {e}")
    found_loc = find_template_on_screen_pyautogui(zhandou_jieshu_button[0],
                                                  screenshot_pil,
                                                  confidence=zhandou_jieshu_button[2])
    if found_loc:
        try:
            pyautogui.click(found_loc[0] + found_loc[2]//2 + zhandou_jieshu_button[1][0],
                            found_loc[1] + found_loc[3]//2 + zhandou_jieshu_button[1][1],
                            clicks=1, interval=0, button='left', duration=0)
            time.sleep(1)
        except Exception as e:
            print(f"点击断网重连3时发生错误: {e}")


select_jineng_button = (resource_path("picture/select_jineng/jineng"), (0, 0), 0.9)  # 存放技能相关的点击
jihuo_jineng_button = (resource_path("picture/select_jineng/yijihuo.png"), (0, 0), 0.9)  # 已激活技能的


def choose_ji_neng(screenshot_pil):
    # --- 已激活技能 --
    found_loc = find_template_on_screen_pyautogui(jihuo_jineng_button[0],
                                                  screenshot_pil,
                                                  confidence=jihuo_jineng_button[2])
    if found_loc:
        try:
            pyautogui.click(found_loc[0] + found_loc[2]//2 + jihuo_jineng_button[1][0],
                            found_loc[1] + found_loc[3]//2 + jihuo_jineng_button[1][1],
                            clicks=2, interval=0.05, button='left', duration=0)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"点击已激活技能时发生错误: {e}")
    # --- 技能选择 --
    try:
        p = Path(select_jineng_button[0])
        if not p.is_dir():
            print(f"错误：'{select_jineng_button}' 不是一个有效的文件夹。")
        all_entries = [entry.name for entry in p.iterdir()]  # .name 获取路径的最后一部分（文件名或目录名）
        for f in all_entries:
            found_loc = find_template_on_screen_pyautogui(select_jineng_button[0] + "/" + f,
                                                          screenshot_pil,
                                                          confidence=select_jineng_button[2])
            if found_loc:
                pyautogui.click(found_loc[0] + found_loc[2]//2 + select_jineng_button[1][0],
                                found_loc[1] + found_loc[3]//2 + select_jineng_button[1][1],
                                clicks=3, interval=0.1, button='left', duration=0)
                time.sleep(5)
                return True
    except Exception as e:
        print(f"选择技能发生错误: {e}")
    return False


tili_buzu_state = (resource_path("picture/state_picture/lack_energy"), None, 0.9)  # 判断 体力不足 的文件夹的图片


def is_end_state(screenshot_pil):
    try:
        # 通过 tili_buzu_state 判断是否已经没有体力了
        p = Path(tili_buzu_state[0])
        if not p.is_dir():
            print(f"错误：'{tili_buzu_state}' 不是一个有效的文件夹。")
        all_entries = [entry.name for entry in p.iterdir()]  # .name 获取路径的最后一部分（文件名或目录名）
        for f in all_entries:
            found_loc = find_template_on_screen_pyautogui(tili_buzu_state[0] + "/" + f,
                                                                screenshot_pil,
                                                                confidence=tili_buzu_state[2])
            if found_loc:
                return True
    except Exception as e:
        print(f"体力不足判断发生错误: {e}")
    return False

