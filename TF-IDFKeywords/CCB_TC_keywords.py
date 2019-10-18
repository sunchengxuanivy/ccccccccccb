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

os.environ[
    'GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ginnywong/documents/GCP_Project/hsbc-1044360-ihubasp-sandbox-8efb2949e323.json'

storage_client = storage.Client()
bucket = storage_client.get_bucket('ccb_audio_cantonese')
blob = bucket.blob(blob_name='model/model.bin')
blob.download_to_filename(filename='/tmp/model.bin')

model = fasttext.load_model("/tmp/model.bin")

project_id = "hsbc-1044360-ihubasp-sandbox"
topic_name = "hello_pubsub"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

jieba.suggest_freq('還款能力', True)
jieba.suggest_freq('月結單', True)

ALERT_TYPE = {
    0: "CORRECT",
    1: "MISSING_KEYWORD",
    2: "WRONG_KEYWORD",
    3: "SAID_NOTHING",
    4: "IRRELEVANT"
}

call_guides = [
    "另外 提示 一下 於 申請 貸款 前 先考 慮 清楚 財政狀況 及 還款能力",
    "你 證明 所 提供 嘅 資 料 係 正 確 及 完整 並授 權銀行 向 所有 有關 方面 查證 核實"]

rules = [["財政狀況", "還款能力"],
         []]

call_guides_vectors = []

for guide in call_guides:
    #     print("{}".format(sentence))
    w2v = model.get_sentence_vector(guide)
    call_guides_vectors.append(w2v)

"""
def send_email(msg, recipients):
    user = 'limitedpermissions@gmail.com'
    pw = 'Ivy5238317'
    smtpObj = smtplib.SMTP_SSL('smtp.googlemail.com', 465)
    smtpObj.ehlo()
    smtpObj.login(user, pw)
    smtpObj.sendmail(user, recipients, msg.as_string())
"""


def cosine_dist_comparison(sentence):
    # Compare with call guides and rate the best one
    cosine_results = []
    vector_sentence = model.get_sentence_vector(sentence)

    # For each of call guide to be compared with the input sentence
    for vector_call_guide in call_guides_vectors:
        cosine = scipy.spatial.distance.cosine(vector_sentence, vector_call_guide)
        cosine_results.append(round((1 - cosine) * 100, 2))

    index = np.where(cosine_results == np.amax(np.amax(cosine_results)))[0][0]
    return index, cosine_results[index]


def valid_biz_rule(sentence, key_word_list):
    """
    To validate business rule.
    there are multiple
    :param sentence: a string, the sentence to be validated.
    :param key_word_list: a string list, containing multiple key words.
    :return: int
        0 --> sentence is good, containing all key words.
        1 --> sentence contains no key words, [missing key word]
        2 --> sentence contains partial key words, [wrong key word]
        3 --> sentence is none.
        4 --> sentence is irrelevant.
    """
    # Simple regex to detect the existence of required keywords
    matched_no = 0
    for key_word in key_word_list:
        if re.search("^.*{}.*$".format(key_word), sentence):
            matched_no += 1
    if matched_no == len(key_word_list):
        return 0
    elif matched_no == 0:
        return 1
    else:
        return 2


# In[110]:


def process_biz_rules(sentence, index):
    # Select the highest matched section
    return valid_biz_rule(sentence, rules[index])


"""
def compose_email_message(sentence, validation_result, index, similarity):
    email_str_array = []
    if sentence == "":
        validation_result = 3
    elif similarity < 75:
        validation_result = 4
    email_subject_dict = {
        0: "call monitoring - correct",
        1: "call monitoring - missing key word",
        2: "call monitoring - wrong key word",
        3: "call monitoring - nothing said",
        4: "call monitoring - irrelevant"
    }

    cos_fit_dict = dict.fromkeys([0, 1, 2],
                                 "The input sentence's similarity to call guide section {} with {}%".format(index + 1,
                                                                                                            similarity))
    cos_fit_dict.update(dict.fromkeys([3, 4], ""))
    input_sentence = "You said: {}".format(sentence)

    validation_dict = {
        0: "The T&C section {} has been valided with presence of keywords {}".format(index + 1, rules[index]),
        1: "The T&C section {} has failed the business rules, no presence of keywords {}".format(index + 1,
                                                                                                 rules[index]),
        2: "The T&C section {} has failed the business rules, wrong matching keywords {}".format(index + 1,
                                                                                                 rules[index]),
        3: "You said nothing.",
        4: "It's irrelevant to any business rules."
    }

    email_str_array.append(cos_fit_dict.get(validation_result))
    email_str_array.append(input_sentence)
    email_str_array.append(validation_dict.get(validation_result))
    body = '\n\r'.join(email_str_array)

    msg = MIMEText(body, 'plain', 'utf-8')
    msg.set_charset('utf8')
    msg['Subject'] = email_subject_dict.get(validation_result)
    msg["Accept-Language"] = "zh-CN"
    msg["Accept-Charset"] = "ISO-8859-1,utf-8"
    return msg, validation_result
"""


def transcribe_gcs(gcs_uri):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""
    from google.cloud import speech_v1p1beta1 as speech
    client = speech.SpeechClient()

    # Hint Boost. This value increases the probability that a specific
    # phrase will be recognized over other similar sounding phrases.
    # The higher the boost, the higher the chance of false positive
    # recognition as well. Can accept wide range of positive values.
    # Most use cases are best served with values between 0 and 20.
    # Using a binary search happroach may help you find the optimal value.
    phrases = ['另外提示一下', '一下於申請貸款', '先考慮清楚', '財政狀況', '還款能力']
    boost = 20.0
    speech_contexts_element = {"phrases": phrases, "boost": boost}

    # with io.open(gcs_uri, 'rb') as audio_file:
    #   content = audio_file.read()

    audio = speech.types.RecognitionAudio(uri=gcs_uri)
    # audio = speech.types.RecognitionAudio(content=content)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        audio_channel_count=2,
        # speech_contexts=[speech_contexts_element],
        # enable_speaker_diarization=True,
        max_alternatives=30,
        enable_word_time_offsets=True,
        # diarization_speaker_count=1,
        enable_automatic_punctuation=False,
        # enable_separate_recognition_per_channel=True,
        model='command_and_search',
        language_code='yue-Hant-HK')

    response = client.long_running_recognize(config, audio)
    res = response.result(timeout=360)
    return res


