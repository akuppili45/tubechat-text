from flask import Flask, jsonify
import xml.etree.ElementTree as ElementTree
from html import unescape
import math
import time
from flask_cors import CORS
import base64
import boto3
import requests
import pytube


app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    return jsonify({"message": "hello world"})

@app.route("/get-text/<path:curr_link>")
def get_text(curr_link):
    try:
        print(curr_link, flush=True)
        youtube = pytube.YouTube(curr_link)
        print("curr_link", flush=True)
        video_id = youtube.video_id
        youtube.bypass_age_gate()
        caption = youtube.captions['a.en']
        full_text = xml_caption_to_srt(caption.xml_captions)
        # put full_text in cloud storage write to a file and return the link
        
        folder_name = video_id
        file_name = f'{folder_name}/captions.txt'
        def write_to_s3_bucket(text: str) -> str:
            s3 = boto3.client('s3')
            bucket_name = 'tubechat-contents'
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=file_name)
            check = 'Contents' in response
            if not check:
                s3.put_object(Body=text, Bucket=bucket_name, Key=file_name)
                # create vector store
                # url = f'http://127.0.0.1:5001/vector-store/{video_id}'
                # response = requests.get(url)
                # if response.status_code == 200:
                #     print("worked")
                # else:
                #     print(f"Can't create vector store. Request failed with status code {response.status_code}")
            else:
                print("already exists", flush=True)
            file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
            return file_url

        
        # file_url = write_to_s3_bucket(full_text)
        
        # return jsonify({"message": full_text, "file_url": file_url, "video_id": video_id})
        return jsonify({"message": full_text, "video_id": video_id})

    except Exception as e:
        print(e, flush=True)
        return jsonify({"message": "not valid youtube"})

## HELPER METHODS

def xml_caption_to_srt(xml_captions: str) -> str:
        """Convert xml caption tracks to "SubRip Subtitle (srt)".

        :param str xml_captions:
            XML formatted caption tracks.
        """
        segments = []
        root = ElementTree.fromstring(xml_captions)
        fullText = ""
        for i in range(len(root[1])):
            cap = ""
            for child in root[1][i]:
                cap += child.text
            fullText += cap + " "
        return fullText

def float_to_srt_time_format(d: float) -> str:
        """Convert decimal durations into proper srt format.

        :rtype: str
        :returns:
            SubRip Subtitle (str) formatted time duration.

        float_to_srt_time_format(3.89) -> '00:00:03,890'
        """
        fraction, whole = math.modf(d)
        time_fmt = time.strftime("%H:%M:%S,", time.gmtime(whole))
        ms = f"{fraction:.3f}".replace("0.", "")
        return time_fmt + ms
    