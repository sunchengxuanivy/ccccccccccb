import io
import os
import subprocess
from threading import Thread

import xlsxwriter
from pydub import AudioSegment

from pathlib import Path

from google.cloud import speech_v1p1beta1 as speech
from audio2bigquery import get_response_element
from google.cloud import storage


def stt_blobs(blob_list, thread_no):
    workbook_path = dir_path / '2nd_round_result_{}.xlsx'.format(thread_no)
    workbook = xlsxwriter.Workbook(str(workbook_path))
    worksheet = workbook.add_worksheet()
    worksheet.write('A1', 'CALL_ID')
    worksheet.write('B1', 'AGENT_SEQ')
    worksheet.write('C1', 'TIME_MS')
    worksheet.write('D1', 'SLOW_DOWN_RATE')
    worksheet.write('E1', 'QUALITY')
    worksheet.write('F1', 'RESULT_TRANSCRIPT')
    worksheet.write('G1', 'CORRECT_TRANSCRIPT')
    excel_line = 2
    for blob in blob_list:
        blob_name = blob.name
        blob_name_stem = blob_name.replace('audios_2nd/', '').replace('.wav', '')
        name_seg = blob_name_stem.split('_')
        if len(name_seg) == 3:
            response = speech_to_text('gs://dataproc-init-ivy/{}'.format(blob_name), 8000)
            quality = False
            slow_down_rate = 1
            call_id = name_seg[0]
        else:
            response = speech_to_text('gs://dataproc-init-ivy/{}'.format(blob_name), 44100)
            slow_down_rate = name_seg[0]
            quality = True
            call_id = name_seg[1]
        file_name = '/Users/sun/Documents/{}'.format(blob_name)
        blob.download_to_filename(file_name)
        audio = AudioSegment.from_file(file_name)
        agent_seq = name_seg[-1].replace('silence', '')
        response_json = get_response_element(response)
        words = get_all_words(response_json)
        worksheet.write('A{}'.format(excel_line), call_id)
        worksheet.write('B{}'.format(excel_line), agent_seq)
        worksheet.write('C{}'.format(excel_line), len(audio))
        worksheet.write('D{}'.format(excel_line), slow_down_rate)
        worksheet.write('E{}'.format(excel_line), quality)
        worksheet.write('F{}'.format(excel_line), words)
        # worksheet.write('G{}'.format(excel_line), 'CORRECT_TRANSCRIPT')
        excel_line = excel_line + 1
    workbook.close()


def get_all_words(response):
    all_words = ""
    if len(response.get("results")) == 0:
        return all_words
    for w in response.get("results")[0].get("alternatives")[0].get("words"):
        all_words += w.get("word")
    return all_words


