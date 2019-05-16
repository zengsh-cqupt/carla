from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ray
from ray.tune import run_experiments

from env import CarlaEnv, ENV_CONFIG
# from models import register_carla_model
from models_lstm import register_carla_model


from scenarios import TOWN2_STRAIGHT, TOWN2_ONE_CURVE, TOWN2_NAVIGATION


env_config = ENV_CONFIG.copy()
# update config
env_config.update({
    "verbose": False,
    "x_res": 96,
    "y_res": 96,
    "use_depth_camera": False,
    "discrete_actions": True,
    "server_map": "/Game/Maps/Town02",
    "scenarios": TOWN2_ONE_CURVE,
})
register_carla_model()

ray.init(redirect_output=True)
run_experiments({
    "carla": {
        "run": "PPO",
        "env": CarlaEnv,
        "checkpoint_freq": 5,
        # "use_lstm": True,
        # "restore":"/home/gu/ray_results/carla/PPO_CarlaEnv_0_2019-05-15_12-26-41z6llpae8/checkpoint_1030/checkpoint-1030",
        "config": {
            "env_config": env_config,
            "model": {
                "custom_model": "carla",   # defined in model
                "use_lstm": True,
                # "lstm_use_prev_action_reward": True,
                "custom_options": {
                    "image_shape": [
                        env_config["x_res"], env_config["y_res"], 7
                    ],
                }
            },
            "num_workers": 10,
            "train_batch_size": 2400,
            "sample_batch_size": 120,
            "lambda": 0.95,
            "clip_param": 0.2,
            "num_sgd_iter": 20,
            "vf_share_layers": True,
            "lr": 0.0001,
            "sgd_minibatch_size": 64,
            "num_gpus": 2,
        },
    },
})
# /tmp/ray/session_2019-05-15_20-15-57_14951/tmpcpypfea8.json