def transcript_of_highest_conf(response):
    max_conf = 0
    max_trans = None
    for result in response.results:
        if result.alternatives[0].confidence >= max_conf:
            max_trans = result.alternatives[0].transcript
            max_conf = result.alternatives[0].confidence

    return max_trans


def bq_update(transcript, gcs_path, valid_result, tc_section):
    query_format = "insert into `hsbc-1044360-ihubasp-sandbox.ccb.audio_validation` values (\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",current_timestamp)"
    client = bigquery.Client(project_id)
    job_config = bigquery.QueryJobConfig()
    job_config.use_legacy_sql = False
    load_job = client.query(
        query=query_format.format(randrange(10), transcript, gcs_path, ALERT_TYPE.get(valid_result), tc_section),
        job_config=job_config)
    load_job.result()


def hello_gcs(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file_name = event['name']
    mon_bucket = event['bucket']
    object_path = 'gs://{}/{}'.format(mon_bucket, file_name)
    res = transcribe_gcs(object_path)
    best_trans = transcript_of_highest_conf(response=res)
    sentence = "" if best_trans is None else " ".join(jieba.cut(best_trans))

    index, similarity = cosine_dist_comparison(sentence)
    valid_result = process_biz_rules(sentence, index)
    email, valid_result = compose_email_message(sentence, valid_result, index, similarity)
    result = str(valid_result)
    future = publisher.publish(topic_path, data=result.encode('utf-8'))
    future.result(timeout=10)
    """
    send_email(email, ["ivy.c.x.sun@hsbc.com", "250268675@qq.com", "thomas.qian@hsbc.com.hk", "mary.chu@hsbc.com.hk",
                       "qianthomas@gmail.com", "mary.chu.mc@gmail.com", "ginnyyk.rs@gmail.com"])
    """

    bq_update(sentence, object_path, valid_result, index + 1)


if __name__ == '__main__':
    # res = transcribe_gcs('gs://ccb_ginny_nlp/TestAgentSound.wav')
    # for result in res.results:
    #    print('Transcript: {}'.format(result.alternatives[0].transcript))

    # best_trans = transcript_of_highest_conf(response=res)

    fInput = open('TranscriptOut/TranscriptList.txt', 'r')
    samples = []
    for szLine in fInput:
        samples.append(szLine.rstrip())
    fInput.close()

    # load user dictionary
    jieba.load_userdict('ExtraDict/LocalDict_V2.txt')
    # load custom IDF file, format $WORD $IDF_VALUE
    #print(jieba.analyse.default_tfidf.idf_freq)
    print(jieba.analyse.default_tfidf.median_idf)
    # Low IDF means occurrence in high freq.
    jieba.analyse.set_idf_path("ExtraDict/IDF_Out.txt")
    #jieba.analyse.set_idf_path("ExtraDict/IDF_big.txt")
    print(jieba.analyse.default_tfidf.median_idf)
    # load custom stopwords file
    jieba.analyse.set_stop_words("ExtraDict/StopWords_V1.txt")

    szFullSent = ''
    for szFName in samples:
        fTrans = open('TranscriptOut/' + szFName, 'r');
        for szCont in fTrans:
            szTags = "" if szCont is None else " ".join(jieba.cut(szCont))
            szFullSent += ' ' + szTags
        fTrans.close()

    print(szFullSent)
    tags = jieba.analyse.extract_tags(szFullSent, topK=100, withWeight=True)

    fOutKey = open('TranscriptOut/OutKeyWords.txt', 'w')
    for item in tags:
        fOutKey.write(item[0] + ',' + str(item[1]) + '\n')
        print(item[0] + ',' + str(item[1]))

    fOutKey.close()

    #idf = jieba.analyse.TFIDF()
    #print(idf)
    #print(",".join(tags))

#    index, similarity = cosine_dist_comparison(sentence)
#    valid_result = process_biz_rules(sentence, index)
#    email, result = compose_email_message(sentence, valid_result, index, similarity)
#    print(email.as_string().encode('UTF-8'))
#    send_email(email, ["ivy.c.x.sun@hsbc.com", "250268675@qq.com"])

