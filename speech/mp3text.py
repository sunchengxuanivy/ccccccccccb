import os
import sys
from pathlib import Path
import subprocess

from google.cloud import storage


class Sentence:
    words = ""
    start_time = None
    end_time = None
    channel_tag = None


def transcribe_gcs(gcs_uri):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""
    from google.cloud import speech_v1p1beta1 as speech
    client = speech.SpeechClient()

    phrases = ['評估', '保安', '申請', '指定', '加額', '失效', '法律', '索取', '管轄', '機構', '參考', '本金', '委託', '資料', '個人', '宜家', '睇過',
               '撳番', '剔返', '銀碼', '哩次', '客戶', '未能', '修改', '兩個percent', '第三者', '用途', '條文', '批核', '合約', '享有', '不限', '今日',
               '根據', '左下角', '唔會', '貸款', '列明', '內容', '銀行', '有關', '文件', '前七日', '款項', '超連結', '分期萬應錢', '回覆', '限期', '提供',
               '私隠', '一個', '推廣', '同事', '財政', '取消', '不獲', '存入', '優惠', '拖欠', '修訂', '第五條', '包括', '還款', '破產', '沒有', '七個',
               '償還', '四百', '利益', '查詢', '未還', '扣除', '審批', '生效', '收到', '繳付', '清還', '複查', '細則', '新優惠', '推廣期', '月平息', '第一期',
               '決定權', '查閱', '順利', '借款', '再提取', '到期日', '確認信', '有利益', '正確', '對內', '香港特別行政區', '監管', '第三方', '再聯絡', '曾經',
               '通知', '狀況', '信函', '以上', '利息', '產品', '完成', '作出', '退回', '打翻', '短信', '詮釋', '隨時', '方面', '章則', '成功', '強制',
               '信貸', '條款', '短訊', '年利率', '同意', '工作天', '手續費', '信用額', '通過', '逾期', '明白', '補交', '能力', '接受', '同時', '取代', '每月',
               '較先', '核實', '詳細', '確認', '餘額', '授權', '提醒', '結欠', '爭議', '格仔', '2.25厘', '下載', '轉介', '變動', '執行', '受僱', '服務',
               '任何', '債務', '權利', '日後', '月息', '保留', '否則', '再次', '條例', '網頁', '尾數', '日期', '總利息', '熱線', '規定', '並無', '遞交',
               '供款額', '披露', '使用', '最終', '額外', '考慮', '貸款額', '除咗', '按期', '第八條', '私人', '提早', '戶口', '跟進', '閱讀', '金額', '至少',
               '實際', '滙豐', '有權', '約束', '資訊', '對外', '完整', '查證', '安排', '正在', '收取', '證明', '並非', '一啲', '上網', '全期', '請問',
               '007615'
               ]
    speech_contexts_element = {"phrases": phrases, "boost": 20}
    audio = speech.types.RecognitionAudio(uri=gcs_uri)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        speech_contexts=[speech_contexts_element],
        audio_channel_count=2,
        enable_speaker_diarization=True,
        enable_automatic_punctuation=True,
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


def result_to_sentences(words):
    sentences = []
    sentence = Sentence()
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
            sentence.start_time = end
        sentence.words = sentence.words + w.word

    return sentences


def slow_down(org_path, stg1_path, stg2_path):
    org = str(org_path)
    stg1 = str(stg1_path)
    stg2 = str(stg2_path)
    stg1_cmd = ['sbsms', org, stg1, '0.75', '0.75', '0', '0']
    print(stg1_cmd)
    subprocess.check_call(stg1_cmd)
    stg2_cmd = ['sox', stg1, '-b', '16', '-e', 'signed-integer', stg2]
    print(stg2_cmd)
    subprocess.check_call(stg2_cmd)


# def main(request):
if __name__ == "__main__":

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('/root/credential.json')

    ORG_AUDIO_BUCKET = 'ccb_audio_automate'
    SLOW_AUDIO_BUCKET = 'ccb_audio_slow'
    TRANSCRIPT_BUCKET = 'ccb_audio_transcript'

    blob_name = sys.argv[1]
    local_file_name = blob_name.replace('/', '_')

    tmp_folder = Path('/tmp')

    local_org_path = tmp_folder / local_file_name

    local_slow1_path = tmp_folder / 'slow1_{}'.format(local_file_name)
    local_slow2_path = tmp_folder / 'slow2_{}'.format(local_file_name)
    local_transcript_path = (tmp_folder / local_org_path.stem).with_suffix('.txt')

    storage_client = storage.Client()
    org_audio_bucket = storage_client.get_bucket(ORG_AUDIO_BUCKET)
    slow_audio_bucket = storage_client.get_bucket(SLOW_AUDIO_BUCKET)
    transcript_bucket = storage_client.get_bucket(TRANSCRIPT_BUCKET)

    # Start process audio files
    # download org audio file
    org_audio_bucket.blob(blob_name).download_to_filename(str(local_org_path))

    # slow down speech speed. local_slow2_path is the output.
    slow_down(local_org_path, local_slow1_path, local_slow2_path)

    # upload the slowed-down audio.
    slowed_blob = slow_audio_bucket.blob(local_slow2_path.name)
    slowed_blob.upload_from_filename(str(local_slow2_path))

    # speech-to-text API
    res = transcribe_gcs("gs://{}/{}".format(slow_audio_bucket.name, slowed_blob.name))

    result = res.results[-1]
    words_info = result.alternatives[0].words
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

    sentences = result_to_sentences(words_info)

    with open(local_transcript_path, 'w+') as file:
        for sentence in sentences:
            file.write("{}\t{}\t{}".format(sentence.start_time, sentence.end_time, sentence.words))
            file.write('\n')

    transcript_bucket.blob(local_transcript_path.name).upload_from_filename(str(local_transcript_path))

    os.remove(local_org_path)
    os.remove(local_slow1_path)
    os.remove(local_slow2_path)
    os.remove(local_transcript_path)
