import os
import re
import uuid
import logging
import tempfile
import subprocess
import soundfile as sf
import sherpa_onnx
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SenseVoiceSTT")

# Setup models paths
MODELS_DIR = os.environ.get("MODELS_DIR", "/app/models")
MODEL_DIR = os.path.join(MODELS_DIR, "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17")
MODEL_PATH = os.path.join(MODEL_DIR, "model.onnx")
TOKENS_PATH = os.path.join(MODEL_DIR, "tokens.txt")

app = FastAPI(title="SenseVoice STT ONNX Service", version="1.0.0")

# Lazy initialization of the model to allow startup before download completes
recognizer = None

def init_recognizer():
    global recognizer
    if recognizer is not None:
        return recognizer

    if not os.path.exists(MODEL_PATH) or not os.path.exists(TOKENS_PATH):
        logger.error("SenseVoice model files not found. Inference is unavailable.")
        return None

    try:
        logger.info(f"Loading SenseVoice model from: {MODEL_PATH}")
        recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=MODEL_PATH,
            tokens=TOKENS_PATH,
            num_threads=4,  # Thread optimization for host CPU
            use_itn=True
        )
        logger.info("SenseVoice model loaded successfully.")
        return recognizer
    except Exception as e:
        logger.error(f"Failed to load SenseVoice recognizer: {e}")
        return None

class TranscribeResponse(BaseModel):
    text: str
    emotion: str
    raw_tags: List[str]

def parse_sensevoice_output(text: str) -> dict:
    """
    Parses SenseVoice-Small tags (e.g. <|zh|><|NEUTRAL|><|speech|>)
    to extract clean text and detected emotion.
    """
    # Find all <|tag|> patterns
    tags = re.findall(r"<\|(.*?)\|>", text)
    # Clean output text from tags
    clean_text = re.sub(r"<\|.*?\|>", "", text).strip()
    
    # Map emotions
    emotion = "平静" # Default fallback
    for tag in tags:
        tag_upper = tag.upper()
        if "HAPPY" in tag_upper:
            emotion = "开心"
        elif "SAD" in tag_upper:
            emotion = "伤心"
        elif "ANGRY" in tag_upper:
            emotion = "暴躁"
        elif "NEUTRAL" in tag_upper:
            emotion = "平静"

    return {
        "text": clean_text,
        "emotion": emotion,
        "raw_tags": tags
    }

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file in any standard format (AAC, Opus, WAV, MP3, etc.),
    transcodes it to 16kHz mono WAV using ffmpeg, decodes it via ONNX SenseVoice,
    and returns parsed transcription and emotion tag.
    """
    rec = init_recognizer()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech-to-text model is still downloading or loading. Please try again in a few moments."
        )

    # Generate safe unique names for temp storage
    file_id = uuid.uuid4().hex
    temp_dir = tempfile.gettempdir()
    temp_input = os.path.join(temp_dir, f"{file_id}_in")
    temp_wav = os.path.join(temp_dir, f"{file_id}_out.wav")

    try:
        # Save uploaded file
        with open(temp_input, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Transcode file to 16kHz mono PCM WAV via FFmpeg
        # SenseVoice requires 16kHz sample rate mono channel
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", temp_input,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            temp_wav
        ]
        
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr.decode()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to decode audio. Please check file integrity and format."
            )

        # Read samples
        if not os.path.exists(temp_wav):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transcoded audio output is missing."
            )
            
        samples, sample_rate = sf.read(temp_wav, dtype='float32')
        if len(samples) == 0:
            logger.info("Transcoded audio samples are empty. Returning empty text.")
            return {"text": "", "emotion": "平静", "raw_tags": []}

        # Calculate RMS energy to detect background silence/whisper
        import numpy as np
        rms = float(np.sqrt(np.mean(samples**2)))
        logger.info(f"Audio RMS energy: {rms:.6f}")
        if rms < 0.003:
            logger.info(f"Audio RMS energy too low ({rms:.6f}), filtering out as background silence.")
            return {"text": "", "emotion": "平静", "raw_tags": []}

        # Run inference
        stream = rec.create_stream()
        stream.accept_waveform(sample_rate, samples)
        rec.decode_stream(stream)
        
        raw_text = stream.result.text
        logger.info(f"SenseVoice raw output: {raw_text}")
        
        # Parse results
        parsed = parse_sensevoice_output(raw_text)
        
        # SenseVoice hallucination filter for pure silence English filler words (e.g. yes, yeah)
        hallucination_words = {"yes", "yeah", "you", "thanks", "thank you", "huh", "um", "ah", "sigh", "oh", "yes.", "yeah."}
        clean_check = parsed["text"].strip().lower()
        if clean_check in hallucination_words and rms < 0.015:
            logger.info(f"Filtered background silence STT hallucination: '{parsed['text']}' (RMS={rms:.6f})")
            parsed["text"] = ""

        return parsed

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Transcribe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
    finally:
        # Clean up temporary files
        for path in (temp_input, temp_wav):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

@app.get("/api/health")
async def health():
    rec = init_recognizer()
    return {
        "status": "healthy",
        "model_loaded": rec is not None,
        "supported_codecs": ["wav", "mp3", "opus", "aac", "ogg", "flac"]
    }
