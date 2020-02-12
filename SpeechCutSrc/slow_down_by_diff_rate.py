import os
import subprocess
from pathlib import Path
from SilenceCut import slice_cut_silence
from pydub import AudioSegment

dir_path = Path('/Users/sun/Documents')

ten_calls = [
    # '9135763951750002401_agent.wav',
    # '9135764269440002401_agent.wav',
    '9136038592380002401_agent.wav',
    # '9136136315500002401_agent.wav',
    # '9135763881250003261_agent.wav',
    # '9136230、002390003261_agent.wav',
    # '9135764046400002401_agent.wav',
    # '9136508829910003261_agent.wav',
    # '9135763575330002401_agent.wav',
    # '913577141、3180003261_agent.wav'
]
slow_down_rate = [
    1.0, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6
]
for call in ten_calls:
    call_path = dir_path / call

    slices = slice_cut_silence(call_path)
    for i, sli in enumerate(slices):
        for rate in slow_down_rate:
            sli_path = Path(sli)
            stg1_path = dir_path / '{}_tmp_{}.wav'.format(rate, sli_path.stem)
            stg2_path = dir_path / '{}_tmp_2_{}.wav'.format(rate, sli_path.stem)
            slow_path = dir_path / '{}_{}.wav'.format(rate, sli_path.stem)
            stg1_cmd = ['sbsms', sli, str(stg1_path), str(rate), str(rate), '0', '0']
            subprocess.check_call(stg1_cmd)
            stg2_cmd = ['sox', str(stg1_path), '-b', '16', '-e', 'signed-integer', str(stg2_path)]
            subprocess.check_call(stg2_cmd)
            wave_file = AudioSegment.from_file(str(stg2_path))
            cut_len = int(400 * (1 / rate - 1))
            final_wave = wave_file[cut_len:]
            final_wave.export(out_f=str(slow_path), format='wav')
            os.remove(str(stg1_path))
            os.remove(str(stg2_path))
