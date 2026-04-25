"""
头像素材生成服务。

生成一个可驱动的数字人头像，大致要走这几步：
1. 把输入视频拆成逐帧图片。
2. 对每一帧做人脸检测。
3. 把检测到的人脸区域裁出来并统一缩放。
4. 保存整帧图、人脸图、以及贴回时要用到的人脸框坐标。

最终产物会落到 `data/avatars/<avatar_id>/` 目录下。
"""

import sys
import os
import cv2
import numpy as np
import pickle
import glob
from tqdm import tqdm

# face_detection 是项目内嵌的本地模块，不是 pip 包。
# 这里手动把 `backend/wav2lip` 放进搜索路径，保证 `import face_detection` 可用。
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wav2lip_path = os.path.join(backend_root, "wav2lip")
if wav2lip_path not in sys.path:
    sys.path.insert(0, wav2lip_path)

import face_detection
import torch
import asyncio
from utils.logger import logger

device = "cuda" if torch.cuda.is_available() else "cpu"


def osmakedirs(path_list):
    """批量创建目录；目录已存在时静默跳过。"""
    for path in path_list:
        os.makedirs(path) if not os.path.exists(path) else None


def video2imgs(vid_path, save_path, ext=".png", cut_frame=10000000):
    """
    把视频拆成连续图片帧。

    这里会顺手把 `LiveTalking` 水印打到每一帧上，后续生成的头像素材也会带着它。
    """
    cap = cv2.VideoCapture(vid_path)
    count = 0
    while True:
        if count > cut_frame:
            break
        ret, frame = cap.read()
        if ret:
            cv2.putText(
                frame,
                "LiveTalking",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                (128, 128, 128),
                1,
            )
            cv2.imwrite(f"{save_path}/{count:08d}{ext}", frame)
            count += 1
        else:
            break
    cap.release()


def read_imgs(img_list):
    """把图片路径列表一次性读入内存。"""
    frames = []
    logger.info("reading images...")
    for img_path in tqdm(img_list):
        frame = cv2.imread(img_path)
        frames.append(frame)
    return frames


def get_smoothened_boxes(boxes, T):
    """
    对相邻帧的人脸框做滑动平均。

    这样做的目的是减少框抖动，否则后面贴脸或裁脸时容易出现跳动感。
    """
    for i in range(len(boxes)):
        if i + T > len(boxes):
            window = boxes[len(boxes) - T :]
        else:
            window = boxes[i : i + T]
        boxes[i] = np.mean(window, axis=0)
    return boxes


def face_detect(images, face_det_batch_size=2, pads=[0, 10, 0, 0], nosmooth=False):
    """
    对整组图片做批量人脸检测，并返回裁剪后的人脸和原图坐标。

    返回结果里的 `coords` 很关键：
    后续推理得到的新嘴型图，会按这个坐标贴回原图。
    """
    detector = face_detection.FaceAlignment(
        face_detection.LandmarksType._2D, flip_input=False, device=device
    )

    batch_size = face_det_batch_size

    while 1:
        predictions = []
        try:
            for i in tqdm(range(0, len(images), batch_size)):
                predictions.extend(
                    detector.get_detections_for_batch(np.array(images[i : i + batch_size]))
                )
        except RuntimeError:
            if batch_size == 1:
                raise RuntimeError(
                    "Image too big to run face detection on GPU. Please use a smaller batch size."
                )
            batch_size //= 2
            logger.warning("Recovering from OOM error; New batch size: {}".format(batch_size))
            continue
        break

    results = []
    pady1, pady2, padx1, padx2 = pads
    for rect, image in zip(predictions, images):
        if rect is None:
            raise ValueError("Face not detected! Ensure the video contains a face in all the frames.")

        y1 = max(0, rect[1] - pady1)
        y2 = min(image.shape[0], rect[3] + pady2)
        x1 = max(0, rect[0] - padx1)
        x2 = min(image.shape[1], rect[2] + padx2)

        results.append([x1, y1, x2, y2])

    boxes = np.array(results)
    if not nosmooth:
        boxes = get_smoothened_boxes(boxes, T=5)
    results = [
        [image[y1:y2, x1:x2], (y1, y2, x1, x2)]
        for image, (x1, y1, x2, y2) in zip(images, boxes)
    ]

    del detector
    return results


def sync_generate_avatar(avatar_id: str, video_path: str, img_size: int = 256):
    """
    同步执行头像素材生成。

    这是实际干活的函数，异步版本只是把它丢到线程池里跑。
    """
    try:
        # 为当前 avatar 创建标准目录结构。
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        avatar_path = os.path.join(backend_root, "data", "avatars", avatar_id)
        full_imgs_path = os.path.join(avatar_path, "full_imgs")
        face_imgs_path = os.path.join(avatar_path, "face_imgs")
        coords_path = os.path.join(avatar_path, "coords.pkl")

        osmakedirs([avatar_path, full_imgs_path, face_imgs_path])

        logger.info(f"Starting avatar generation for {avatar_id} from {video_path}")

        # 1. 先拆帧，拿到完整原图序列。
        video2imgs(video_path, full_imgs_path, ext=".png")
        input_img_list = sorted(glob.glob(os.path.join(full_imgs_path, "*.[jpJP][pnPN]*[gG]")))

        # 2. 再做人脸检测，拿到裁剪后的人脸和对应坐标。
        frames = read_imgs(input_img_list)
        face_det_results = face_detect(frames)

        coord_list = []
        idx = 0
        for frame, coords in face_det_results:
            # 3. 把人脸统一缩放到模型输入尺寸，方便 Wav2Lip 推理。
            resized_crop_frame = cv2.resize(frame, (img_size, img_size))
            cv2.imwrite(f"{face_imgs_path}/{idx:08d}.png", resized_crop_frame)
            coord_list.append(coords)
            idx += 1

        # 4. 把坐标序列持久化，之后渲染阶段会反复读取。
        with open(coords_path, "wb") as f:
            pickle.dump(coord_list, f)

        logger.info(f"Successfully generated avatar {avatar_id}")
        return {"code": 0, "msg": "Avatar generated successfully"}
    except Exception as e:
        logger.error(f"Failed to generate avatar: {str(e)}")
        return {"code": -1, "msg": str(e)}


async def generate_avatar(avatar_id: str, video_path: str, img_size: int = 256):
    """异步包装器：把耗时素材生成任务放到线程池执行。"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_generate_avatar, avatar_id, video_path, img_size)
