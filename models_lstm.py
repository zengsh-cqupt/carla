from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf
import tensorflow.contrib.slim as slim
from tensorflow.contrib.layers import xavier_initializer
import sys
from ray.rllib.models.catalog import ModelCatalog
from ray.rllib.models.misc import normc_initializer
from ray.rllib.models.model import Model
# tf.enable_eager_execution()
from collections import OrderedDict

import gym
import tensorflow as tf

from ray.rllib.models.misc import linear, normc_initializer
from ray.rllib.models.preprocessors import get_preprocessor
from ray.rllib.utils.annotations import PublicAPI

import tensorflow as tf

import resnet_utils


class CarlaModel(Model):
    """Carla model that can process the observation tuple.

    The architecture processes the image using convolutional layers, the
    metrics using fully connected layers, and then combines them with
    further fully connected layers.
    """

    def _build_layers_v2(self, input_dict, num_outputs, options):
        """{'obs': [ < tf.Tensor 'default/Reshape:0' shape = (?, 96, 96, 8) dtype = float32 >,   image space
                     < tf.Tensor 'default/Reshape_1:0' shape = (?, 5) dtype = float32 >,         discrete 5
                     < tf.Tensor 'default/Reshape_2:0' shape = (?, 2) dtype = float32 >],        box 2
            'prev_actions': <tf.Tensor 'default / action_1: 0' shape=(?, 2) dtype=float32>,
            'prev_rewards': <tf.Tensor 'default / prev_reward: 0' shape=(?,) dtype=float32>,
            'is_training': <tf.Tensor 'default / PlaceholderWithDefault: 0' shape=() dtype = bool >}"""

        convs = options.get("structure", [
            [48, [4, 4], 3],
            [64, [4, 4], 2],
            [72, [3, 3], 2],
            [128, [3, 3], 1],
            [256, [3, 3], 1],
            [1024, [8, 8], 1],
        ])

        hiddens = options.get("fcnet_hiddens", [700, 100])
        fcnet_activation = options.get("fcnet_activation", "elu")
        if fcnet_activation == "tanh":
            activation = tf.nn.tanh
        elif fcnet_activation == "relu":
            activation = tf.nn.relu
        elif fcnet_activation == "elu":
            activation = tf.nn.elu

        vision_in = input_dict['obs'][0]
        metrics_in = tf.concat([input_dict['obs'][1], input_dict['obs'][2]], axis=-1)

        with tf.name_scope("carla_vision"):
            for i, (out_size, kernel, stride) in enumerate(convs[:-1], 1):
                vision_in = slim.conv2d(
                    vision_in,
                    out_size,
                    kernel,
                    stride,
                    activation_fn=activation,
                    scope="conv{}".format(i))
                vision_in = tf.layers.batch_normalization(
                    vision_in, training=input_dict["is_training"])

            out_size, kernel, stride = convs[-1]
            vision_in = slim.conv2d(
                vision_in,
                out_size,
                kernel,
                stride,
                activation_fn=activation,
                padding="VALID",
                scope="conv_out")
            vision_in = tf.squeeze(vision_in, [1, 2])

        # Setup metrics layer
        with tf.name_scope("carla_metrics"):
            metrics_in = slim.fully_connected(
                metrics_in,
                90,
                weights_initializer=xavier_initializer(),
                activation_fn=activation,
                scope="metrics_out")

        with tf.name_scope("carla_out"):
            i = 1
            last_layer = tf.concat([vision_in, metrics_in], axis=1)
            print("Shape of concatenated out is", last_layer.shape)
            for size in hiddens:
                last_layer = slim.fully_connected(
                    last_layer,
                    size,
                    weights_initializer=xavier_initializer(),
                    activation_fn=activation,
                    scope="fc{}".format(i))
                i += 1
            output = slim.fully_connected(
                last_layer,
                num_outputs,
                weights_initializer=normc_initializer(0.01),
                activation_fn=None,
                scope="fc_out")

        return output, last_layer

    def value_function(self):
        hiddens = [400, 300]
        last_layer = self.last_layer
        with tf.name_scope("value_function"):
            i = 0
            for size in hiddens:
                last_layer = slim.fully_connected(last_layer, size, weights_initializer=xavier_initializer(),
                                                 activation_fn=tf.nn.elu,scope="value_function{}".format(i))
                i += 1
            output = slim.fully_connected(last_layer, 1, weights_initializer=normc_initializer(0.01),
                                                 activation_fn=None,scope="value_out")
        return tf.reshape(output, [-1])

    def value_function(self):
        """Builds the value function output.

        This method can be overridden to customize the implementation of the
        value function (e.g., not sharing hidden layers).

        Returns:
            Tensor of size [BATCH_SIZE] for the value function.
        """
        hiddens = [400, 300]
        with tf.name_scope("carla_out"):
            i = 1
            for size in hiddens:
                last_layer = slim.fully_connected(
                    last_layer,
                    size,
                    weights_initializer=xavier_initializer(),
                    activation_fn=tf.nn.elu,
                    scope="value_function{}".format(i))
                i += 1
            output = slim.fully_connected(
                last_layer,
                1,
                weights_initializer=normc_initializer(0.01),
                activation_fn=None,
                scope="value_out")
        # return output
        return tf.reshape(output, [-1])

