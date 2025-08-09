import streamlit as st
import yt_dlp
import os
import tempfile

# Page config
st.set_page_config(page_title="Clippy YouTube Downloader", page_icon="🎬", layout="wide")

# Custom CSS for Gen Z style
st.markdown("""
    <style>
    body {
        background-color: #0f0f0f;
        color: white;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff0055, #ff7b00);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 8px 12px;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background: linear-gradient(90deg, #ff7b00, #ff0055);
    }
    .format-card {
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Human-readable size
def sizeof_fmt(num, suffix="B"):
    if num is None:
        return "Unknown"
    for unit in ["", "K", "M", "G", "T", "P"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"

# Download helper (auto merge if video-only)
def download_and_offer(url, format_id, merge=False):
    try:
        with st.spinner("⏳ Downloading..."):
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")

            fmt = f"{format_id}+bestaudio/best" if merge else format_id

            ydl_opts = {
                "format": fmt,
                "outtmpl": output_path,
                "quiet": True,
                "merge_output_format": "mp4",
                "noplaylist": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(result)

            with open(file_path, "rb") as f:
                st.download_button(
                    label="⬇ Click to Save",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="video/mp4" if merge or "video" in fmt else "application/octet-stream",
                )

            os.remove(file_path)
            os.rmdir(temp_dir)
    except yt_dlp.utils.DownloadError:
        st.error("⚠ Unable to download. This video may be blocked in this region or require login.")
    except Exception as e:
        st.error(f"⚠ An error occurred: {str(e)}")

# Title
st.markdown("<h1 style='text-align: center;'>⚡ Clippy YouTube Downloader</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Swift Solves Studios [mehdinathani]</h2>", unsafe_allow_html=True)
url = st.text_input("🎯 Paste YouTube URL here:")

if url:
    try:
        with st.spinner("🔍 Fetching formats..."):
            ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get("formats", [])

        audio_formats = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"]
        video_formats = [f for f in formats if f.get("vcodec") != "none"]

        # Quick Best Quality (video+audio merged)
        st.markdown("### 🚀 Quick Download")
        if st.button("Download Best Quality Available"):
            download_and_offer(url, "bestvideo", merge=True)

        # Video Formats
        with st.expander("🎥 Video Formats", expanded=True):
            cols = st.columns(3)
            for idx, f in enumerate(video_formats):
                with cols[idx % 3]:
                    size = sizeof_fmt(f.get('filesize') or f.get('filesize_approx'))
                    height = f.get('height') or '?'
                    st.markdown(f"""
                        <div class="format-card">
                            <b>{f.get('ext')}</b><br>
                            {height}p<br>
                            {size}
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("Download", key=f"video_{f['format_id']}"):
                        merge_required = f.get('acodec') == 'none'
                        download_and_offer(url, f["format_id"], merge=merge_required)

        # Audio Formats
        with st.expander("🎵 Audio Formats", expanded=False):
            cols = st.columns(3)
            for idx, f in enumerate(audio_formats):
                with cols[idx % 3]:
                    size = sizeof_fmt(f.get('filesize') or f.get('filesize_approx'))
                    st.markdown(f"""
                        <div class="format-card">
                            <b>{f.get('ext')}</b><br>
                            Audio Only<br>
                            {size}
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("Download", key=f"audio_{f['format_id']}"):
                        download_and_offer(url, f["format_id"])
    except yt_dlp.utils.DownloadError:
        st.error("⚠ Unable to fetch video info. The video might be geo-blocked or private.")
    except Exception as e:
        st.error(f"⚠ Error: {str(e)}")
