'''
import json
import jsonstreams
import ijson
import requests
from pathlib import Path
pathtowrapper = r'C:\Users\Christian Casteel\Downloads\2021-2025-patent-filewrapper-full-json-20250921\2021.json'

with open(pathtowrapper, 'r', encoding='utf-8') as f:
    objects = ijson.items(f, 'patentFileWrapperDataBag.item')
    for i, obj in enumerate(objects):
        print(f"\n=== Record {i+1} ===")
        print(obj.keys())
        
        other = obj.get('pgpubDocumentMetaData')
        file_uri = obj.get('pgpubDocumentMetaData', {}).get('fileLocationURI')
        print("HERE'S THE FILE URI:", file_uri)

        if other:
            print("pgpubDocumentMetaData keys:", other.keys())
        
        if i == 1:   # stop after 2nd record
            break

save_path = "ipa210501.zip"

headers = {"User-Agent": "PatentWizard/1.0 (Contact: your_email@example.com)"}

r = requests.get(file_uri, headers=headers, stream=True)
if r.status_code == 200:
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Downloaded:", save_path)
else:
    print("Failed with status:", r.status_code)

    # NEED TO GET API KEY FROM USPTO DATABASE
    '''