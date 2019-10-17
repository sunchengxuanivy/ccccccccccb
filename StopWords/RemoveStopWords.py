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
    print(tags)
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

inputs = open('./TranscriptOut/AGENT_Slow.txt', 'r')
for line in inputs:
    line_seg = sentence_seg(line)
    print(line_seg)
inputs.close()
