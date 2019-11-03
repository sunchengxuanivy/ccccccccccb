import fasttext

import jieba
import jieba.analyse

# Get stopwords list
def get_stopwords_list(file_path):
    file_stop = open(file_path, 'r')
    vec_out_words = []
    for szLine in file_stop:
        vec_out_words.append(szLine.strip())
    file_stop.close()
    return vec_out_words

# Segmentation without stop words
def sentence_seg(sentence):
    tags = "" if sentence is None else "/".join(jieba.cut(sentence))
    #print(tags)
    stopwords = get_stopwords_list('./ExtraDict/StopWords_V1.txt')
    start = 0
    end = 0
    curr_posn = 0
    out_str = ''
    for char in tags:
        if char == '/':
            word = tags[start:curr_posn]
            if word not in stopwords:
                out_str += word
                out_str += " "
            start = curr_posn + 1
        curr_posn += 1
    return out_str

# generate the training file
# call once only
def GenerateTrainingFile():

    temp_vec = []

    with  open('./Model/TandC_Keys_train_update.txt', 'r', encoding='utf-8') as sourceFile, open('./Model/TandC_Keys_train_v2.txt', 'a+',
                                                                                  encoding='utf-8') as targetFile:
        for line in sourceFile:
            label = line[0:13]
            context = line[13:]
            TandC_vec = [label.strip(), context.strip()]
            temp_vec.append(TandC_vec)

        # print (temp_vec)

        temp_vec2 = temp_vec
        temp_vec3 = temp_vec

        for i in temp_vec:
            for j in temp_vec2:
                for k in temp_vec3:
                    if i[0].strip() != j[0].strip() and i[0].strip() != k[0].strip() and j[0].strip() != k[0].strip():
                        temp_sent = i[0].strip() + " " + j[0].strip() + " " + k[0].strip() + " " + i[1].strip() + " " + \
                                    j[1].strip() + " " + k[1].strip()
                        targetFile.write(temp_sent)
                        targetFile.write('\n')

        for i in temp_vec:
            for j in temp_vec2:
                if i[0].strip() != j[0].strip():
                    temp_sent = i[0].strip() + " " + j[0].strip() + " " + i[1].strip() + " " + j[1].strip()
                    targetFile.write(temp_sent)
                    targetFile.write('\n')

        for i in temp_vec:
            temp_sent = i[0].strip() + " " + i[1].strip()
            targetFile.write(temp_sent)
            targetFile.write('\n')

        print('done!')

    # train and save the model
    train_save_model()

def train_save_model():
    model_train = fasttext.train_supervised(input="./Model/entireT_C_split_v2.txt", epoch=50, lr=0.5,
                                            minn=2, maxn=3, dim=300,
                                            pretrained_vectors='./ExtraDict/wiki.zh_yue.vec', loss='ova')
    model_train.save_model("./Model/Train_Entire.bin")

# Predict T&C
def predict_TnC(model_train, sentence):
    try:
        out_label = model_train.predict(sentence, k=-1, threshold=0.2)
        str_label = " ".join(out_label[0])
        #print(str_label)
        out_str_simple = str(str_label) + ' ' + sentence + '\n'
        out_str = str(out_label) + ' ' + sentence + '\n'
    except:
        out_str_simple = str(r"\No label") + ' ' + sentence + '\n'
        out_str = str(r"\No label") + ' ' + sentence + '\n'
    return out_str_simple, out_str


if __name__ == '__main__':

    fInput = open('TranscriptOut/TranscriptList.txt', 'r')
    samples = []
    for szLine in fInput:
        samples.append(szLine.rstrip())
    fInput.close()

    # load user dictionary
    jieba.load_userdict('ExtraDict/LocalDict_V2.txt')

    # load custom IDF file, format $WORD $IDF_VALUE
    # Low IDF means occurrence in high freq.
    jieba.analyse.set_idf_path("ExtraDict/IDF_Out.txt")
    #jieba.analyse.set_idf_path("ExtraDict/IDF_big.txt") #default file

    # load custom stopwords file
    jieba.analyse.set_stop_words("ExtraDict/StopWords_V1.txt")

    # Execute once only
    #GenerateTrainingFile()
    #train_save_model()

    model_train = fasttext.load_model("./Model/Train_Entire.bin")

    # full sentence analysis

    for szFName in samples:
        fTrans = open('TranscriptOut/' + szFName, 'r')
        szFullSent = ''
        for szCont in fTrans:
            szCont = sentence_seg(szCont)  # remove stopwords
            szFullSent += ' ' + szCont


        print(szFullSent)

        # Extract Keywords
        tags = jieba.analyse.extract_tags(szFullSent, topK=150)
        print(tags)

        # Sentence Splitting
        folder = szFName.split('/')
        file_name = folder[0]
        if len(folder) >= 2:
            file_name = folder[1]

        # Output of sentence splitting
        fOutKey = open('./TranscriptOut/OutSentSplit_' + file_name , 'w')
        fOutLabel = open('./TranscriptOut/OutLabel_' + file_name, 'w')
        fOutLabelSimple = open('./TranscriptOut/OutLabelSimple_' + file_name, 'w')
        currT = 0
        prevT = 0
        item_tags = szFullSent.split(' ')
        for word in item_tags:
            # Use the top 1 keyword as the separator
            if word == tags[0]:
                # not included the term at currT
                sentence = "".join(item_tags[prevT:currT])
                print(sentence)
                fOutKey.write(sentence + '\n')  # output the segmented sentence

                # Output of labeling
                if len(sentence) > 2:
                    fOutLabel.write(sentence + '\n')

                    # using TF-IDF keywords to predict T&C
                    sent_keytags = jieba.analyse.extract_tags(sentence, topK=50)
                    sent_key = "" if sentence is None else " ".join(sent_keytags)
                    # label = model_train.predict(sent_key, k=-1, threshold=0.5)
                    out_simple, out_str = predict_TnC(model_train, sent_key)
                    fOutLabel.write(out_str)
                    fOutLabelSimple.write(out_simple)

                    sent_tags = "" if sentence is None else " ".join(jieba.cut(sentence))
                    out_simple, out_str = predict_TnC(model_train, sent_tags)
                    fOutLabel.write(out_str)
                    fOutLabel.write('\n')
                    fOutLabelSimple.write(out_simple)
                    fOutLabelSimple.write('\n')


                prevT = currT
            currT += 1

        # last sentence
        sentence = "".join(item_tags[prevT:currT])
        print(sentence)
        fOutKey.write(sentence + '\n')

        fOutLabel.close()
        fOutKey.close()
        fTrans.close()
