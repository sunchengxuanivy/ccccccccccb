import csv
import datetime
import io
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from google.cloud import speech_v1p1beta1 as speech
from google.cloud import bigquery, storage
from pydub import AudioSegment


def speech_to_text(content):
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
               '007615', '發送', '打開番', '備用', '睇一睇', '之前', '0.29厘', '6.75厘', '全期總利息', '還款額', '復核', '清楚', '委托', '借貸',
               '收取翻', '已經', '已經', '披露'
               ]
    speech_contexts_element = {"phrases": phrases, "boost": 20}
    audio = speech.types.RecognitionAudio(content=content)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        speech_contexts=[speech_contexts_element],
        audio_channel_count=1,
        enable_speaker_diarization=True,
        # enable_automatic_punctuation=True,
        max_alternatives=30,
        enable_word_time_offsets=True,
        diarization_speaker_count=1,
        enable_separate_recognition_per_channel=True,
        language_code='yue-Hant-HK'
    )
    stt_response = client.recognize(config, audio)

    return stt_response


def slice_cut(audio_path_str, frame_sec, overlap_sec):
    one_sec = 1000

    # long audio will be cut into several short frames. each frame holds 40s
    # there will be overlap between frames, overlap time is 3s
    # frame_sec = 40
    # overlap_sec = 3
    frame_msec = one_sec * frame_sec
    overlap_msec = one_sec * overlap_sec
    frame_non_overlap_msec = frame_msec - overlap_msec

    audio_path = Path(audio_path_str)
    dir = audio_path.parent
    stem = audio_path.stem

    audio_seg = AudioSegment.from_wav(audio_path_str)
    audio_len = len(audio_seg)
    frame_num = audio_len // frame_non_overlap_msec + 1
    last_frame_len = audio_len % frame_non_overlap_msec

    audio_slices = []
    for i in range(0, frame_num):
        start = i * frame_msec - i * overlap_msec
        if i != frame_num - 1:
            end = (i + 1) * frame_msec - i * overlap_msec
        else:
            end = start + last_frame_len
        audio_frame = audio_seg[start: end]
        file_path = dir / "{}_seg{}.wav".format(stem, i)
        file_path_str = str(file_path)
        audio_frame.export(file_path_str, format="wav")
        audio_slices.append(file_path_str)

    print("{} has been split into {} {}-sec slices, with {} sec overlap.".format(audio_path_str, frame_num, frame_sec,
                                                                                 overlap_sec))
    return audio_slices


def slow_down(org_path, stg1_path, stg2_path, slow_down_rate):
    org = str(org_path)
    stg1 = str(stg1_path)
    stg2 = str(stg2_path)
    stg1_cmd = ['sbsms', org, stg1, str(slow_down_rate), str(slow_down_rate), '0', '0']
    print(stg1_cmd)
    subprocess.check_call(stg1_cmd)
    stg2_cmd = ['sox', stg1, '-b', '16', '-e', 'signed-integer', stg2]
    print(stg2_cmd)
    subprocess.check_call(stg2_cmd)


def get_word_element(word):
    element = {}
    start_time_eletment = {"seconds": word.start_time.seconds, "nanos": word.start_time.nanos}
    end_time_eletment = {"seconds": word.end_time.seconds, "nanos": word.end_time.nanos}
    element["start_time"] = start_time_eletment
    element["end_time"] = end_time_eletment
    element["word"] = word.word
    element["speaker_tag"] = word.speaker_tag
    return element


def get_alternative_element(alternative):
    element = {"transcript": alternative.transcript, "confidence": alternative.confidence}
    word_elements = []

    for w in alternative.words:
        word = get_word_element(w)
        word_elements.append(word)
    element["words"] = word_elements
    return element


def get_result_element(result_data):
    alternative_elements = []
    element = {}
    for alternative in result_data.alternatives:
        alternative_element = get_alternative_element(alternative)
        alternative_elements.append(alternative_element)
    element["alternatives"] = alternative_elements
    element["channel_tag"] = result_data.channel_tag
    element["language_code"] = result_data.language_code
    return element


def get_response_element(response_data):
    element = {}
    result_elements = []
    for one_result in response_data.results:
        result_elements.append(get_result_element(one_result))
    element["results"] = result_elements
    return element


def insert_process_info(bucket, object_name, slice_num, slice_lenth_sec, slow_down_rate, overlap_sec):
    call_id = str(uuid.uuid4())
    query_format = """
    insert into
    `hsbc-9553155-ihubhk-dev.ccb_audio_process.ccb_call_process_info` 
    values (
        "{}", 
        "{}/{}", 
        {},
        {},
        {},
        {},
        current_timestamp()
    )
    """
    query = query_format.format(call_id, bucket, object_name, slice_num, slice_lenth_sec, slow_down_rate, overlap_sec)
    bigquery_client = bigquery.Client()
    job_config = bigquery.QueryJobConfig()
    job_config.use_legacy_sql = False
    load_job = bigquery_client.query(query=query, job_config=job_config)
    load_job.result()
    return call_id


