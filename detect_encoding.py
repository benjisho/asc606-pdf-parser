import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

file_encoding = detect_encoding("output_files/ASSR-Revenue-Recognition-Under-ASC-606-Blueprint.txt")
print(f"Detected encoding: {file_encoding}")
