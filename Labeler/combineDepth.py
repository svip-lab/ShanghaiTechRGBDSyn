# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np
import cv2
import time
import re
import os
import sys
import os.path as path
from functools import reduce

getImgArray = lambda img: np.array(Image.open(img))

def getorder(fileNames):
    filterFunc = lambda img: '.raw' in img and 'part' in img
    imgFileNames = filter(filterFunc, fileNames)
    order = sorted(int(re.findall(r'(\d+?).raw', imgFileName)[0]) for imgFileName in imgFileNames)
    return order

def backMask(fold, order):
    mask = np.full((1080, 1920), len(order), dtype='uint8')
    rgbDis = np.zeros((1080, 1920), dtype='int')
    imgTemp = path.join(fold, 'part_{}_{}.bmp')
    for o in order:
        back = getImgArray(imgTemp.format(o, 0)).astype('int')
        fore = getImgArray(imgTemp.format(o, 1)).astype('int')
        diff = np.sum((fore - back) ** 2, axis=2)
        mask = np.where(diff > rgbDis, o, mask)
        rgbDis = np.where(diff > rgbDis, diff, rgbDis)
    return mask

def getCurve(name):
    stencil = np.fromfile(name, 'uint8')
    stencil = stencil.reshape(1080, 1920)
    stencil = np.where(np.isin(stencil, (1, 17)), 1, 0).astype('uint8')
    return stencil

def combineDepth(fold):
    order = getorder(os.listdir(fold))
    mask = backMask(fold, order)

    curveTemp = path.join(fold, 'part_{}.raw')
    for o in order:
        curve = getCurve(curveTemp.format(o))
        mask = np.where(curve==1, o, mask)

    imgTemp = path.join(fold, 'depth_{}.raw')
    fimg = np.fromfile(imgTemp.format(0), np.float32)
    fimg = fimg.reshape(1080, 1920)

    for o in order[1:]:
        img = np.fromfile(imgTemp.format(o), np.float32)
        img = img.reshape(1080, 1920)
        fimg = np.where(mask==o, img, fimg)

    cv2.imwrite(fold + '/depth0.jpg', fimg*20000)
    d_vis = 2 ** fimg - 1
    d_vis = 1 / (d_vis + 1e-9)
    d_vis *= 0.001
    cv2.imwrite(fold + '/depth1.jpg', d_vis * 255)
    cv2.imwrite(fold + '/depth2.jpg', 255-d_vis*255)

    fimg = fimg.reshape(2073600)
    fimg.tofile(fold + r'/depth.raw')

    raw = getCurve(curveTemp.format(order[0]))
    for o in order[1:]:
        part = getCurve(curveTemp.format(o))
        raw = np.where(part == 1, part, raw)
    raw.reshape(-1).tofile(path.join(fold, 'combination.npy'))

def renderCurve(fold, No):
    stencil = getCurve(path.join(fold, "base_{}.raw".format(No)))
    stencil = stencil[:, :, np.newaxis]
    stencil = np.concatenate([stencil] * 3, axis=2)
    bmp = np.array(Image.open(path.join(fold, "base_{}.bmp".format(No))))
    combImg = np.where(stencil == 1, bmp, 0)
    bmp = Image.fromarray(combImg)
    bmp.save(path.join(fold, 'combination_{}.png'.format(No)))
    bmp.save(path.join(fold, 'combination_{}.jpg'.format(No)))

# if __name__ == '__main__':
#     # combine(sys.argv[1])
#     combine('source/part_11_2/1534540881')
