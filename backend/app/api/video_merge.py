"""
NexusCommerce AI - Automated Video + Voiceover Merger Route
Allows 1-click video upload from phone browser, automatically merges with
generated voiceover via ffmpeg, and delivers the final video to phone gallery/downloads.
"""

import os
import shutil
import subprocess
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import logging

logger = logging.getLogger("nexus.video_merge")

router = APIRouter(tags=["Video Merger"])

VOICEOVER_PATH = "/sdcard/Download/nexuscommerce_voiceover.mp3"
OUTPUT_PATH = "/sdcard/Download/NexusCommerce_Final_Demo.mp4"
FALLBACK_VOICEOVER = "/root/nexuscommerce/voiceover.mp3"

@router.get("/merge", response_class=HTMLResponse)
async def get_merge_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NexusCommerce AI — 1-Tap Video + Audio Merger</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { background: #0B0F19; color: #F1F5F9; font-family: system-ui, -apple-system, sans-serif; }
        </style>
    </head>
    <body class="min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-[#111827] border border-cyan-500/40 rounded-2xl p-6 shadow-2xl space-y-5">
            <div class="text-center space-y-2">
                <div class="w-12 h-12 bg-cyan-500/20 border border-cyan-500/40 rounded-xl flex items-center justify-center mx-auto text-2xl">
                    🎬
                </div>
                <h1 class="text-lg font-extrabold text-white">Automated Video + Voiceover Merger</h1>
                <p class="text-xs text-slate-300">
                    Select your screen recording (<code class="text-cyan-400 font-mono">Record_*.mp4</code>). We will automatically attach the AI voiceover narration using FFmpeg!
                </p>
            </div>

            <form action="/merge" method="post" enctype="multipart/form-data" class="space-y-4">
                <div class="space-y-2">
                    <label class="block text-xs font-semibold text-slate-300">Select Screen Recording Video:</label>
                    <input 
                        type="file" 
                        name="video_file" 
                        accept="video/*" 
                        required 
                        class="block w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-cyan-500 file:text-slate-950 hover:file:bg-cyan-400 bg-slate-900 border border-slate-800 rounded-xl p-2 cursor-pointer"
                    />
                </div>

                <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-3 text-[11px] text-slate-400 space-y-1 font-mono">
                    <div>🎙️ Audio: <span class="text-emerald-400 font-bold">nexuscommerce_voiceover.mp3</span></div>
                    <div>⚡ Engine: <span class="text-white">FFmpeg AAC 192k Stream Mux</span></div>
                    <div>🎯 Output: <span class="text-cyan-300">NexusCommerce_Final_Demo.mp4</span></div>
                </div>

                <button 
                    type="submit" 
                    id="submitBtn"
                    class="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-extrabold text-xs shadow-lg shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all transform active:scale-95"
                >
                    <span>⚡ Merge Video with Voiceover Now</span>
                </button>
            </form>

            <div id="loadingIndicator" class="hidden text-center py-3 text-xs text-cyan-400 font-mono animate-pulse">
                ⏳ Processing with FFmpeg... Please wait a few seconds.
            </div>
        </div>

        <script>
            document.querySelector('form').onsubmit = function() {
                document.getElementById('submitBtn').disabled = true;
                document.getElementById('submitBtn').classList.add('opacity-50');
                document.getElementById('loadingIndicator').classList.remove('hidden');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/merge")
async def process_merge(video_file: UploadFile = File(...)):
    if not video_file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    temp_input = "/tmp/uploaded_input.mp4"
    audio_path = VOICEOVER_PATH if os.path.exists(VOICEOVER_PATH) else FALLBACK_VOICEOVER

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=500, detail=f"Voiceover audio not found at {audio_path}")

    # 1. Save uploaded file to temp
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    logger.info(f"Received video file {video_file.filename} ({os.path.getsize(temp_input)} bytes). Merging...")

    # 2. Run FFmpeg command to merge video + audio
    cmd = [
        "ffmpeg", "-y",
        "-i", temp_input,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        OUTPUT_PATH
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        logger.info("FFmpeg merge successful!")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"FFmpeg error: {e.stderr[:300]}")

    # 3. Return success download page or file response
    success_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Merge Complete — NexusCommerce AI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>body {{ background: #0B0F19; color: #F1F5F9; font-family: system-ui, sans-serif; }}</style>
    </head>
    <body class="min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-[#111827] border border-emerald-500/50 rounded-2xl p-6 shadow-2xl text-center space-y-5">
            <div class="w-14 h-14 bg-emerald-500/20 border border-emerald-500/40 rounded-2xl flex items-center justify-center mx-auto text-3xl">
                🎉
            </div>
            <h1 class="text-xl font-extrabold text-white">Merge Completed Successfully!</h1>
            <p class="text-xs text-slate-300 leading-relaxed">
                Your video <span class="text-cyan-400 font-mono font-bold">{video_file.filename}</span> has been merged with the studio AI voiceover.
            </p>

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-slate-300 font-mono text-left space-y-1">
                <div>📁 Saved To: <span class="text-emerald-400 break-all font-bold">{OUTPUT_PATH}</span></div>
                <div>📊 Size: <span class="text-white">{round(os.path.getsize(OUTPUT_PATH) / 1024 / 1024, 2)} MB</span></div>
            </div>

            <div class="space-y-2">
                <a 
                    href="/download-merged"
                    class="block w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-extrabold text-xs shadow-lg shadow-emerald-500/20 transition-all"
                >
                    ⬇️ Download Video to Gallery / Phone Storage
                </a>
                <a 
                    href="/merge" 
                    class="block text-xs text-slate-500 hover:text-slate-300 underline pt-2"
                >
                    Merge another video
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=success_html)

@router.get("/download-merged")
async def download_merged_video():
    if not os.path.exists(OUTPUT_PATH):
        raise HTTPException(status_code=404, detail="Merged video not found.")
    return FileResponse(
        path=OUTPUT_PATH,
        filename="NexusCommerce_Final_Demo.mp4",
        media_type="video/mp4"
    )
