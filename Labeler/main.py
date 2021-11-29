# -*- coding: utf-8 -*-
import sys, time, os, shutil
import os.path as path
import re
import tqdm

from combine import combine
from combineDepth import combineDepth
from getHead import main as getHeadMain
from mkInfo import getInfo, mkJson, mkMat
from getBbox import get_bbox

def deleteFile(fold):
    for fi in os.listdir(fold):
        if 'part' in fi or fi == 'pedInfo.xml':
            continue
        os.remove(path.join(fold, fi))

def mkdir(goal_dir):
    if not path.exists(goal_dir):
        os.makedirs(goal_dir)

if __name__ == '__main__':
    source_dir = r'/group/crowd_counting/GTAV-ours/data11/'
    target_dir = r'/group/crowd_counting/GTAV-ours/processed/'

    for part_dir in os.listdir(source_dir):
        print('---', part_dir, '---')
        if re.match(r'part_\d+_\d', part_dir) == None:
            continue
        start, foldNo = time.time(), 1
        goal_dir = path.join(target_dir, 'scene' + part_dir[4:])
        if os.path.exists(goal_dir):
            print(part_dir + ' has been processed')
            continue
        mkdir(goal_dir)
        subFolds = ('pngs', 'jpgs', 'bmps', 'jsons', 'mats', 'vis', 'segs', 'depth', 'point', 'bbox', 'matrix')
        for subFold in subFolds:
              mkdir(path.join(goal_dir, subFold))

        for foldName in tqdm.tqdm(os.listdir(os.path.join(source_dir, part_dir))):
            fold = path.join(source_dir, part_dir, foldName)
            if path.isdir(fold):
                try:
                    combine(fold)
                    combineDepth(fold)
                    get_bbox(fold)

                    shutil.move(path.join(fold, 'combination.png'), path.join(goal_dir, 'pngs', foldName + '.png'))
                    shutil.move(path.join(fold, 'combination.jpg'), path.join(goal_dir, 'jpgs', foldName + '.jpg'))
                    shutil.move(path.join(fold, 'combination.bmp'), path.join(goal_dir, 'bmps', foldName + '.bmp'))

                    getInfo(os.path.join(source_dir, part_dir), fold)
                    mkJson(path.join(goal_dir, 'jsons', foldName + '.json'))
                    mkMat(path.join(goal_dir, 'mats', foldName + '.mat'))

                    shutil.move(path.join(fold, 'combination.npy'), path.join(goal_dir, 'segs', foldName + '.raw'))

                    shutil.move(path.join(fold, 'bbox.jpg'), path.join(goal_dir, 'vis', foldName + '_bbox.jpg'))
                    shutil.move(path.join(fold, 'point.jpg'), path.join(goal_dir, 'vis', foldName + '_point.jpg'))
                    shutil.move(path.join(fold, 'seg.jpg'), path.join(goal_dir, 'vis', foldName + '_seg.jpg'))

                    shutil.move(path.join(fold, 'depth0.jpg'), path.join(goal_dir, 'vis', foldName + '_depth0.jpg'))
                    shutil.move(path.join(fold, 'depth1.jpg'), path.join(goal_dir, 'vis', foldName + '_depth1.jpg'))
                    shutil.move(path.join(fold, 'depth2.jpg'), path.join(goal_dir, 'vis', foldName + '_depth2.jpg'))
                    shutil.copy(path.join(fold, 'depth.raw'), path.join(goal_dir, 'depth', foldName + '.raw'))

                    shutil.copy(path.join(fold, 'matrix.txt'), path.join(goal_dir, 'matrix', foldName + '.txt'))
                    shutil.move(path.join(fold, 'bbox.txt'), path.join(goal_dir, 'bbox', foldName + '.txt'))
                    shutil.move(path.join(fold, 'pedInfo.json'), path.join(goal_dir, 'point', foldName + '.json'))
                except:
                    with open('error.log', 'a+') as f:
                        print('catch error in fold [' + fold + ']', file=f)
                        print('[fold No.{}]'.format(foldNo), foldName, 'error.')
                else:
                    print('[fold No.{}]'.format(foldNo), foldName, 'done.')
                    deleteFile(fold)
                finally:
                    foldNo += 1
        end = time.time()
        print('cost time:', end - start)
