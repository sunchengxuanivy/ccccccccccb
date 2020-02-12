"""
    This module stores functions writen to facilitate comparing transcripts.
"""
import pandas as pd
import difflib as diff
import os
import re

# the Differ function. After comparing string A and B, yield 3 types of output.
# -char: belongs to A - B
# +char: belongto B - A
# char: belong to A intersection B
d = diff.Differ()


# Orginize the output of Differ function, and give output in tuples.
# Each output tuple has only 1 nonempty entry, with 1 char
def easy_compare(df):
    result = list(d.compare(spliteKeyWord(df.TTS), spliteKeyWord(df.CORRECT)))
    fff = []
    for eachar in result:
        if '+' in eachar:
            fff.append([eachar[2:], '', ''])
        elif '-' in eachar:
            fff.append(['', eachar[2:], ''])
        else:
            fff.append(["", "", eachar[2:]])
    return fff


# String to list such that English word, percent, and numbers, 2.25, will be counted as 1 entry instead of multiple entries by character.
def spliteKeyWord(sent):
    regex = r"[\u4e00-\ufaff]|[0-9]+\.[0-9]+|[0-9]+|[a-zA-Z]+\'*[a-z]*"
    matches = re.findall(regex, sent, re.UNICODE)
    return matches


# Given a datafram course_df, Compare the transcripts stored in col1 to the other transcripts stored in col2
# missing_count: count of words transcribed in Col2 that was not included in Col1
# match_count: count of words corrected transcribed in both Col1 and Col 2
# added_count: count of words transcribed in Col1 but was not included in Col2
def HitIt(col1, col2, source_df):
    compare_df_1 = source_df.iloc[:, [col1, col2]]
    compare_df_1.columns = ['TTS', 'CORRECT']
    compare_df_1['TTS'] = compare_df_1.TTS.astype(str)
    compare_df_1['CORRECT'] = compare_df_1.CORRECT.astype(str)
    result = compare_df_1.apply(easy_compare, axis=1)
    result = pd.DataFrame(result.sum())
    result.columns = ['Missing_From_Correct', 'Added_By_TTS', 'Match']
    Missing_From_Correct = result.Missing_From_Correct.str.cat(sep="")
    Added_By_TTS = result.Added_By_TTS.str.cat(sep='')
    Match = result.Match.str.cat(sep='')
    missing_count = len(spliteKeyWord(Missing_From_Correct))
    match_count = len(spliteKeyWord(Match))
    added_count = len(spliteKeyWord(Added_By_TTS))
    return missing_count, match_count, added_count, result


# Generate a list of files inside root_folder with given file_type
def Get_File_Path(root_folder, file_type):
    file_list = []
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith(file_type):
                file_list.append(os.path.join(root, file))
    return file_list


Alternative_Words_Dict = {'返': ['番', '翻'], '滙': ['匯'], '隱': ['隠']}


def Alternative_Words(sent, dictionary=Alternative_Words_Dict):
    for k, (key, value) in enumerate(dictionary.items()):
        for item in value:
            sent = sent.replace(item, key)
    return sent


"""
    Generate a list of keyword, regardless and/or, for a given T&C label
"""


def str_to_list(sentence):
    r = re.compile(r'[() ]')
    temp = r.sub("", sentence)
    temp = temp.replace('or', 'and').split('and')
    return temp


"""
    Generate a dict of keywords synonyms
"""


def synonyms_dict(df):
    sentence = str(df['Alternatvie'])
    key = df['FinalizedKeywordsList'][0]
    alt = sentence.split(',')
    for item in alt:
        temp = re.sub(r'[\s]', "", item)
        n = temp.find('=')
        if n != -1:
            temp = temp.replace('or', '=')
            content = temp[n + 1:].split('=')
            Dict_TandC_Syn[temp[:n]] = content
        else:
            Dict_TandC_Syn[key] = temp.split('or')


"""
    Return the number of appearance of the key in a given sentence, including appearance of synonyms of the key
"""


def check_keyword(sentence, key):
    n = sentence.count(key)
    if key in Dict_TandC_Syn.keys():
        for item in Dict_TandC_Syn[key]:
            n += sentence.count(item)
    return n


def get_stopwords_list(file_path):
    file_stop = open(file_path, 'r')
    vec_out_words = []
    for szLine in file_stop:
        vec_out_words.append(szLine.strip())
    file_stop.close()
    return vec_out_words


def remove_stopwords(sentence):
    tags = "" if sentence is None else "/".join(jieba.cut(str(sentence)))
    # print(tags)
    stopwords = get_stopwords_list('StopWords_V1_Isa.txt')
    start = 0
    end = 0
    curr_posn = 0
    out_str = ''
    for char in tags:
        if char == '/' or (curr_posn + 1) >= len(tags):
            if (curr_posn + 1) >= len(tags):
                word = tags[start:]
            else:
                word = tags[start:curr_posn]
            if word not in stopwords:
                out_str += word
                # out_str += " "
            start = curr_posn + 1
        curr_posn += 1
    return out_str
