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

# missing_count, match_count, added_count, df1 = \
#     HitIt(col1,
#           col2,
#           source_df.loc[(source_df['SLOW_DOWN_RATE'] == 0.9) & (source_df['QUALITY']) & (source_df['AGENT_SEQ'] == 3)])
# print("{} words matched, {} words missing from the correct transcript and {} words added by TTS".format(match_count,
#                                                                                                         missing_count,
#                                                                                                         added_count))
# print("{}% of correct transcripts is presented".format(round(match_count / (missing_count + match_count) * 100)))
# print("Word Error Rate is {}%".format(round((match_count-added_count)/(match_count+added_count+missing_count)*100)))

slow_down_rate = [
    1.0, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6
]
agent_seq_no = 47
output = source_df.copy()
output["MATCHED_RATE"] = 0.0
output["SPEED"] = 0.0
output["TOTAL_WORDS"] = 0
output["STT_WORDS"] = 0
for agent_seq in range(agent_seq_no):
    for rate in slow_down_rate:
        index = (source_df['SLOW_DOWN_RATE'] == rate) & (source_df['QUALITY'] == True) & (
                source_df['AGENT_SEQ'] == agent_seq)
        missing_count, match_count, added_count, df1 = \
            HitIt(col1,
                  col2,
                  source_df.loc[index])
        output.loc[index, "MATCHED_RATE"] = match_count / (match_count + missing_count)
        output.loc[index, "TOTAL_WORDS"] = (match_count + missing_count)
        output.loc[index, "STT_WORDS"] = (match_count + added_count)
        output.loc[index, "SPEED"] = (match_count + missing_count) / (
                output.loc[index, "TIME_MS"] / 1000)
        if rate == 1.0:
            index = (source_df['SLOW_DOWN_RATE'] == rate) & (source_df['QUALITY'] == False) & (
                    source_df['AGENT_SEQ'] == agent_seq)
            missing_count, match_count, added_count, df1 = \
                HitIt(col1,
                      col2,
                      source_df.loc[index])
            output.loc[index, "MATCHED_RATE"] = match_count / (match_count + missing_count)
            output.loc[index, "TOTAL_WORDS"] = (match_count + missing_count)
            output.loc[index, "STT_WORDS"] = (match_count + added_count)
            output.loc[index, "SPEED"] = (match_count + missing_count) / (
                    output.loc[index, "TIME_MS"] / 1000)

output.to_excel('text.xlsx', index=None, header=True)
