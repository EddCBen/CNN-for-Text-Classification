

'''
`TEXT Classifying CNN By 
                                          Charaf Eddine BENARAB 03/22/2020 
'''
#                                                                                   Note: The Gdrive Parameters are to be Changed.
#!pip install tensorflow==2.1.0
import tensorflow as tf 
from sklearn.model_selection import train_test_split
import gensim
import numpy as np 
from keras.utils import get_file
from keras.layers import Dense, Input, GlobalAveragePooling1D
from keras.layers import Conv1D, MaxPooling1D, Embedding  
from keras.models import Model, Sequential
from keras.layers import Input, Dense, Embedding, Conv2D, MaxPooling2D, Dropout,concatenate
from keras.activations import relu
from keras.layers.core import Reshape, Flatten
from keras.callbacks import EarlyStopping
from keras.optimizers import SGD
from keras.models import Model
from keras import regularizers
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils import to_categorical
import matplotlib.pyplot as plt

"""***Loading and preprocessing the ImDb dataset ***

**Creating a Google Drive Client**
"""

!pip install -U -q PyDrive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
# Authenticate and create the PyDrive client.
auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)
link ="https://drive.google.com/open?id=1R3zcK5nOrXnBKMZqD94y0KYwXsxlAUh3"
fluff, ID = link.split('=')
print(ID)

"""**Creating a Pandas dataFrame for the Dataset **"""

import pandas as pd 
downloaded = drive.CreateFile({'id':ID}) 
downloaded.GetContentFile('Filename.csv')  
df = pd.read_csv('Filename.csv')
df = df[['review','sentiment']]

"""**Cleaning the Data (Preprocessing)**"""

import re 
def clean_str(in_str):
    in_str = str(in_str)    
    in_str = re.sub(r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]\.[^\s]{2,})", "url", in_str)
    in_str = re.sub(r'([^\s\w]|_)+', '', in_str)
    return in_str.strip().lower()
df['text'] = df['review'].apply(clean_str)

df['l'] = df['review'].apply(lambda x: len(str(x).split(' ')))
print("mean length of sentence: " + str(df.l.mean()))
print("max length of sentence: " + str(df.l.max()))
print("std dev length of sentence: " + str(df.l.std()))

sequence_length = 2470
num_features = 20000                #max num of words to be embedded

tokenizer = Tokenizer(num_words=max_features, split=' ',  oov_token='<unw>')
tokenizer.fit_on_texts(df['review'].values)
word_index = tokenizer.word_index
X = tokenizer.texts_to_sequences(df['review'].values)
#padding the sequences 
X = pad_sequences(X, sequence_length)
y = pd.get_dummies(df['sentiment']).values
X_train, X_test, y_train, y_test = train_test_split(X,y, test_size = 0.1)

"""# **Loading Word2Vec preTrained Model from Google**"""

import gensim.downloader as api 
word2vec = api.load('word2vec-google-news-300')

"""# **Embedding layer**"""

#Prepariing the Embedding layer 
embedding_dim = 300 
vocabulary_size = min(len(word_index)+1, num_features) 
embedding_matrix = np.zeros((vocabulary_size, embedding_dim))

# Setting the Word2Vec values for the embedding matrix 
for word, i in word_index.items():
  if i >= num_features:
    continue
  try:
    embedding_vector = word2vec[word]
    embedding_matrix[i] = embedding_vector
  except KeyError:
    vec = np.zeros(embedding_dim)


del(word2vec)
embedding_layer = Embedding(vocabulary_size,
                            embedding_dim,
                            weights = [embedding_matrix],
                            trainable = False)  
del(embedding_matrix)

"""# ***Neural Network ***"""

# CNN for multiple filter sizes
from keras.constraints import max_norm 
sequence_length =  X_train.shape[1]
#The following parameters are specified in the Original paper under : "Baseline configuration"
filter_sizes = [3,4,5]
num_filters = 100 
drop = 0.5 
l2_norm = max_norm(3)
#preparing inputs ...
inputs = Input(shape=(sequence_length,))
embedding_sequence = embedding_layer(inputs)
reshape = Reshape((sequence_length,embedding_dim,1))(embedding_sequence)

# Six filters / 2 for each region size [3,4,5] // Convulutions

conv_0 = Conv2D(num_filters, (filter_sizes[0], embedding_dim),activation='relu',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(reshape)
conv_1 = Conv2D(num_filters, (filter_sizes[0], embedding_dim),activation='relu',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(reshape)
conv_2 = Conv2D(num_filters, (filter_sizes[1], embedding_dim),activation='relu',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(reshape)
conv_3 = Conv2D(num_filters, (filter_sizes[1], embedding_dim),activation='relu',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(reshape)
conv_4 = Conv2D(num_filters, (filter_sizes[2], embedding_dim),activation='relu',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(reshape)
conv_5 = Conv2D(num_filters, (filter_sizes[2], embedding_dim),activation='relu',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(reshape
                                         
#Max pooling the filter results 
maxpool_0 = MaxPooling2D((sequence_length - filter_sizes[0] + 1, 1), strides=(1,1))(conv_0)
maxpool_1 = MaxPooling2D((sequence_length - filter_sizes[0] + 1, 1), strides=(1,1))(conv_1)
maxpool_2 = MaxPooling2D((sequence_length - filter_sizes[1] + 1, 1), strides=(1,1))(conv_2)
maxpool_3 = MaxPooling2D((sequence_length - filter_sizes[1] + 1, 1), strides=(1,1))(conv_3)
maxpool_4 = MaxPooling2D((sequence_length - filter_sizes[2] + 1, 1), strides=(1,1))(conv_4)
maxpool_5 = MaxPooling2D((sequence_length - filter_sizes[2] + 1, 1), strides=(1,1))(conv_5)
                                         
# Now we merge the results into one vector 

merged_tensor = concatenate([maxpool_0,maxpool_1,maxpool_2,maxpool_3,maxpool_4,maxpool_5],axis=1)
flatten = Flatten()(merged_tensor)
dropout = Dropout(drop)(flatten)
output = Dense(units=2, activation='softmax',kernel_constraint=l2_norm,
                bias_constraint=l2_norm)(dropout)

#Decalring the Model to train 
model = Model(inputs = inputs, outputs = output)

"""# **Training Params Inspired by the Original Paper**"""

Stochastic_Grad_Desc = SGD(lr=0.01, momentum=0.9, decay=0.0001)
loss_func = 'categorical_crossentropy'
batch_size = 50 
model.compile(loss=loss_func, optimizer= Stochastic_Grad_Desc, metrics= ['accuracy'])
#print(model.summary())

"""# **Starting the Training**"""

history = model.fit(X_train, y_train, epochs=1, batch_size=batch_size, verbose=1,
                    validation_split=0.5, shuffle=True)

"""# **Saving the Model into a File**"""

from google.colab import drive

drive.mount('/content/gdrive')

model.save(filepath="/content/gdrive/My Drive/CNNforSentAnalysis.h5")
