from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import time
import re
import sys
import os
import os.path as path
import json
import cv2
import math

headJson = []

class pedestrian:
    def __init__(self, info):
        self.id = int(info[0])
        boneLoc = map(lambda x: re.findall(r" x=(.*?) y=(.*?) />", x)[0], info[1].strip().split('\n\t'))
        bones = boneLoc
        self.bones = np.array(list(bones), dtype='float32')  # e.g.[[0.319012 0.334564]]

def render(stencil, origin):
    x, y, z = origin.shape
    nshape = np.array([255, 255, 0], dtype='uint8')
    psize = 3
    top, bottom = max(0, stencil[0] - psize), min(x, stencil[0] + psize)
    left, right = max(0, stencil[1] - psize), min(y, stencil[1] + psize)
    mark = np.ones((bottom - top, right - left), dtype='uint8')
    mark = np.pad(mark, ((top, x - bottom), (left, y - right)), 'constant')
    for i in range(z):
        origin[:, :, i] = np.where(mark == 1, nshape[i], origin[:, :, i])
    return origin

def multiRender(bmp, p, stencil):
    boneLoc = np.dot(p.bones, np.array([[0, 1920], [1080, 0]])).round().astype('int')  # remap to image size
    headLoc = (boneLoc[0] - 1).tolist()
    x, y = headLoc
    if x >= 0 and y >= 0 and stencil[x, y]:
        bmp = render(headLoc, bmp)
        headJson.append(headLoc)
    return bmp

def runRender(fold, peds, rendfunc, bmpName='result'):
    bmpArray = cv2.imread(path.join(fold, 'combination.bmp'))
    pointArray = cv2.imread(path.join(fold, 'combination.bmp'))
    depth = np.fromfile(path.join(fold, 'depth.raw'), dtype=np.float32)
    depth = depth.reshape(1080, 1920)  # max=1.0

    stencil = np.fromfile(path.join(fold, 'combination.npy'), 'uint8')  # stencil->segmentation
    stencil = stencil.reshape(1080, 1920)

    for p in peds:
        if p.bones.shape[0] == 0:
            continue

        boneLoc = np.dot(p.bones, np.array([[0, 1920], [1080, 0]])).round().astype('int')
        headLoc = (boneLoc[0] - 1).tolist()
        x, y = headLoc
        if x < 0 or y < 0:
            continue

        alpha = depth[x, y]
        inter = 2 ** alpha - 1
        inter = 1 / inter
        inter *= 0.1
        length = int(0.8 * 0.15 * 1483 / inter)

        beta = depth[x-length:x+length, y-length:y+length]
        mask = stencil[x-length:x+length, y-length:y+length]
        beta = beta * mask
        if np.sum(mask) == 0:
            continue
        beta = np.sum(beta) / np.sum(mask)
        inter = 2 ** beta - 1
        inter = 1 / inter
        inter *= 0.1
        length = int(0.8 * 0.15 * 1483 / inter)

        offset = math.ceil(length * 0.15)
        x -= offset

        bound = int(length / 2)

        if stencil[x, y] or np.sum(stencil[x - bound:x + bound, y - bound:y + bound])/((bound*2)**2) > 0.75:
            headJson.append(headLoc)
            cv2.rectangle(bmpArray, (y-length, x-length), (y+length, x+length), (0, 255, 255), 3)
            cv2.circle(pointArray, (y, x), 4, (0, 255, 255), -1)
            with open(path.join(fold, 'bbox.txt'), 'a') as f:
                f.write(str(y-length)+' '+str(x-length)+' '+str(y+length)+' '+str(x+length))
                f.write('\r\n')
    cv2.imwrite(path.join(fold, 'point.jpg'), pointArray)
    cv2.imwrite(path.join(fold, 'bbox.jpg'), bmpArray)

def get_bbox(fold):
    peds = []
    with open(path.join(fold, 'pedInfo.xml')) as f:
        info = re.findall(r'<ped id=(\d+?)>([\s\S]*?)</ped>', f.read())
        peds = list(map(pedestrian, info))
        if len(peds) == 0:
            print(fold + 'error: no peds')

    runRender(fold, peds, multiRender, bmpName='result')

    with open(path.join(fold, 'pedInfo.json'), 'w+') as f:
        global headJson
        json.dump(headJson, f)
        headJson = []


# if __name__ == '__main__':
#     get_bbox(sys.argv[1])
