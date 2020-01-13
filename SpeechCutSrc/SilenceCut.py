from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)

# Cut the audio at silence position
def slice_cut_silence(audio_path_str):

    # Load your audio.
    song = AudioSegment.from_wav(audio_path_str)

    audio_path = Path(audio_path_str)
    dir = audio_path.parent
    stem = audio_path.stem

    print("song dBFS: {}".format(song.dBFS))

    # Split track where the silence is 2 seconds or more and get chunks using
    # the imported function.
    chunks = split_on_silence(
        # Use the loaded audio.
        song,
        # Specify that a silent chunk must be at least 1 seconds or 1000 ms long.
        min_silence_len=1000,
        # Consider a chunk silent if it's quieter than (the max. amplitude of track - 15) dBFS.
        silence_thresh=song.dBFS-15,
        keep_silence=500
    )

    print(len(chunks))
    audio_slices = []

    # setting minimum length of each chunk to 10 seconds
    target_length = 10 * 1000
    output_chunks = [chunks[0]]
    for chunk in chunks[1:]:
        if len(output_chunks[-1]) < target_length:
            output_chunks[-1] += chunk
        else:
            # if the last output chunk is longer than the target length,
            # we can start a new one
            output_chunks.append(chunk)

    # Process each chunk with your parameters
    for i, chunk in enumerate(output_chunks):

        # Create a silence chunk that's 0.5 seconds (or 500 ms) long for padding.
        # set frame rate as the original track
        silence_chunk = AudioSegment.silent(duration=500, frame_rate=song.frame_rate)

        # Add the padding chunk to beginning and end of the entire chunk.
        audio_chunk = silence_chunk + chunk + silence_chunk

        # Normalize the entire chunk. To amplify the audio
        normalized_chunk = match_target_amplitude(audio_chunk, -20.0)

        # Export the audio chunk
        out_path = dir / "{}_silence{}.wav".format(stem, i)
        print("Exporting {} dBFS {}.".format(out_path, normalized_chunk.dBFS))
        normalized_chunk.split_to_mono()[1].export(
            out_path,
            format="wav"
        )
        audio_slices.append(str(out_path))
    return audio_slices