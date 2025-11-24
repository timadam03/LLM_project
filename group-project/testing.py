example = ['The president of the United States (POTUS) is the head of state and head of government of the United States. The president directs the executive branch of the ...', 'President Donald J. Trump is returning to the White House to build upon his previous successes and use his mandate to reject the extremist policies.', 'Donald J. Trump. President of the United States · JD Vance. VICE PRESIDENT OF THE UNITED STATES · Melania Trump. First Lady OF THE UNITED STATES · The Cabinet. Of ...']

def convert(result_list):
    final_result = ""
    for result in result_list:
        result = result.removesuffix("...")
        final_result += result.strip() + "," + "\n"
    print(final_result)

if __name__ == "__main__":
    convert(example)