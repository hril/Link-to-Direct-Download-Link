import os
import requests
from flask import Flask, request, jsonify, send_file, redirect

from pytube import YouTube 
import time
import requests
from urllib.parse import urlparse, unquote
from PIL import Image
from io import BytesIO
from PIL.PngImagePlugin import PngInfo
import tempfile

app = Flask(__name__)
mime_map = {
    "text/javascript": ".mjs", "application/json": ".json", "application/manifest+json": ".webmanifest", "application/msword": ".wiz", "application/n-quads": ".nq", "application/n-triples": ".nt", "application/octet-stream": ".so", "application/oda": ".oda", "application/pdf": ".pdf", "application/pkcs7-mime": ".p7c", "application/postscript": ".eps", "application/trig": ".trig", "application/vnd.apple.mpegurl": ".m3u8", "application/vnd.ms-excel": ".xlb", "application/vnd.ms-powerpoint": ".pwz", "application/wasm": ".wasm", "application/x-bcpio": ".bcpio", "application/x-cpio": ".cpio", "application/x-csh": ".csh", "application/x-dvi": ".dvi", "application/x-gtar": ".gtar", "application/x-hdf": ".hdf", "application/x-hdf5": ".h5", "application/x-latex": ".latex", "application/x-mif": ".mif", "application/x-netcdf": ".nc", "application/x-pkcs12": ".pfx", "application/x-pn-realaudio": ".ram", "application/x-python-code": ".pyo", "application/x-sh": ".sh", "application/x-shar": ".shar", "application/x-shockwave-flash": ".swf", "application/x-sv4cpio": ".sv4cpio", "application/x-sv4crc": ".sv4crc", "application/x-tar": ".tar", "application/x-tcl": ".tcl", "application/x-tex": ".tex", "application/x-texinfo": ".texinfo", "application/x-troff": ".tr", "application/x-troff-man": ".man", "application/x-troff-me": ".me", "application/x-troff-ms": ".ms", "application/x-ustar": ".ustar", "application/x-wais-source": ".src", "application/xml": ".xpdl", "application/zip": ".zip", "audio/3gpp": ".3gpp", "audio/3gpp2": ".3gpp2", "audio/aac": ".ass", "audio/basic": ".snd", "audio/mpeg": ".mp2", "audio/opus": ".opus", "audio/x-aiff": ".aiff", "audio/x-pn-realaudio": ".ra", "audio/x-wav": ".wav", "image/avif": ".avif", "image/bmp": ".bmp", "image/gif": ".gif", "image/ief": ".ief", "image/jpeg": ".jpeg", "image/heic": ".heic", "image/heif": ".heif", "image/png": ".png", "image/svg+xml": ".svg", "image/tiff": ".tif", "image/vnd.microsoft.icon": ".ico", "image/webp": ".webp", "image/x-cmu-raster": ".ras", "image/x-portable-anymap": ".pnm", "image/x-portable-bitmap": ".pbm", "image/x-portable-graymap": ".pgm", "image/x-portable-pixmap": ".ppm", "image/x-rgb": ".rgb", "image/x-xbitmap": ".xbm", "image/x-xpixmap": ".xpm", "image/x-xwindowdump": ".xwd", "message/rfc822": ".nws", "text/css": ".css", "text/csv": ".csv", "text/html": ".htm", "text/markdown": ".markdown", "text/n3": ".n3", "text/plain": ".srt", "text/richtext": ".rtx", "text/rtf": ".rtf", "text/tab-separated-values": ".tsv", "text/vtt": ".vtt", "text/x-python": ".py", "text/x-rst": ".rst", "text/x-setext": ".etx", "text/x-sgml": ".sgml", "text/x-vcard": ".vcf", "text/xml": ".xml", "video/mp4": ".mp4", "video/mpeg": ".mpg", "video/quicktime": ".qt", "video/webm": ".webm", "video/x-msvideo": ".avi", "video/x-sgi-movie": ".movie"
}
temp_dir = tempfile.gettempdir()

