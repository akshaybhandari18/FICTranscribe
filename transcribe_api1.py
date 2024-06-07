from flask import Flask, request, jsonify, send_file
import whisper
import os
from io import StringIO
import torch
import logging
from datetime import datetime
from flasgger import Swagger
from constants import HARDCODED_TOKEN, MODEL_NAME, STATIC_FOLDER

app = Flask(__name__)
swagger = Swagger(app)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the Whisper model once during application startup
logger.info("Loading model...")
model = whisper.load_model(MODEL_NAME)
logger.info("Model loaded successfully.")

# Create the static folder if it doesn't exist
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe audio file.
    ---
    parameters:
      - name: audio_file
        in: formData
        type: file
        required: true
        description: The audio file to transcribe
      - name: Authorization
        in: header
        type: string
        required: true
        description: The authorization token
    responses:
      200:
        description: Transcription successful
        schema:
          properties:
            transcribed_text:
              type: string
              description: The transcribed text
            text_file_path:
              type: string
              description: The path to the transcribed text file
            vtt_file_path:
              type: string
              description: The path to the VTT file
      400:
        description: No audio file provided
      401:
        description: Invalid token
      500:
        description: Internal server error
    """
    try:
        # Check if the hardcoded token matches
        provided_token = request.headers.get('Authorization')
        if provided_token != HARDCODED_TOKEN:
            return jsonify({'error': 'Invalid token'}), 401

        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio_file']
        
        # Create a folder with the filename and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{os.path.splitext(audio_file.filename)[0]}_{timestamp}"
        folder_path = os.path.join(STATIC_FOLDER, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, audio_file.filename)
        audio_file.save(file_path)

        # Transcribe the audio using the model
        logger.info(f"Transcribing audio file: {file_path}")
        result = model.transcribe(file_path)

        # Get the transcribed text
        transcribed_text = result["text"]

        # Save the transcribed text to a file in the created folder
        text_filename = os.path.splitext(audio_file.filename)[0] + "_transcribed.txt"
        text_file_path = os.path.join(folder_path, text_filename)
        with open(text_file_path, "w") as text_file:
            text_file.write(transcribed_text)

        # Save the transcribed text to a VTT file in the created folder
        vtt_filename = os.path.splitext(audio_file.filename)[0] + ".vtt"
        vtt_file_path = os.path.join(folder_path, vtt_filename)
        with open(vtt_file_path, "w") as vtt_file:
            vtt_file.write("WEBVTT\n\n")
            for segment in result["segments"]:
                start = segment["start"]
                end = segment["end"]
                text = segment["text"]
                start_time = format_timestamp(start)
                end_time = format_timestamp(end)
                vtt_file.write(f"{start_time} --> {end_time}\n{text}\n\n")

        logger.info(f"Transcription completed for file: {file_path}")
        return jsonify({
            'transcribed_text': transcribed_text,
            'text_file_path': text_file_path,
            'vtt_file_path': vtt_file_path
        })

    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/downloadText/<path:folder_name>/<path:filename>', methods=['GET'])
def download_text(folder_name, filename):
    """
    Download the transcribed text file.
    ---
    parameters:
      - name: folder_name
        in: path
        type: string
        required: true
        description: The name of the folder containing the text file
      - name: filename
        in: path
        type: string
        required: true
        description: The name of the text file to download
    responses:
      200:
        description: File downloaded successfully
      404:
        description: File not found
    """
    try:
        text_file_path = os.path.join(STATIC_FOLDER, folder_name, filename)
        return send_file(text_file_path, as_attachment=True)
    except FileNotFoundError:
        logger.error(f"Text file not found: {text_file_path}")
        return jsonify({'error': 'File not found'}), 404

@app.route('/downloadVtt/<path:folder_name>/<path:filename>', methods=['GET'])
def download_vtt(folder_name, filename):
    """
    Download the VTT file.
    ---
    parameters:
      - name: folder_name
        in: path
        type: string
        required: true
        description: The name of the folder containing the VTT file
      - name: filename
        in: path
        type: string
        required: true
        description: The name of the VTT file to download
    responses:
      200:
        description: File downloaded successfully
      404:
        description: File not found
    """
    try:
        vtt_file_path = os.path.join(STATIC_FOLDER, folder_name, filename)
        return send_file(vtt_file_path, as_attachment=True)
    except FileNotFoundError:
        logger.error(f"VTT file not found: {vtt_file_path}")
        return jsonify({'error': 'File not found'}), 404

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"

if __name__ == "__main__":
    app.run()