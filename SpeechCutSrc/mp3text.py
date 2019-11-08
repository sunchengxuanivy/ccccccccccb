import io
import os
from pathlib import Path
from google.cloud import speech_v1p1beta1 as speech
from sentence import Sentence
from pydub import AudioSegment
from SilenceCut import slice_cut_silence

os.environ[
    'GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/ginnywong/documents/GCP_Project/hsbc-1044360-ihubasp-sandbox-8efb2949e323.json'

#def transcribe_gcs(gcs_uri):
def transcribe_gcs(audio_path):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""

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
               '收取翻', '已經', '已經', '披露']

    speech_contexts_element = {"phrases": phrases, "boost": 20}

    with io.open(audio_path, 'rb') as audio_file:
        content = audio_file.read()

    # Loads the audio into memory
    audio = speech.types.RecognitionAudio(content=content)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        speech_contexts=[speech_contexts_element],
        audio_channel_count=1,
        enable_speaker_diarization=True,
        max_alternatives=30,
        enable_word_time_offsets=True,
        diarization_speaker_count=1,
        enable_separate_recognition_per_channel=True,
        language_code='yue-Hant-HK')

    response = client.recognize(config, audio)

    print('Waiting for operation to complete...')
    #response = response.result(timeout=360)

    # The transcript within each result is separate and sequential per result.
    # However, the words list within an alternative includes all the words
    # from all the results thus far. Thus, to get all the words with speaker
    # tags, you only have to take the words list from the last result:

    return response

def slice_cut(audio_path_str):
    one_sec = 1000

    # long audio will be cut into several short frames. each frame holds 40s
    # there will be overlap between frames, overlap time is 3s
    frame_sec = 50
    overlap_sec = 3
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
        if len(audio_frame.split_to_mono()) > 1:
            audio_frame.split_to_mono()[1].export(file_path_str, format="wav")
        else:
            audio_frame.export(file_path_str, format="wav")
        audio_slices.append(file_path_str)

        # print(response.results[0].alternatives[0].transcript)
    print("{} has been split into {} {}-sec slices, with {} sec overlap.".format(audio_path_str, frame_num, frame_sec,
                                                                                 overlap_sec))
    return audio_slices



if __name__=="__main__":
    audio_path = Path('../audio/1040_2_slow.wav')
    #print(audio_path.absolute())
    #slices = slice_cut(str(audio_path.absolute()))
    silence_slices = slice_cut_silence(audio_path)

    out_str = ''
    for i, asilence_slice in enumerate(silence_slices):
        print(asilence_slice)
        silence_audio = AudioSegment.from_wav(asilence_slice)
        if len(silence_audio) > 50000:
            small_slices = slice_cut(asilence_slice)
            for asmall_slice in small_slices:
                print(asmall_slice)
                res = transcribe_gcs(asmall_slice)
                for result in res.results:
                    out_str += result.alternatives[0].transcript
            out_str += '\n'
        else:
            res = transcribe_gcs(asilence_slice)
            for result in res.results:
                out_str += result.alternatives[0].transcript
            out_str += '\n'

    transcript_dir = Path('response_example').absolute()
    transcript_path = transcript_dir / '{}.txt'.format(audio_path.stem)

    with open(str(transcript_path), 'w+') as file:
        file.write(out_str)

    print(out_str)