def speech_to_text(uri, sample_rate_hertz):
    client = speech.SpeechClient()
    phrases = [
        '007615', '一個工作天', '七個工作天', '上網', '下載', '不獲批核', '並無', '並非', '享有', '任何', '保安', '保留', '信用額', '信貸複查', '信貸資料', '修改',
        '修訂', '個人資料', '個人資料私隱條例', '借款', '債務', '償還', '兩個percent', '再提取', '再聯絡', '分期萬應錢', '列明', '利息', '利益', '到期日', '前七日',
        '匯豐', '參考', '取代', '取消', '受僱', '合約', '合適', '同意', '同時生效', '四百', '回覆', '存入', '安排', '完整', '實際年利率', '實際還款', '對內',
        '對外', '左下角', '強制執行', '成功', '成功批核', '戶口', '手提電話', '手續費', '扣除', '批核', '披露', '拖欠', '指定', '按期償還', '授權', '接受',
        '推廣優惠', '推廣期', '推廣條款', '推廣條款細則', '提供', '提早償還', '提醒', '撳番', '新優惠', '明白同意', '曾經', '最後六個數字', '最終決定權', '月平息', '月息',
        '有利益安排', '有權', '有關客戶', '有關方面', '服務機構', '未能', '本金', '查證', '查閱', '核實', '根據', '條文', '條款', '條款文件', '機構', '權利', '款項',
        '正確', '每月供款額', '每月還款', '每月限期前', '沒有委託', '法律', '清楚明白', '清還', '爭議', '產品資料', '用途', '申請', '發送', '發送號碼', '監管', '短訊',
        '破產', '確認', '確認信', '私人貸款', '私隱', '章則條款', '第一期', '第三方', '第三者權利', '第五條', '第八條', '管轄', '約束', '索取', '細則', '結欠',
        '網頁', '總利息', '繳付', '考慮', '補交', '規定', '詮釋', '詳細內容', '證明', '財政狀況', '貸款', '貸款用途', '貸款額', '資料', '超連結', '跟進', '較先',
        '轉介', '退回', '通知', '逾期未還', '逾期還款', '還款到期日', '還款戶口', '還款日期', '還款能力', '重要資訊', '銀碼', '閱讀', '順利批核', '額外文件', '餘額',
        '香港特別行政區', '滙豐主網頁', '已償還', '提早償還', '清楚列明', '同埋披露你', '申請信貸', '你確認', '同埋詮釋', '蚊預期', '全數貸款', '委托任何', '存入還款戶口',
        '對内對外信貸資料', '授權銀行', '本金結欠', '委托第三方', '申請貸款', '貸款用途', '請問', '打開番', '而家', '重要條款', '我哋', '方唔方便',
        '方便', '收到', '重要', '資訊', '之後', '之前', '接受掣', '睇完', '睇番', '手提電話號碼', '打開個', '撳番個', '留意', '唔明白', '聲明', '隨時', '問番',
        '條款聲明', '有唔明', '可以',
        '想問番', '於申請', '要申請', '財政', '狀況', '金額', '實際', '1厘', '2厘', '3厘', '4厘', '5厘', '6厘', '7厘', '8厘', '9厘', '全期總利息',
        '全期', '畀番你', '變動', '落數',
        '聯絡', '聯絡返', '假如', '復核', '一經', '直接', '假設', '還款', '並沒有', '委託', '哩次申請', '推廣', '關於', '參考返', '信貸', 'link', '你已經',
        '撳開', '有條', '控權人', 'load埋',
        '還款額', 'OK', '逾期', '現金', '回贈', '償還日期', '每一個月', '可以享受番', '銀行方面', '收取', '本金餘額', '做番', '利息方面', '邊方面', '抵押', '冇抵押',
        '特別', '清楚財政',
        '一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月', '同時', '經短訊', '發咗'
    ]
    speech_contexts_element = {"phrases": phrases, "boost": 20}
    audio = speech.types.RecognitionAudio(uri=uri)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate_hertz,
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
    stt_response = client.long_running_recognize(config, audio)
    response = stt_response.result(timeout=360)

    return response


dir_path = Path('/Users/sun/Documents')
ten_calls = [
    '9135763951750002401_agent.wav',
    '9135764269440002401_agent.wav',
    '9136038592380002401_agent.wav',
    '9136136315500002401_agent.wav',
    '9135763881250003261_agent.wav',
    '9136230002390003261_agent.wav',
    '9135764046400002401_agent.wav',
    '9136508829910003261_agent.wav',
    '9135763575330002401_agent.wav',
    '9135771413180003261_agent.wav'
]
slow_down_rate = [
    1.0, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6
]

storage_client = storage.Client()
bucket = storage_client.bucket('dataproc-init-ivy')
blobs = bucket.list_blobs(prefix='audios_2nd/')
blob_list = list(blobs)[1:]
thread_list = []
thread_len = 10
for i in range(thread_len):
    thread_list.append(Thread(target=stt_blobs, args=(blob_list[i::thread_len], i)))

for i in range(thread_len):
    thread_list[i].start()

for i in range(thread_len):
    thread_list[i].join()

# stt_blobs(blob_list, 0)
# print(blob_list[-1].name)


# audio = AudioSegment.from_wav(sli)
# file_con = None
# with io.open(sli, 'rb') as audio_file:
#     file_con = audio_file.read()
# response = speech_to_text(file_con, 8000)
# response_json = get_response_element(response)
# words = get_all_words(response_json)
# print('{}\t{}'.format(i, words))
# worksheet.write('A{}'.format(excel_line), call.replace('_agent.wav', ''))
# worksheet.write('B{}'.format(excel_line), i)
# worksheet.write('C{}'.format(excel_line), len(audio))
# worksheet.write('D{}'.format(excel_line), 1)
# worksheet.write('E{}'.format(excel_line), False)
# worksheet.write('F{}'.format(excel_line), words)
# worksheet.write('G{}'.format(excel_line), 'CORRECT_TRANSCRIPT')
# excel_line = excel_line + 1
