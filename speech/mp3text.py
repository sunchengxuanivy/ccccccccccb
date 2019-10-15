from speech.sentence import Sentence


def transcribe_gcs(gcs_uri):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""
    from google.cloud import speech_v1p1beta1 as speech
    client = speech.SpeechClient()

    phrases = ['登記', '手提電話',
               '而家', '短訊', '發送', '重要', '資訊', '號碼', '最後六個數字', '007615', '收到', '打開', '超鏈接', '撳返', '接受', '方便', '上網',
               '講番', '條款',
               '用途', '一啲', '同時',
               '申請', '貸款', '考慮', '財政', '狀況', '還款', '能力',
               '分期萬應錢', '銀碼', '每月供款額', '月平息', '總利息', '全期', '實際', '年率', '年利率', '五毫', '四毫', '七厘', '五厘', '六厘', '還款', '金額',
               '參考', '尾數', '申請', '一經', '批核', '加額', '優惠', '失效', '月息', '文件',
               '存入', '指定', '戶口', '唔會', '通知', '確認信', '列明', '貸款額', '第一期', '日期',
               '委託', '第三方', '轉介', '利益', '安排', '並非', '私隱', '保安',
               '償還', '收取', '章則', '第五條', '繳付', '金額', '餘額', '本金', '結欠', '兩個percent', '逾期', '還款', '2.25厘', '九厘', '未還',
               '利息',
               '對內',
               '對外', '審批',
               '推廣']
    speech_contexts_element = {"phrases": phrases, "boost": 20}
    audio = speech.types.RecognitionAudio(uri=gcs_uri)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        speech_contexts=[speech_contexts_element],
        audio_channel_count=2,
        enable_speaker_diarization=True,
        max_alternatives=30,
        enable_word_time_offsets=True,
        diarization_speaker_count=1,
        enable_separate_recognition_per_channel=True,
        language_code='yue-Hant-HK')

    response = client.long_running_recognize(config, audio)

    print('Waiting for operation to complete...')
    response = response.result(timeout=360)

    # The transcript within each result is separate and sequential per result.
    # However, the words list within an alternative includes all the words
    # from all the results thus far. Thus, to get all the words with speaker
    # tags, you only have to take the words list from the last result:

    return response


res = transcribe_gcs("gs://dataproc-daba3d54-fdea-4936-a9c1-c45661e21ef8-europe-west2/1003_3.wav")

result = res.results[-1]
words_info = result.alternatives[0].words
print(result.channel_tag)
# Printing out the output:
for word_info in words_info:
    time_full = (word_info.start_time.seconds * 1000000000 + word_info.start_time.nanos) * 3 / 4
    word_info.start_time.seconds = int(time_full / 1000000000)
    word_info.start_time.nanos = int(time_full - word_info.start_time.seconds * 1000000000)
    time_full = (word_info.end_time.seconds * 1000000000 + word_info.end_time.nanos) * 3 / 4
    word_info.end_time.seconds = int(time_full / 1000000000)
    word_info.end_time.nanos = int(time_full - word_info.end_time.seconds * 1000000000)
    # print("{}\t{}\t '{}'".format(
    #     (word_info.start_time.seconds * 1000000000 + word_info.start_time.nanos) * 3 / 4 / 1000000000,
    #     (word_info.end_time.seconds * 1000000000 + word_info.end_time.nanos) * 3 / 4 / 1000000000,
    #     word_info.word))


def result_to_sentences(words):
    sentences = []
    sentence = Sentence()
    sentence.channel_tag = result.channel_tag
    sentence.start_time = result.alternatives[0].words[0].start_time.seconds
    for w in words:
        start = w.start_time.nanos / 1000000000 + w.start_time.seconds
        end = w.end_time.nanos / 1000000000 + w.end_time.seconds
        if len(sentence.words) == 0:
            sentence.start_time = end
        if (end - start) > 1:
            # start new sentence
            sentence.end_time = start
            if sentence.words != "":
                sentences.append(sentence)
            sentence = Sentence()
            sentence.channel_tag = result.channel_tag
            sentence.start_time = end
        sentence.words = sentence.words + w.word

    return sentences


sentences = result_to_sentences(words_info)

for sentence in sentences:
    print("{}\t{}\t{}".format(sentence.start_time, sentence.end_time, sentence.words))
