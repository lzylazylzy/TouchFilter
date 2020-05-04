import os
import pickle
import sys

import numpy as np
import matplotlib.pyplot as plt

sys.path.append('..')
from utils.viz_util import Visualizer
visualizer = Visualizer()

# name = 'exp'
# epoch = 82

epochs = [45,45,45,45]

for exp in range(4):
    name = 'exp%d'%exp
    epoch = epochs[exp]
    if os.path.exists('%s-%d-gen-dist.png'%(name, epoch)):
        continue
    data = pickle.load(open(os.path.join('../logs/logs/%s/%04d.pkl'%(name, epoch)), 'rb'))
    obj_id, gen_hand, syn_hand, GE, SE, g_ema = data
    os.makedirs('%s-%d'%(name, epoch), exist_ok=True)
    diff = np.zeros([len(gen_hand), len(gen_hand)])
    for i in range(len(gen_hand)):
        for j in range(len(gen_hand)):
            diff[i,j] = np.linalg.norm(gen_hand[i] - gen_hand[j]) / np.linalg.norm(gen_hand[i])
    plt.clf()
    _ = plt.imshow(diff)
    plt.axis('off')
    plt.colorbar(_)
    # plt.show()
    plt.savefig('%s-%d/gen-diff.png'%(name, epoch))
    for i in range(len(syn_hand)):
        print(name, epoch, GE[i], SE[i])
        try:
            visualizer.visualize_distance(3, gen_hand[0], '%s-%d/%d-gen'%(name, epoch, i))
            visualizer.visualize_distance(3, syn_hand[0], '%s-%d/%d-syn'%(name, epoch, i))
        except:
            pass