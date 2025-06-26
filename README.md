# Online face recognition
Using [face_recognition](https://github.com/ageitgey/face_recognition)  
Tested on python 3.10.6  
Multiprocess download photos from txt list and check if there is a person.  
No GPU is required 
## Installation
```bash
git clone https://github.com/vonider/online-face-recognition.git
cd online-face-recognition
python -m pip install -r requirements.txt
```
## Usage
Place links to photos in file photo_links.txt  
Put image of person to find in folder  
```python
python find_person.py --target person_to_find.jpg
```
This will download photos to folder "found" with person and highlight it.  
Processed links stored in processed.txt, links with person stored in found.txt.  

## Parameters:
- Specify path to file where links to process stored with parameter `--input`  
- Specify path to file to store processed links with parameter `--processed-file`  
- Specify path to file to store links with person with parameter `--found-file`  
- Specify path to image that contains person to find with parameter `--target`  
- Specify tolerance of similarity with parameter `--tolerance`. Accepts float value between 0 and 1. The less tolerance is, the more similar faces are searched for. 0 means to find almost identical image. Default: 0.6  
- Specify number of retries to download image with parameter `--request-retries`. Default: 3. Links failed to requests are not added to processed file  
- Specify number of processes that program can use with parameter `--cpu`. Default: 4. The more processes there are, the more cpu consumption  
- Parameter `--no-highlight` used to disable marking person of found images  
