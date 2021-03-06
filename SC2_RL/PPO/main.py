#!/usr/bin/python3
import gym
import numpy as np
import tensorflow as tf
from PPO import PPO_model

import sys
import sc2gym.envs
from absl import flags
from pysc2.lib import features
import numpy as np
FLAGS = flags.FLAGS
FLAGS(sys.argv)

ITERATION = 10000
EPISODE = 8
BATCH = 4
GAMMA = 0.95

#TRAIN = True
TRAIN = False

if not TRAIN:
    ITERATION = 100

def main():
    #map = 'SC2MoveToBeacon-v0'
    #map = 'SC2CollectMineralShards-v0'
    #map = 'SC2DefeatRoaches-v0'
    map = 'SC2DefeatZerglingsAndBanelings-v0'
    #map = 'SC2FindAndDefeatZerglings-v0'
    env = gym.make(map)
    ob_space = np.array(env.observation_space.shape[::-1])
    #act_space = np.prod(env.action_space.nvec)
    act_space = env.action_space
    with tf.Session() as sess:
        #print('act_space',act_space.nvec[0])
        #net = 'Network_G'
        net = 'Network'
        fold = "one/"+map
        if net == 'Network_G':
            fold = "group/"+map
        PPO = PPO_model(ob_space,act_space,sess,network=net, gamma=GAMMA)
        sess.run(tf.global_variables_initializer())
        PPO.restore_trainer("./ckpt/"+fold+"/summary/model.ckpt")
        total_reward=0
        rewards = 0
        max_reward=0
        if TRAIN:
            writer = tf.summary.FileWriter("./log/"+fold, sess.graph)
        for iteration in range(ITERATION):  # episode
            obs = env.reset()
            while True:
                act, v_pred = PPO.choose_action(obs)
                next_obs, reward, done,_ = env.step(act)
                total_reward+=reward
                rewards += reward
                if TRAIN:
                    if done and iteration % BATCH==0:
                        #不儲存最後一個
                        PPO.ep_vnt = PPO.ep_vs[1:]+[v_pred]
                        PPO.ep_gaes = PPO.get_gaes()
                        PPO.assign_policy_parameters()
                        for _ in range(EPISODE):
                            PPO.train()
                        summary = PPO.get_summary()
                        writer.add_summary(summary, iteration)
                        PPO.clear_all_array()
                        break
                    elif done:
                        break
                    else:
                        PPO.store_transition(obs,act,reward*100,v_pred)
                elif done:
                    break
                else:
                    #time.sleep(0.1)
                    pass

                obs = next_obs
            if max_reward < rewards:
                    max_reward = rewards
            rewards = 0
            if TRAIN:
                if iteration % 1000 == 0:
                    PPO.save_trainer("./ckpt/"+fold+"/model.ckpt")
                tfsum = tf.Summary(value=[tf.Summary.Value(tag='episode_reward', simple_value=sum(PPO.ep_rs)/100)])
                writer.add_summary(tfsum, iteration)
        print("average reward:",total_reward/ITERATION)
        print("max reward:",max_reward)
        if TRAIN:
            writer.close()
            PPO.save_trainer("./ckpt/"+fold+"/summary/model.ckpt")



if __name__ == '__main__':
    main()