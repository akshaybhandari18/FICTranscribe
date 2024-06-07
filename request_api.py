import requests
import os

#base URL of your Flask API
base_url = "http://localhost:5000"

HARDCODED_TOKEN = 'your_hardcoded_token'
# path of the audio file you want to transcribe
audio_file_path = r"C:\Users\Dell\Downloads\abcd.mp3"

headers = {
    'Authorization': HARDCODED_TOKEN
}

# calling transcribe endpoint
with open(audio_file_path, "rb") as file:
    files = {"audio_file": file}
    response = requests.post(f"{base_url}/transcribe", headers=headers, files=files)


if response.status_code == 200:
    
    json_response = response.json()

    transcribed_text = json_response["transcribed_text"]
    text_file_path = json_response["text_file_path"]
    vtt_file_path = json_response["vtt_file_path"]

    print("Transcription successful!")
    print("Transcribed Text:")
    print(transcribed_text)
    print("Text File Path:", text_file_path)
    print("VTT File Path:", vtt_file_path)

    # Downloading the transcribed text file
    text_folder_name = os.path.dirname(text_file_path)
    text_filename = os.path.basename(text_file_path)
    text_response = requests.get(f"{base_url}/download_text/{text_folder_name}/{text_filename}")
    if text_response.status_code == 200:
        with open(text_filename, "wb") as file:
            file.write(text_response.content)
        print("Text file downloaded successfully!")
    else:
        print("Failed to download the text file.")

    # Downloading the VTT file
    vtt_folder_name = os.path.dirname(vtt_file_path)
    vtt_filename = os.path.basename(vtt_file_path)
    vtt_response = requests.get(f"{base_url}/download_vtt/{vtt_folder_name}/{vtt_filename}")
    if vtt_response.status_code == 200:
        with open(vtt_filename, "wb") as file:
            file.write(vtt_response.content)
        print("VTT file downloaded successfully!")
    else:
        print("Failed to download the VTT file.")
else:
    print("Transcription failed.")
    print("Status Code:", response.status_code)
    print("Error:", response.text)