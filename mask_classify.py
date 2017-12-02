import numpy as np
import skimage
import skimage.io
from skimage.filters import gaussian
import os
import glob
from keras.models import Sequential
from keras.layers.core import Flatten, Dense, Dropout
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD
from RunMain import VGG_16
import CallResult

import cv2

IMAGE_DIR = '/home/nishchal/workspace/MIT/6861/ILSVRC2013_DET_val/done'
MASK_DIR = '/home/nishchal/workspace/MIT/6861/saliency-salgan-2017/imagenet_saliency'
IMAGE_NAMES = []
VGG_WEIGHTS = '/home/nishchal/workspace/MIT/6861/saccadinator/vgg16_weights_tf_dim_ordering_tf_kernels.h5'
for img_name in glob.glob(os.path.join(MASK_DIR, '*')):
    IMAGE_NAMES.append(os.path.split(img_name)[-1])

# Make VGG model
model = VGG_16(VGG_WEIGHTS)
sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(optimizer=sgd, loss='categorical_crossentropy')

def make_masked_image(image, mask_img, threshold, blur=False, blur_amount=10):
    mask = mask_img <= threshold
    result = image.copy()
    if blur:
        back_image = gaussian(image, blur_amount)
        back_image = skimage.img_as_ubyte(back_image)
    else:
        back_image = np.zeros(image.shape)
    result[mask] = back_image[mask]
    return result

def test_image_at_levels(image_name, level_list, blur=False, blur_amount=10):
    img = skimage.io.imread(os.path.join(IMAGE_DIR, image_name[:-3]+'JPEG'))
    mask_img = skimage.io.imread(os.path.join(MASK_DIR, image_name))
    results = []
    for level in level_list:
        masked_image = make_masked_image(img, mask_img, level, blur, blur_amount)
        # Transform image for VGG
        masked_image = cv2.resize(masked_image, (224,224)).astype(np.float32)
        masked_image[:,:,0] -= 103.939
        masked_image[:,:,1] -= 116.779
        masked_image[:,:,2] -= 123.68
        masked_image = masked_image.transpose((1,0,2))
        masked_image = np.expand_dims(masked_image, axis=0)
        out = model.predict(masked_image)
        print(out.max())
        ordered_idx = np.argsort(-out)
        result = (CallResult.lines[int(ordered_idx[0][0])], out[0][ordered_idx[0]][0])
        results.append(result)


    return results

