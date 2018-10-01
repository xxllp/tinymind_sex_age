from keras import models
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.layers import BatchNormalization
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.core import Dense, Activation, Dropout
from keras.models import Sequential
from keras.optimizers import Adam
from keras.utils import np_utils
from sklearn.cross_validation import train_test_split

from tiny.tfidf import *
from tiny.usage import *

tmp_model = './model/checkpoint/dnn_best_tmp.hdf5'
np.random.seed(47)
def train_dnn(dropout, lr):
    #dropout = 0.7

    args = locals()

    feature_label = get_feature_label_dnn()


    test = feature_label[feature_label['sex'].isnull()]
    train=feature_label[feature_label['sex'].notnull()]


    X_train, X_test, y_train, y_test = split_train(train, 0)



    print(X_train.shape, y_train.shape)
    input_dim = X_train.shape[1]

    model = Sequential()
    model.add(Dense(1200, input_shape=(input_dim,)))
    #model.add(Activation('sigmoid'))
    model.add(LeakyReLU(alpha=0.01))
    model.add(Dropout(dropout))


    model.add(Dense(100))
    model.add(LeakyReLU(alpha=0.01))
    model.add(BatchNormalization())
    model.add(Dropout(dropout))


    model.add(Dense(15, ))
    model.add(LeakyReLU(alpha=0.01))


    model.add(Dense(22, ))
    model.add(Activation('softmax'))

    # model.compile(optimizer="sgd", loss="mse")
    adam = Adam(lr=lr)
    model.compile(loss='categorical_crossentropy', optimizer=adam,
                    #metrics=['categorical_crossentropy'],
                  )
    print(model.summary())
    #model.compile(loss='binary_crossentropy', optimizer='adam', metrics=[categorical_accuracy])

    #'./model/'
    file_path = tmp_model

    check_best = ModelCheckpoint(filepath=replace_invalid_filename_char(file_path),
                                monitor='val_loss',verbose=1,
                                save_best_only=True, mode='min')

    early_stop = EarlyStopping(monitor='val_loss',verbose=1,
                               patience=300,
                               )

    history = model.fit(X_train, np_utils.to_categorical(y_train),
                        validation_data=(X_test, np_utils.to_categorical(y_test)),
                        callbacks=[check_best, early_stop],
                        batch_size=128,
                        #steps_per_epoch= len(X_test)//128,
                        epochs=5000,
                        verbose=1,
                        )

    return model, history, args


def get_feature_label_dnn():
    feature_label = get_stable_feature('0930')
    feature_label['sex_age'] = feature_label['sex_age'].astype('category')
    return feature_label


if __name__ == '__main__':
    for drop in [0.75,0.85, 0.7,] :
        for lr in [0.001, 0.0007, 0.0005]:

            _ , history, args = train_dnn(drop, lr)

            best_epoch = np.array(history.history['val_loss']).argmin()+1
            best_score = np.array(history.history['val_loss']).min()

            model = models.load_model(tmp_model)

            feature_label = get_feature_label_dnn()

            test = feature_label[feature_label['sex'].isnull()]
            train = feature_label[feature_label['sex'].notnull()]

            X_train, X_test, y_train, y_test = split_train(train)

            classifier = model

            pre_x = test.drop(['sex', 'age', 'sex_age', 'device'], axis=1)
            sub = pd.DataFrame(classifier.predict_proba(pre_x.values))

            sub.columns = test.sex_age.cat.categories
            sub['DeviceID'] = test['device'].values
            sub = sub[
                ['DeviceID', '1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8', '1-9', '1-10', '2-0', '2-1', '2-2',
                 '2-3', '2-4', '2-5', '2-6', '2-7', '2-8', '2-9', '2-10']]

            from sklearn.metrics import log_loss

            best = log_loss(y_test, classifier.predict_proba(X_test))

            logger.debug(f'Best:{best}, best_score:{best_score} @ epoch:{best_epoch}')

            model_file = f'./model/checkpoint/dnn_best_{best}_{args}_epoch_{best_epoch}.hdf5'
            model.save(model_file,
                       overwrite=True)

            print(
                f'=============Final train feature({len(feature_label.columns)}):\n{list(feature_label.columns)} \n {len(feature_label.columns)}')

            file = f'./sub/baseline_dnn_{best}_{args}_epoch_{best_epoch}.csv'
            file = replace_invalid_filename_char(file)
            logger.info(f'sub file save to {file}')
            sub = round(sub, 10)
            sub.to_csv(file, index=False)