def base26(n):
    if n == 0:  return ""
    mp = "abcdefghijklmnopqrstuvwxyz"
    if n < 26:  return mp[n]
    return base26((n) // 26) + mp[(n) % 26]

def generate_base26_time():
    return base26(int(time.time()))

def remove_meta(image_bytes):
    img = Image.open(BytesIO(image_bytes))
    data = list(img.getdata())
    img_without_meta = Image.new(img.mode, img.size)
    img_without_meta.putdata(data)
    
    output = BytesIO()
    img_without_meta.save(output, format='PNG')
    return output.getvalue()

def replace_meta(image_bytes, metadata_json):
    img = Image.open(BytesIO(image_bytes))
    metadata = PngInfo()
    for key, value in metadata_json.items():
        metadata.add_text(key, str(value))
    
    output = BytesIO()
    img.save(output, format='PNG', pnginfo=metadata)
    return output.getvalue()

metadata_json = {"parameters": "According to all known laws of aviation, there is no way a bee should be able to fly. Its wings are too small to get its fat little body off the ground.\nNegative prompt: The bee, of course, flies anyway because bees don't care what humans think is impossible.\nSteps: 100, Sampler: DPM++ 2S a Karras, CFG scale: 7, Seed: 2700961759, Size: 1536x2048, Model hash: d82hailx9a, Model: ho-red, VAE hash: 4f37bgfx1a, VAE: sdxl_vae.safetensors, Clip skip: 2, Denoising strength: 0.4, Clip skip: 2, Hires upscale: 4, Hires steps: 200, Hires upscaler: R-ESRGAN 4x+ Anime6B, ADetailer model: face_yolov8n.pt, ADetailer confidence: 0.3, ADetailer dilate erode: 4, ADetailer mask blur: 4, ADetailer denoising strength: 0.4, ADetailer inpaint only masked: True, ADetailer inpaint padding: 32, ADetailer version: 24.5.1, Lora hashes: \"Twitter: hailx\", Version: f0.0.17v1.8.0rc-latest-276-g29be1da7"}

@app.route('/yta', methods=['GET'])
def yta():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    yt = YouTube(url)
    destination = temp_dir
    title = yt.video_id
    mp4_filename = f"{title}.mp4"
    mp3_filename = f"{title}.mp3"
    target_mp4 = os.path.join(destination, mp4_filename)
    target_mp3 = os.path.join(destination, mp3_filename)

    if not os.path.exists(target_mp3):
        if not os.path.exists(target_mp4):
            video = yt.streams.filter(only_audio=True).first() 
            video.download(output_path=destination, filename=mp4_filename)
        os.system(f"ffmpeg -i {target_mp4} -q:a 0 -map a {target_mp3}")

    file_url = f"http://{request.host}/files/{target_mp3.replace('/', '%3E')}"
    return redirect(file_url, code=302)        

@app.route('/', methods=['GET'])
def download_file():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    a = request.args.get('a', '1').lower() != '0'
    b = request.args.get('b', '0').lower() != '0'
    c = request.args.get('c', '0').lower() != '0'
    fn = request.args.get('fn')
    
    if fn:
        filename = fn
    elif a:
        filename = generate_base26_time()
    else:
        filename = os.path.basename(unquote(urlparse(url).path))
        
    response = requests.head(url)
    if not os.path.splitext(filename)[1]:
        content_type = response.headers.get('content-type', '').split(';')[0]
        filename += mime_map.get(content_type, '.html')

    filepath = os.path.join(temp_dir, filename)
    if not os.path.exists(filepath):
        response = requests.get(url)
        content = response.content
        if c:
            content = replace_meta(content, metadata_json=metadata_json)
        elif b:
            content = remove_meta(content)
        with open(filepath, 'wb') as f:
            f.write(content)

    file_url = f"http://{request.host}/files/{filepath.replace('/', '%3E')}"
    return redirect(file_url, code=302)

@app.route('/files/<filename>', methods=['GET'])
def serve_file(filename):
    filename = filename.replace('>', '/')
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(port=7860)