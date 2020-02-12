from accuracy_lib import *

"""
    Read in xlxs file
"""

file_name = '/Users/sun/Downloads/9136038592380002401.xlsx'

source_df = pd.read_excel(file_name)

# Column of STT transcripts
col1 = 5

# Column of correct transcripts
col2 = 6

missing_count, match_count, added_count, df1 = HitIt(col1, col2, source_df.loc[
    (source_df['SLOW_DOWN_RATE'] == 0.85) & (source_df['QUALITY'] == True) & (source_df['AGENT_SEQ'] == 44)])
print("{} words matched, {} words missing from the correct transcript and {} words added by TTS".format(match_count,
                                                                                                        missing_count,
                                                                                                        added_count))
print("{}% of correct transcripts is presented".format(round(match_count / (missing_count + match_count) * 100)))
# print("Word Error Rate is {}%".format(round((match_count-added_count)/(match_count+added_count+missing_count)*100)))

df1.to_excel("details.xlsx", index=None, header=True)
