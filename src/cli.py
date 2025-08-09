#!/usr/bin/env python3
"""
Simple CLI wrapper around yt-dlp for validation before building Streamlit UI.
Usage examples:
  python cli.py info <url>
  python cli.py formats <url>
  python cli.py download <url> --format_id 22
  python cli.py audio <url> --audio-format mp3
"""

import argparse
import logging
import os
import sys
import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(message)s")


def get_info(url):
    opts = {"quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            logging.error(f"Failed to fetch info: {e}")
            return None


def print_basic_info(info):
    if not info:
        print("No info available.")
        return
    print("Title:", info.get("title"))
    print("Uploader:", info.get("uploader"))
    print("Duration (s):", info.get("duration"))
    print("Webpage URL:", info.get("webpage_url"))
    print("ID:", info.get("id"))
    print("Available formats count:", len(info.get("formats", [])))


def print_formats(info, limit=20):
    if not info:
        print("No info/formats available.")
        return
    formats = info.get("formats", [])
    print(f"\nShowing up to {limit} formats (format_id, ext, height, note, approx filesize):\n")
    for f in formats[:limit]:
        fid = f.get("format_id")
        ext = f.get("ext")
        height = f.get("height")
        note = f.get("format_note", "")
        fs = f.get("filesize") or f.get("filesize_approx")
        print(f"{fid}\t{ext}\theight={height}\t{note}\tfilesize={fs}")


def download(url, format_id=None, outtmpl="downloads/%(title)s.%(ext)s", extract_audio=False, audio_format="mp3"):
    os.makedirs(os.path.dirname(outtmpl), exist_ok=True)
    opts = {
        "outtmpl": outtmpl,
        "continuedl": True,
        "noplaylist": True,
        # you can add rate limit or retries here if needed
    }
    if format_id:
        opts["format"] = format_id
    if extract_audio:
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": "192",
        }]

    def progress_hook(d):
        status = d.get("status")
        if status == "downloading":
            percent = d.get("_percent_str", "").strip()
            eta = d.get("_eta_str", "")
            sys.stdout.write(f"\r{percent} ETA:{eta}    ")
            sys.stdout.flush()
        elif status == "finished":
            print("\nDownload finished — finalizing...")

    opts["progress_hooks"] = [progress_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info
    except Exception as e:
        logging.error(f"Download failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="yt-dlp based CLI validator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info", help="Show basic metadata")
    p_info.add_argument("url")

    p_formats = sub.add_parser("formats", help="List available formats")
    p_formats.add_argument("url")

    p_download = sub.add_parser("download", help="Download a video (choose format_id from formats)")
    p_download.add_argument("url")
    p_download.add_argument("--format_id", "-f", help="format_id to download (optional, default 'best')")

    p_audio = sub.add_parser("audio", help="Download and extract audio")
    p_audio.add_argument("url")
    p_audio.add_argument("--audio-format", default="mp3", help="preferred audio codec (mp3, m4a, etc.)")

    args = parser.parse_args()

    if args.cmd == "info":
        info = get_info(args.url)
        print_basic_info(info)
    elif args.cmd == "formats":
        info = get_info(args.url)
        print_formats(info)
    elif args.cmd == "download":
        info = download(args.url, format_id=args.format_id)
        if info:
            print("Saved:", info.get("_filename") or info.get("requested_downloads"))
    elif args.cmd == "audio":
        info = download(args.url, extract_audio=True, audio_format=args.audio_format)
        if info:
            print("Audio saved. Title:", info.get("title"))


if __name__ == "__main__":
    main()
