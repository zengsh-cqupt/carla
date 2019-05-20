# mode = "mnist"
# mode = "carla"
# mode = "check"
mode = "carla_high"
if mode == "mnist":
    IMG_SIZE = (28, 28, 1)
    epochs = 15
    latent_dim = 2
    beta = 1
    scale = 1
    scale_r = 600
    lr = 1e-5
    batch_size = 100
    use_pretrained = False
    filepath = "/home/gu/project/ppo/ppo_carla/models/mnist/ld_{}_beta_{}_r_{}.hdf5".format(latent_dim, beta, scale_r)
elif mode == "carla":
    IMG_SIZE = (128, 128, 3)
    epochs = 300
    latent_dim = 1024
    beta = 1
    scale = 1 / beta
    scale_r = 1100
    lr = 1e-5
    batch_size = 100
    use_pretrained = False
    filepath = "/home/gu/project/ppo/ppo_carla/models/carla/2_ld_{}_beta_{}_r_{}_lr_{}.hdf5".format(latent_dim, beta,
                                                                                                    scale_r, lr)
elif mode == "carla_high":
    IMG_SIZE = (128, 128, 3)
    epochs = 30
    latent_dim = 256
    beta = 1
    scale = 1 / beta
    scale_r = 100
    lr = 1e-4
    batch_size = 100
    use_pretrained = False
    filepath = "/home/gu/project/ppo/ppo_carla/models/carla/high_ld_{}_beta_{}_r_{}_lr_{}.hdf5".format(latent_dim, beta,
                                                                                                       scale_r, lr)
elif mode == "check":
    IMG_SIZE = (128, 128, 3)
    epochs = 100
    latent_dim = 50
    beta = 1
    scale = 1 / beta
    scale_r = 1100
    lr = 1e-5
    batch_size = 100
    use_pretrained = True
    mode = "carla"
    # filepath = "/home/gu/project/ppo/ppo_carla/models/carla/ld_{}_beta_{}_r_{}_lr_{}.hdf5".format(latent_dim, beta, scale_r, lr)
    filepath = "/home/gu/project/ppo/ppo_carla/models/carla/ld_512_beta_1_r_1100_lr_1e-05.hdf5"
