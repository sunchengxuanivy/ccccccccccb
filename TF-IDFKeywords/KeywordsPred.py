import os
import io

from email.mime.text import MIMEText

from google.cloud import pubsub_v1, bigquery
import fasttext
import scipy.spatial.distance
import numpy as np
import re
import smtplib
import jieba
import jieba.analyse

from google.cloud import storage
from random import randrange

if __name__ == '__main__':

    fInput = open('TranscriptOut/TranscriptList.txt', 'r')
    samples = []
    for szLine in fInput:
        samples.append(szLine.rstrip())
    fInput.close()

    # load user dictionary
    jieba.load_userdict('ExtraDict/LocalDict_V2.txt')
    # load custom IDF file, format $WORD $IDF_VALUE
    # print(jieba.analyse.default_tfidf.idf_freq)
    print(jieba.analyse.default_tfidf.median_idf)
    # Low IDF means occurrence in high freq.
    jieba.analyse.set_idf_path("ExtraDict/IDF_Out.txt")
    #jieba.analyse.set_idf_path("ExtraDict/IDF_big.txt") #default file
    print(jieba.analyse.default_tfidf.median_idf)
    # load custom stopwords file
    jieba.analyse.set_stop_words("ExtraDict/StopWords_V1.txt")

    model_train = fasttext.train_supervised(input="Model/TandC_Keys_train.txt", epoch=50, lr=0.5,
                                            minn=2, maxn=3, dim=300,
                                            pretrained_vectors='ExtraDict/wiki.zh_yue.vec')

    # full sentence analysis
    szFullSent = ''
    for szFName in samples:
        fTrans = open('TranscriptOut/' + szFName, 'r');
        for szCont in fTrans:
            szTags = "" if szCont is None else " ".join(jieba.cut(szCont))
            szFullSent += ' ' + szTags
        fTrans.close()

    print(szFullSent)
    tags = jieba.analyse.extract_tags(szFullSent, topK=150, withWeight=True)

    fOutKey = open('TranscriptOut/OutKeyWords.txt', 'w')
    count = 0
    for item in tags:
        fOutKey.write(item[0] + ',' + str(item[1]) + '\n')
        print(item[0] + ',' + str(item[1]))
        count += 1
        if count % 50 == 0:
            print('count: ' + str(count))

    fOutKey.close()

    print('count: ' + str(count))

# keywords analysis
for szFName in samples:
    fTrans = open('TranscriptOut/' + szFName, 'r');
    for szCont in fTrans:
        szTags = "" if szCont is None else " ".join(jieba.cut(szCont))
        print(szTags)
        sent_tags = jieba.analyse.extract_tags(szTags, topK=20)
        print(sent_tags)
        sent_keys = ''
        for item in sent_tags:
            sent_keys += item + ' '
        print("Label: ", model_train.predict(sent_keys))
    fTrans.close()
