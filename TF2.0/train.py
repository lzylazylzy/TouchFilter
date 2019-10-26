import copy
import os
import pickle
import time
from collections import defaultdict

import numpy as np
import scipy.io as sio
import tensorflow as tf
import trimesh as tm
from pyquaternion.quaternion import Quaternion as Q
# from mayavi import mlab

from config import flags
from model import Model

project_root = os.path.join(os.path.dirname(__file__), '..')

# load pca
pca = pickle.load(open(os.path.join(os.path.dirname(__file__), 'pca/pkl%d/pca_%d.pkl'%(flags.pca_size, flags.z_size)), 'rb'))
pca_components = pca.components_
pca_mean = pca.mean_
pca_var = pca.explained_variance_
print('PCA loaded.')

# load obj
cup_id_list = [1,2,3,4,5,6,7,8]
if flags.debug:
    cup_id_list = [1,2]

cup_models = {cup_id: tm.load_mesh(os.path.join(project_root, 'data/cups/onepiece/%d.obj'%cup_id)) for cup_id in cup_id_list}
print('Cup models loaded.')

# load data
cup_annotation = {x.split(',')[0]: x.strip().split(',')[1:] for x in open(os.path.join(project_root, 'data/cup_video_annotation.txt')).readlines()}

cup_rs = defaultdict(list)
obs_zs = defaultdict(list)

for i in cup_id_list:
    center = np.mean(cup_models[i].bounding_box.vertices, axis=0)
    for j in range(1,11):
        mat_data = sio.loadmat(os.path.join(project_root, 'data/grasp/cup%d/cup%d_grasping_60s_%d.mat'%(i,i,j)))['glove_data']
        annotation = cup_annotation['%d_%d'%(i,j)]
        for start_end in annotation:
            start, end = [int(x) for x in start_end.split(':')]
            for frame in range(start, end):
                if flags.debug and len(cup_rs[i]) > 1:
                    break
                cup_id = i
                cup_rotation = Q(mat_data[frame, 1 + 28 * 3 + 27 * 4: 1 + 28 * 3 + 28 * 4]).rotation_matrix
                cup_translation = mat_data[frame, 1 + 27 * 3 : 1 + 28 * 3]
                hand_jrot = mat_data[frame, 1 + 28 * 7 + 7 : 1 + 28 * 7 + 29]
                hand_grot = Q(mat_data[frame, 1 + 28 * 3 + 1 * 4 : 1 + 28 * 3 + 2 * 4]).rotation_matrix[:,:2]
                hand_gpos = mat_data[frame, 1 + 1 * 3 : 1 + 2 * 3] - cup_translation
                hand_jrot = np.stack([np.sin(hand_jrot), np.cos(hand_jrot)], axis=-1)
                hand_z = np.concatenate([hand_jrot.reshape([44]), hand_grot.reshape([6]), hand_gpos])
                if flags.use_pca:
                    hand_z = np.concatenate([np.matmul((hand_z[:flags.pca_size]-pca_mean), pca_components.T) / np.sqrt(pca_var), hand_z[flags.pca_size:]], axis=-1)
                cup_rs[cup_id].append(cup_rotation)
                obs_zs[cup_id].append(hand_z)

cup_rs = {i:np.array(x) for (i,x) in cup_rs.items()}
obs_zs = {i:np.array(x) for (i,x) in obs_zs.items()}

zs = np.vstack(obs_zs.values())
stddev = np.std(zs, axis=0)

minimum_data_length = min(len(cup_rs[cup_id]) for cup_id in cup_id_list)
data_idxs = {cup_id: np.arange(len(cup_rs[cup_id])) for cup_id in cup_id_list}
batch_num = minimum_data_length // flags.batch_size * len(cup_id_list)
print('Training data loaded.')

# load model
model = Model(flags, stddev)
print('Model loaded')

# create session
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)
sess.run(tf.global_variables_initializer())

# create directories
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'logs', flags.name), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'models'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'models', flags.name), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'figs'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'figs', flags.name), exist_ok=True)
log_dir = os.path.join(os.path.dirname(__file__), 'logs', flags.name)
model_dir = os.path.join(os.path.dirname(__file__), 'models', flags.name)
fig_dir = os.path.join(os.path.dirname(__file__), 'figs', flags.name)

