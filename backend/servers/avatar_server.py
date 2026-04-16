import sys
import os
import cv2
import numpy as np
import pickle
import glob
from tqdm import tqdm

# Add wav2lip to sys.path to support local face_detection package and its dynamic imports
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wav2lip_path = os.path.join(backend_root, "wav2lip")
if wav2lip_path not in sys.path:
    sys.path.insert(0, wav2lip_path)

import face_detection
import torch
import asyncio
from utils.logger import logger

device = 'cuda' if torch.cuda.is_available() else 'cpu'

def osmakedirs(path_list):
    for path in path_list:
        os.makedirs(path) if not os.path.exists(path) else None

def video2imgs(vid_path, save_path, ext='.png', cut_frame=10000000):
    cap = cv2.VideoCapture(vid_path)
    count = 0
    while True:
        if count > cut_frame:
            break
        ret, frame = cap.read()
        if ret:
            cv2.putText(frame, "LiveTalking", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (128,128,128), 1)
            cv2.imwrite(f"{save_path}/{count:08d}{ext}", frame)
            count += 1
        else:
            break
    cap.release()

def read_imgs(img_list):
    frames = []
    logger.info('reading images...')
    for img_path in tqdm(img_list):
        frame = cv2.imread(img_path)
        frames.append(frame)
    return frames

def get_smoothened_boxes(boxes, T):
    for i in range(len(boxes)):
        if i + T > len(boxes):
            window = boxes[len(boxes) - T:]
        else:
            window = boxes[i : i + T]
        boxes[i] = np.mean(window, axis=0)
    return boxes

def face_detect(images, face_det_batch_size=2, pads=[0, 10, 0, 0], nosmooth=False):
    detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, 
                                            flip_input=False, device=device)

    batch_size = face_det_batch_size
    
    while 1:
        predictions = []
        try:
            for i in tqdm(range(0, len(images), batch_size)):
                predictions.extend(detector.get_detections_for_batch(np.array(images[i:i + batch_size])))
        except RuntimeError:
            if batch_size == 1: 
                raise RuntimeError('Image too big to run face detection on GPU. Please use a smaller batch size.')
            batch_size //= 2
            logger.warning('Recovering from OOM error; New batch size: {}'.format(batch_size))
            continue
        break

    results = []
    pady1, pady2, padx1, padx2 = pads
    for rect, image in zip(predictions, images):
        if rect is None:
            # cv2.imwrite('temp/faulty_frame.jpg', image) # check this frame where the face was not detected.
            raise ValueError('Face not detected! Ensure the video contains a face in all the frames.')

        y1 = max(0, rect[1] - pady1)
        y2 = min(image.shape[0], rect[3] + pady2)
        x1 = max(0, rect[0] - padx1)
        x2 = min(image.shape[1], rect[2] + padx2)
        
        results.append([x1, y1, x2, y2])

    boxes = np.array(results)
    if not nosmooth: boxes = get_smoothened_boxes(boxes, T=5)
    results = [[image[y1: y2, x1:x2], (y1, y2, x1, x2)] for image, (x1, y1, x2, y2) in zip(images, boxes)]

    del detector
    return results

def sync_generate_avatar(avatar_id: str, video_path: str, img_size: int = 256):
    try:
        # Get the backend root directory (parent of servers/)
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        avatar_path = os.path.join(backend_root, "data", "avatars", avatar_id)
        full_imgs_path = os.path.join(avatar_path, "full_imgs")
        face_imgs_path = os.path.join(avatar_path, "face_imgs")
        coords_path = os.path.join(avatar_path, "coords.pkl")
        
        osmakedirs([avatar_path, full_imgs_path, face_imgs_path])
        
        logger.info(f"Starting avatar generation for {avatar_id} from {video_path}")
        
        video2imgs(video_path, full_imgs_path, ext='.png')
        input_img_list = sorted(glob.glob(os.path.join(full_imgs_path, '*.[jpJP][pnPN]*[gG]')))

        frames = read_imgs(input_img_list)
        face_det_results = face_detect(frames) 
        
        coord_list = []
        idx = 0
        for frame, coords in face_det_results:        
            resized_crop_frame = cv2.resize(frame, (img_size, img_size))
            cv2.imwrite(f"{face_imgs_path}/{idx:08d}.png", resized_crop_frame)
            coord_list.append(coords)
            idx += 1
        
        with open(coords_path, 'wb') as f:
            pickle.dump(coord_list, f)
            
        logger.info(f"Successfully generated avatar {avatar_id}")
        return {"code": 0, "msg": "Avatar generated successfully"}
    except Exception as e:
        logger.error(f"Failed to generate avatar: {str(e)}")
        return {"code": -1, "msg": str(e)}

async def generate_avatar(avatar_id: str, video_path: str, img_size: int = 256):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sync_generate_avatar, avatar_id, video_path, img_size)
