"""
:Date        : 2025-07-21 22:11:13
:LastEditTime: 2025-08-28 08:11:20
:Description : 
"""
import os
import xml.etree.ElementTree as ET
import cv2
import numpy as np
from skimage.morphology import skeletonize


def get_contour_size(filepath: str):
    """
    获取图像的实际测绘大小
    """
    # 解析 XML 文件
    if os.path.exists(f"{filepath}_metadata.xml"):
        metadata_path = f"{filepath}_metadata.xml"
    else:
        filename, extension = os.path.splitext(filepath)
        prefix = filename[:filename.rindex("_")]
        metadata_path = f"{prefix}{extension}_metadata.xml"
    tree = ET.parse(metadata_path)
    root = tree.getroot()  # 获取根节点
    # 遍历节点
    for contour in root.findall('.//ContourSize'):
        contour_size_list = contour.text.split(",")
        for i, contour_size in enumerate(contour_size_list):
            contour_size_list[i] = float(contour_size)
        return contour_size_list
    return None

def find_branch_points(skeleton: cv2.typing.MatLike):
    """检测骨架中的分叉点"""
    skeleton_int = skeleton.astype(np.float32)  # 转为float32

    # 定义核（float32类型）
    kernel = np.array([[1, 1, 1],
                      [1, 10, 1],
                      [1, 1, 1]], dtype=np.float32)

    # 卷积计算（输出为float32）
    neighbor_count = cv2.filter2D(skeleton_int, -1, kernel)

    # 分叉点条件：中心为255且邻居数≥3（即卷积值≥10*255 + 3*255 = 3315）
    branch_points = (skeleton == 255) & (neighbor_count >= 13 * 255)
    return np.argwhere(branch_points)

def extract_main_branches(skeleton: cv2.typing.MatLike, branch_points):
    """从骨架中提取主干分支"""
    # 标记分叉点（临时设为0，避免干扰轮廓提取）
    skeleton_cleaned = skeleton.copy()
    for y, x in branch_points:
        skeleton_cleaned[y, x] = 0

    # 提取所有分支轮廓
    contours, _ = cv2.findContours(skeleton_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    main_contour = max(contours, key=lambda x: cv2.arcLength(x, False))
    return main_contour, extract_single_path(main_contour)

def extract_single_path(contour: cv2.typing.MatLike) -> cv2.typing.MatLike:
    """
    处理来回路径的去重
    """
    points = contour.reshape(-1, 2)
    # 看起始点在哪头，如果第一个元素等于倒数第二个元素，那需要反转，正常情况应该是第二个元素等于倒数第一个元素
    if points[0].tolist() == points[-2].tolist():
        points = points[::-1]
    _, indices = np.unique(points, axis=0, return_index=True)
    return points[np.sort(indices)].reshape(-1, 1, 2)


def clean_main_contour(contour: cv2.typing.MatLike, skeleton_shape):
    """
    清理纤毛的分叉
    """
    skeleton = np.zeros(skeleton_shape, dtype=np.uint8)
    cv2.drawContours(skeleton, [contour], -1, 255, 1)
    branch_point = find_branch_points(skeleton)
    return extract_main_branches(skeleton, branch_point)


def arc_length(
        img: cv2.typing.MatLike,
        box: list,
        contour_size: list = None,
        decay_imit: int = None
    ):
    """
    处理图像并计算线条长度
    
    参数:
        image_path: 图像路径
        top_left: 矩形区域左上角坐标 (x1, y1)
        bottom_right: 矩形区域右下角坐标 (x2, y2)
        contour_size: 轮廓尺寸 [宽度, 高度]
        visualize: 是否显示可视化结果
    
    返回:
        处理后的图像和线条长度
    """
    if not contour_size:
        return None
    _, contour_size_height = contour_size
    height, _, _ = img.shape
    # 截取矩形区域
    x1, y1, x2, y2 = box
    cropped = img[y1:y2, x1:x2]

    # 提取红色通道 (OpenCV使用BGR顺序)
    red_channel = cropped[:, :, 2].copy()

    # 方法：取红色通道前n%的亮度作为阈值（可调整percent）
    percent = decay_imit or 5
    threshold = np.percentile(red_channel, 100 - percent)
    # 阈值去噪处理与二值化
    _, binary = cv2.threshold(red_channel, threshold, 255, cv2.THRESH_BINARY)

    # 形态学操作去除小噪点
    kernel_denoise = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    phase1 = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel=kernel_denoise, iterations=1) # 去除大部分噪点
    # phase1 = cv2.erode(binary, kernel_denoise, iterations=1) # 去除大部分噪点
    # 这里可能需要多来几次
    phase2 = cv2.dilate(phase1, kernel_rect, iterations=1) # 把断裂处补上
    cleaned = cv2.erode(phase2, kernel_ellipse, iterations=1) # 平滑曲线

    # 骨架化提取中心线
    skeleton = skeletonize(cleaned // 255).astype(np.uint8) * 255

    # 找出各条中心线的矩阵表示，第二个返回值只在孔洞嵌套的闭合图形中有用，这里不管
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # 如果红色分量全是红色的离散点，单个点是不算长度的
    if not contours:
        return 0.0

    # 找到最长的轮廓
    main_contour = max(contours, key=lambda x: cv2.arcLength(x, False))

    # 去掉分叉
    main_contour, cleaned_main_contour = clean_main_contour(main_contour, skeleton.shape)

    # 计算曲线长度，这个方法本质是离散像素点欧氏距离的累加求和
    curve_length = cv2.arcLength(cleaned_main_contour, False)  / height * contour_size_height

    return curve_length
