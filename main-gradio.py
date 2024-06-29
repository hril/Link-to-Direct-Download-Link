import os

import json
import time
import gradio as gr
import requests
from urllib.parse import urlparse, unquote
from PIL import Image
from io import BytesIO
from PIL.PngImagePlugin import PngInfo
import tempfile

mime_map = {
    "text/javascript": ".mjs", "application/json": ".json", "application/manifest+json": ".webmanifest", "application/msword": ".wiz", "application/n-quads": ".nq", "application/n-triples": ".nt", "application/octet-stream": ".so", "application/oda": ".oda", "application/pdf": ".pdf", "application/pkcs7-mime": ".p7c", "application/postscript": ".eps", "application/trig": ".trig", "application/vnd.apple.mpegurl": ".m3u8", "application/vnd.ms-excel": ".xlb", "application/vnd.ms-powerpoint": ".pwz", "application/wasm": ".wasm", "application/x-bcpio": ".bcpio", "application/x-cpio": ".cpio", "application/x-csh": ".csh", "application/x-dvi": ".dvi", "application/x-gtar": ".gtar", "application/x-hdf": ".hdf", "application/x-hdf5": ".h5", "application/x-latex": ".latex", "application/x-mif": ".mif", "application/x-netcdf": ".nc", "application/x-pkcs12": ".pfx", "application/x-pn-realaudio": ".ram", "application/x-python-code": ".pyo", "application/x-sh": ".sh", "application/x-shar": ".shar", "application/x-shockwave-flash": ".swf", "application/x-sv4cpio": ".sv4cpio", "application/x-sv4crc": ".sv4crc", "application/x-tar": ".tar", "application/x-tcl": ".tcl", "application/x-tex": ".tex", "application/x-texinfo": ".texinfo", "application/x-troff": ".tr", "application/x-troff-man": ".man", "application/x-troff-me": ".me", "application/x-troff-ms": ".ms", "application/x-ustar": ".ustar", "application/x-wais-source": ".src", "application/xml": ".xpdl", "application/zip": ".zip", "audio/3gpp": ".3gpp", "audio/3gpp2": ".3gpp2", "audio/aac": ".ass", "audio/basic": ".snd", "audio/mpeg": ".mp2", "audio/opus": ".opus", "audio/x-aiff": ".aiff", "audio/x-pn-realaudio": ".ra", "audio/x-wav": ".wav", "image/avif": ".avif", "image/bmp": ".bmp", "image/gif": ".gif", "image/ief": ".ief", "image/jpeg": ".jpeg", "image/heic": ".heic", "image/heif": ".heif", "image/png": ".png", "image/svg+xml": ".svg", "image/tiff": ".tif", "image/vnd.microsoft.icon": ".ico", "image/webp": ".webp", "image/x-cmu-raster": ".ras", "image/x-portable-anymap": ".pnm", "image/x-portable-bitmap": ".pbm", "image/x-portable-graymap": ".pgm", "image/x-portable-pixmap": ".ppm", "image/x-rgb": ".rgb", "image/x-xbitmap": ".xbm", "image/x-xpixmap": ".xpm", "image/x-xwindowdump": ".xwd", "message/rfc822": ".nws", "text/css": ".css", "text/csv": ".csv", "text/html": ".htm", "text/markdown": ".markdown", "text/n3": ".n3", "text/plain": ".srt", "text/richtext": ".rtx", "text/rtf": ".rtf", "text/tab-separated-values": ".tsv", "text/vtt": ".vtt", "text/x-python": ".py", "text/x-rst": ".rst", "text/x-setext": ".etx", "text/x-sgml": ".sgml", "text/x-vcard": ".vcf", "text/xml": ".xml", "video/mp4": ".mp4", "video/mpeg": ".mpg", "video/quicktime": ".qt", "video/webm": ".webm", "video/x-msvideo": ".avi", "video/x-sgi-movie": ".movie"}

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

def download_file(url, filename=None, gen_base26=True, remove_metadata=False, add_fake_meta=False):
    if not url:
        return "URL is required"
    
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        return "Failed to fetch file"

    if not filename:
        if gen_base26:
            filename = generate_base26_time()
        else:
            content_disp = response.headers.get('content-disposition')
            if content_disp:
                filename = content_disp.split('filename=')[-1].strip('"\'')
            else:
                filename = os.path.basename(unquote(urlparse(url).path))

    if not os.path.splitext(filename)[1]:
        content_type = response.headers.get('content-type', '').split(';')[0]
        filename += mime_map.get(content_type, '.html')

    content = response.content
    if filename.lower().endswith('.png'):
        if add_fake_meta:
            print("Adding fake metadata:")
            print(content[:50])
            
            content = replace_meta(content, metadata_json=metadata_json)
            print(content[:50])
        elif remove_metadata:
            print("Removing metadata:")
            print(content[:50])
            content = remove_meta(content)
            print(content[:50])
    
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, filename)
    
    with open(filename, 'wb') as f:
        f.write(content)

    return filename

iface = gr.Interface(
    fn=download_file,
    inputs=[
        gr.Textbox(label="Enter URL of the file to download"),
        gr.Textbox(label="Enter filename (optional)"),
        gr.Checkbox(label="Generate base26 filename if empty", value=True),
        gr.Checkbox(label="Remove PNG Metadata", value=False),
        gr.Checkbox(label="Add Fake Metadata", value=False)
    ],
    outputs=gr.File(label="Downloaded File"),
    allow_flagging="never",
)

iface.launch()