def update_process_csv(file_name, callid, bucket, object_name, slice_num, slice_lenth_sec, slow_down_rate,
                       overlap_sec):
    with open(file_name, 'a', newline='', encoding='UTF-8') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(
            [callid,
             "{}/{}".format(bucket, object_name),
             slice_num,
             slice_lenth_sec,
             slow_down_rate,
             overlap_sec,
             str(datetime.datetime.now()),
             '1',
             None
             ])


def insert_response_info(parent_call_id, slice_id, response_data, channel_tag):
    query_format = """
    insert into
    `hsbc-9553155-ihubhk-dev.ccb_audio_process.ccb_call_response_info`
    values (
        '{}',
        '{}',
        '{}',
        '{}'
    )
    """
    query = query_format.format(parent_call_id, slice_id, response_data, channel_tag)
    bigquery_client = bigquery.Client()
    job_config = bigquery.QueryJobConfig()
    job_config.use_legacy_sql = False
    load_job = bigquery_client.query(query=query, job_config=job_config)
    load_job.result()


def update_response_csv(file_name, parent_call_id, slice_id, response_data, channel_tag):
    with open(file_name, 'a', newline='', encoding='UTF-8') as csvfile:
        spamwriter = csv.writer(csvfile)
        spamwriter.writerow(
            [parent_call_id,
             slice_id,
             response_data,
             channel_tag
             ])


def main_process(blob_name):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('/root/credential.json')

    ORG_AUDIO_BUCKET = 'ihubhk_ccb_audio_automate'

    SLOW_DOWN_RATE = 0.75
    SLICE_LENTH_SEC = 40
    OVERLAP_SEC = 3

    # blob_name = str(sys.argv[1])
    local_file_name = blob_name.split(sep='/')[-1]

    tmp_folder = Path('/tmp')

    csv_folder = Path('/root/csv')

    house_keep = []

    local_org_path = tmp_folder / local_file_name

    process_csv_path = (csv_folder / "process_{}".format(local_org_path.stem)).with_suffix('.csv')
    response_csv_path = (csv_folder / "response_{}".format(local_org_path.stem)).with_suffix('.csv')

    storage_client = storage.Client()
    org_audio_bucket = storage_client.get_bucket(ORG_AUDIO_BUCKET)

    # Start process audio files
    # download org audio file
    org_audio_bucket.blob(blob_name).download_to_filename(str(local_org_path))

    slices = slice_cut(str(local_org_path), SLICE_LENTH_SEC, OVERLAP_SEC)

    call_id = str(local_org_path.stem)
    update_process_csv(str(process_csv_path), call_id, ORG_AUDIO_BUCKET, blob_name, len(slices), SLICE_LENTH_SEC,
                       SLOW_DOWN_RATE,
                       OVERLAP_SEC)

    for index, aslice in enumerate(slices):
        slice_slow1_path = tmp_folder / 'slow1_{}'.format(Path(aslice).name)
        slice_slow2_path = tmp_folder / 'slow2_{}'.format(Path(aslice).name)
        slow_down(aslice, slice_slow1_path, slice_slow2_path, SLOW_DOWN_RATE)

        slow_down_audio = AudioSegment.from_wav(str(slice_slow2_path))

        for j, channel in enumerate(slow_down_audio.split_to_mono()):
            slice_slow2_channel_path = tmp_folder / 'slow2_c{}_{}'.format(j, Path(aslice).name)
            channel.export(str(slice_slow2_channel_path), format='wav')
            print('speech-to-text {}-channel {}'.format(slice_slow2_channel_path, j))
            with io.open(str(slice_slow2_channel_path), 'rb') as audio_file:
                content = audio_file.read()
            response = speech_to_text(content)
            update_response_csv(str(response_csv_path), call_id, index,
                                json.dumps(get_response_element(response), ensure_ascii=False), j)
            house_keep.append(str(slice_slow2_channel_path))

        house_keep.append(str(slice_slow1_path))
        house_keep.append(str(slice_slow2_path))

    house_keep.append(str(local_org_path))
    house_keep.extend(slices)
    for inter_file in house_keep:
        os.remove(inter_file)


def main_wrap_up(blob_name):
    error_folder = Path('/root/error')
    error_file = error_folder / blob_name.replace('/', '_')
    try:
        main_process(blob_name)
    except:
        os.mknod(str(error_file))


if __name__ == "__main__":
    blob = str(sys.argv[1])
    main_wrap_up(blob)