# logger and saver
train_writer = tf.summary.FileWriter(log_dir, sess.graph)
saver = tf.train.Saver(max_to_keep=0)
if flags.restore_batch >= 0 and flags.restore_epoch >= 0:
    saver.restore(sess, os.path.join(model_dir, '%04d-%d.ckpt'%(flags.name, flags.restore_epoch, flags.restore_batch)))

print('Start training...')

# train
for epoch in range(flags.epochs):
    if epoch < flags.restore_epoch:
        continue

    shuffled_idxs = copy.deepcopy(data_idxs)
    for cup_id in cup_id_list:
        np.random.shuffle(shuffled_idxs[cup_id])
    
    for batch_id in range(batch_num):
        if batch_id < flags.restore_batch:
            continue
        
        t0 = time.time()
        cup_id = batch_id % len(cup_id_list) + 1
        item_id = batch_id // len(cup_id_list)
        idxs = shuffled_idxs[cup_id][flags.batch_size * item_id : flags.batch_size * (item_id + 1)]

        cup_r = cup_rs[cup_id][idxs]
        obs_z = obs_zs[cup_id][idxs]
        syn_z = np.zeros(obs_z.shape)
        syn_z[:,1::2] = 1
        syn_z[:,-9:] = [1, 0, 0, 1, 0, 0, 0, 0.3, 0.3]

        syn_z_seq = [syn_z]
        syn_e_seq = []
        syn_w_seq = []

        # ini_e = sess.run(model.inp_e[cup_id], feed_dict={model.cup_r: cup_r, model.inp_z: ini_z})

        for langevin_step in range(flags.langevin_steps):
            syn_z, syn_e, syn_w = sess.run(model.syn_zew[cup_id], feed_dict={model.cup_r: cup_r, model.inp_z: syn_z})
            # print(langevin_step, syn_z, syn_e, np.any(np.isnan(syn_w)), np.any(np.isinf(syn_w)))
            syn_z_seq.append(syn_z)
            syn_e_seq.append(syn_e)
            syn_w_seq.append(syn_w)
            if langevin_step % 100 == 99:
                syn_ew, obs_ew, loss, _ = sess.run([model.inp_ew[cup_id], model.obs_ew[cup_id], model.descriptor_loss[cup_id], model.des_train[cup_id]], feed_dict={
                    model.cup_r: cup_r, model.obs_z: obs_z, model.inp_z: syn_z
                })

        # syn_ew, obs_ew, loss, _ = sess.run([model.inp_ew[cup_id], model.obs_ew[cup_id], model.descriptor_loss[cup_id], model.des_train[cup_id]], feed_dict={
        #     model.cup_r: cup_r, model.obs_z: obs_z, model.inp_z: syn_z
        # })
        syn_e_seq.append(syn_ew[0])
        syn_w_seq.append(syn_ew[1])

        summ = sess.run(model.summ, feed_dict={model.summ_obs_e: obs_ew[0], model.summ_ini_e: syn_e_seq[0], model.summ_syn_e: syn_ew[0], model.summ_descriptor_loss: loss})
        train_writer.add_summary(summ, global_step=epoch * batch_num + batch_id)

        assert not (np.any(np.isnan(syn_z_seq)) or np.any(np.isinf(syn_z_seq)))
        print('\rE%dB%d/%d(C%d): Obs: %f, Ini: %f Syn: %f, Loss: %f, Time: %f'%(epoch, batch_id, batch_num, cup_id, obs_ew[0], syn_e_seq[0], syn_ew[0], loss, time.time() - t0), end='')
        
        if item_id % 100 == 0:
            data = {
                'cup_id': cup_id, 
                'cup_r' : cup_r, 
                'obs_z' : obs_z, 
                'obs_e' : obs_ew[0], 
                'obs_w' : obs_ew[1], 
                'syn_e' : syn_e_seq, 
                'syn_z' : syn_z_seq, 
                'syn_w' : syn_w_seq
            }

            pickle.dump(data, open(os.path.join(fig_dir, '%04d-%d.pkl'%(epoch, batch_id)), 'wb'))
            saver.save(sess, os.path.join(model_dir, '%04d-%d.ckpt'%(epoch, batch_id)))

    print()

# python train.py --pca_size 44 --z_size 2 --use_pca --debug --batch_size 1 --step_size 0.01 --adaptive_langevin --langevin_steps 90 --clip_norm_langevin