def register_carla_model():
    ModelCatalog.register_custom_model("carla", CarlaModel)

# slim = tf.contrib.slim
# resnet_arg_scope = resnet_utils.resnet_arg_scope
#
# @slim.add_arg_scope
# def bottleneck(inputs, depth, depth_bottleneck, stride, rate=1,
#                outputs_collections=None, scope=None):
#     """Bottleneck residual unit variant with BN before convolutions.
#     This is the full preactivation residual unit variant proposed in [2]. See
#     Fig. 1(b) of [2] for its definition. Note that we use here the bottleneck
#     variant which has an extra bottleneck layer.
#     When putting together two consecutive ResNet blocks that use this unit, one
#     should use stride = 2 in the last unit of the first block.
#     Args:
#       inputs: A tensor of size [batch, height, width, channels].
#       depth: The depth of the ResNet unit output.
#       depth_bottleneck: The depth of the bottleneck layers.
#       stride: The ResNet unit's stride. Determines the amount of downsampling of
#         the units output compared to its input.
#       rate: An integer, rate for atrous convolution.
#       outputs_collections: Collection to add the ResNet unit output.
#       scope: Optional variable_scope.
#     Returns:
#       The ResNet unit's output.
#     """
#     with tf.variable_scope(scope, 'bottleneck_v2', [inputs]) as sc:
#         depth_in = slim.utils.last_dimension(inputs.get_shape(), min_rank=4)
#         preact = slim.batch_norm(inputs, activation_fn=tf.nn.relu, scope='preact')
#         if depth == depth_in:
#             shortcut = resnet_utils.subsample(inputs, stride, 'shortcut')
#         else:
#             shortcut = slim.conv2d(preact, depth, [1, 1], stride=stride,
#                                    normalizer_fn=None, activation_fn=None,
#                                    scope='shortcut')
#
#         residual = slim.conv2d(preact, depth_bottleneck, [1, 1], stride=1,
#                                scope='conv1')
#         residual = resnet_utils.conv2d_same(residual, depth_bottleneck, 3, stride,
#                                             rate=rate, scope='conv2')
#         residual = slim.conv2d(residual, depth, [1, 1], stride=1,
#                                normalizer_fn=None, activation_fn=None,
#                                scope='conv3')
#
#         output = shortcut + residual
#
#         return slim.utils.collect_named_outputs(outputs_collections,
#                                                 sc.name,
#                                                 output)
#
# def resnet_v2(inputs,
#               blocks,
#               num_classes=None,
#               is_training=True,
#               global_pool=True,
#               output_stride=None,
#               include_root_block=True,
#               spatial_squeeze=True,
#               reuse=None,
#               scope=None):
#     """Generator for v2 (preactivation) ResNet models.
#     This function generates a family of ResNet v2 models. See the resnet_v2_*()
#     methods for specific model instantiations, obtained by selecting different
#     block instantiations that produce ResNets of various depths.
#     Training for image classification on Imagenet is usually done with [224, 224]
#     inputs, resulting in [7, 7] feature maps at the output of the last ResNet
#     block for the ResNets defined in [1] that have nominal stride equal to 32.
#     However, for dense prediction tasks we advise that one uses inputs with
#     spatial dimensions that are multiples of 32 plus 1, e.g., [321, 321]. In
#     this case the feature maps at the ResNet output will have spatial shape
#     [(height - 1) / output_stride + 1, (width - 1) / output_stride + 1]
#     and corners exactly aligned with the input image corners, which greatly
#     facilitates alignment of the features to the image. Using as input [225, 225]
#     images results in [8, 8] feature maps at the output of the last ResNet block.
#     For dense prediction tasks, the ResNet needs to run in fully-convolutional
#     (FCN) mode and global_pool needs to be set to False. The ResNets in [1, 2] all
#     have nominal stride equal to 32 and a good choice in FCN mode is to use
#     output_stride=16 in order to increase the density of the computed features at
#     small computational and memory overhead, cf. http://arxiv.org/abs/1606.00915.
#     Args:
#       inputs: A tensor of size [batch, height_in, width_in, channels].
#       blocks: A list of length equal to the number of ResNet blocks. Each element
#         is a resnet_utils.Block object describing the units in the block.
#       num_classes: Number of predicted classes for classification tasks.
#         If 0 or None, we return the features before the logit layer.
#       is_training: whether batch_norm layers are in training mode.
#       global_pool: If True, we perform global average pooling before computing the
#         logits. Set to True for image classification, False for dense prediction.
#       output_stride: If None, then the output will be computed at the nominal
#         network stride. If output_stride is not None, it specifies the requested
#         ratio of input to output spatial resolution.
#       include_root_block: If True, include the initial convolution followed by
#         max-pooling, if False excludes it. If excluded, `inputs` should be the
#         results of an activation-less convolution.
#       spatial_squeeze: if True, logits is of shape [B, C], if false logits is
#           of shape [B, 1, 1, C], where B is batch_size and C is number of classes.
#           To use this parameter, the input images must be smaller than 300x300
#           pixels, in which case the output logit layer does not contain spatial
#           information and can be removed.
#       reuse: whether or not the network and its variables should be reused. To be
#         able to reuse 'scope' must be given.
#       scope: Optional variable_scope.
#     Returns:
#       net: A rank-4 tensor of size [batch, height_out, width_out, channels_out].
#         If global_pool is False, then height_out and width_out are reduced by a
#         factor of output_stride compared to the respective height_in and width_in,
#         else both height_out and width_out equal one. If num_classes is 0 or None,
#         then net is the output of the last ResNet block, potentially after global
#         average pooling. If num_classes is a non-zero integer, net contains the
#         pre-softmax activations.
#       end_points: A dictionary from components of the network to the corresponding
#         activation.
#     Raises:
#       ValueError: If the target output_stride is not valid.
#     """
#     with tf.variable_scope(scope, 'resnet_v2', [inputs], reuse=reuse) as sc:
#         end_points_collection = sc.original_name_scope + '_end_points'
#         with slim.arg_scope([slim.conv2d, bottleneck,
#                              resnet_utils.stack_blocks_dense],
#                             outputs_collections=end_points_collection):
#             with slim.arg_scope([slim.batch_norm], is_training=is_training):
#                 net = inputs
#                 if include_root_block:
#                     if output_stride is not None:
#                         if output_stride % 4 != 0:
#                             raise ValueError('The output_stride needs to be a multiple of 4.')
#                         output_stride /= 4
#                     # We do not include batch normalization or activation functions in
#                     # conv1 because the first ResNet unit will perform these. Cf.
#                     # Appendix of [2].
#                     with slim.arg_scope([slim.conv2d],
#                                         activation_fn=None, normalizer_fn=None):
#                         net = resnet_utils.conv2d_same(net, 64, 7, stride=2, scope='conv1')
#                     net = slim.max_pool2d(net, [3, 3], stride=2, scope='pool1')
#                 net = resnet_utils.stack_blocks_dense(net, blocks, output_stride)
#                 # This is needed because the pre-activation variant does not have batch
#                 # normalization or activation functions in the residual unit output. See
#                 # Appendix of [2].
#                 net = slim.batch_norm(net, activation_fn=tf.nn.relu, scope='postnorm')
#                 # Convert end_points_collection into a dictionary of end_points.
#                 end_points = slim.utils.convert_collection_to_dict(
#                     end_points_collection)
#
#                 if global_pool:
#                     # Global average pooling.
#                     net = tf.reduce_mean(net, [1, 2], name='pool5', keep_dims=True)
#                     end_points['global_pool'] = net
#                 if num_classes:
#                     net = slim.conv2d(net, num_classes, [1, 1], activation_fn=None,
#                                       normalizer_fn=None, scope='logits')
#                     end_points[sc.name + '/logits'] = net
#                     if spatial_squeeze:
#                         net = tf.squeeze(net, [1, 2], name='SpatialSqueeze')
#                         end_points[sc.name + '/spatial_squeeze'] = net
#                     end_points['predictions'] = slim.softmax(net, scope='predictions')
#                 return net, end_points
#
# resnet_v2.default_image_size = 224
#
# def resnet_v2_block(scope, base_depth, num_units, stride):
#     """Helper function for creating a resnet_v2 bottleneck block.
#     Args:
#       scope: The scope of the block.
#       base_depth: The depth of the bottleneck layer for each unit.
#       num_units: The number of units in the block.
#       stride: The stride of the block, implemented as a stride in the last unit.
#         All other units have stride=1.
#     Returns:
#       A resnet_v2 bottleneck block.
#     """
#     return resnet_utils.Block(scope, bottleneck, [{
#         'depth': base_depth * 4,
#         'depth_bottleneck': base_depth,
#         'stride': 1
#     }] * (num_units - 1) + [{
#         'depth': base_depth * 4,
#         'depth_bottleneck': base_depth,
#         'stride': stride
#     }])
#
#
# def resnet_v2_50(inputs,
#                  num_classes=None,
#                  is_training=True,
#                  global_pool=True,
#                  output_stride=None,
#                  spatial_squeeze=True,
#                  reuse=None,
#                  scope='resnet_v2_50'):
#     """ResNet-50 model of [1]. See resnet_v2() for arg and return description."""
#     blocks = [
#         resnet_v2_block('block1', base_depth=64, num_units=3, stride=2),
#         resnet_v2_block('block2', base_depth=128, num_units=4, stride=2),
#         resnet_v2_block('block3', base_depth=256, num_units=6, stride=2),
#         resnet_v2_block('block4', base_depth=512, num_units=3, stride=1),
#     ]
#     return resnet_v2(inputs, blocks, num_classes, is_training=is_training,
#                      global_pool=global_pool, output_stride=output_stride,
#                      include_root_block=True, spatial_squeeze=spatial_squeeze,
#                      reuse=reuse, scope=scope)
#
#
# resnet_v2_50.default_image_size = resnet_v2.default_image_size

