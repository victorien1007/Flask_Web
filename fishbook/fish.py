import os.path
from fishbook import app
from PIL import Image
from keras import backend
from tensorflow import Graph, Session
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout

img_width, img_height = 100, 100
import tensorflow as tf
global graph,model
graph=tf.get_default_graph()
def create_model():

    model = Sequential()

    model.add(Conv2D(32, (3, 3), input_shape=(img_width, img_height, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(32, (3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(64, (3, 3), activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Flatten())
    model.add(Dense(64, activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(6, activation="softmax"))

    model.compile(loss='categorical_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])

    # model.summary()

    return model

'''graph=Graph()
with graph.as_default():
    session=Session(graph=graph)
    with session.as_default():
        create_model()'''

cnn_model = create_model()
cnn_model.load_weights(os.path.join(app.root_path, 'weight', 'fish_model_weights.h5'))

#PART 2. Using Neural Networks for Target Classification
import numpy as np
import matplotlib.pyplot as plt
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing.image import load_img, img_to_array
def load_image(img_path):

    img = load_img(img_path, target_size=(img_width, img_height))
    #plt.imshow(img)

    #img.save(os.path.dirname(__file__) + '/images/test.jpg')

    return img

#image_path = './images/train/Sailfish/123.jpg'
#image = load_image(image_path)
def fish_identification(img):

    fish_dict = {
    0 : 'Black bream',
    1 : 'Black grouper',
    2 : 'Bluefin tuna',
    3 : 'Mahi-mahi',
    4 : 'Sailfish',
    5 : 'Yellowtail'} # Prediction result dictionary

    img_array = img_to_array(img) # Convert image to array
    img_expand = np.expand_dims(img_array, axis=0) # Increase the dimension to match the generator input format
    img_normalization = img_expand / 255.0 # Normalize the image
    with graph.as_default():
        resulr_probability = cnn_model.predict(img_normalization) # Get predicted probability
    maximum_probability_index = np.argmax(resulr_probability) # Get the maximum probability index
    result = fish_dict[maximum_probability_index] # Get fish classification results

    return result


def fish(path):
    image=load_image(path)
    return fish_identification(image)
