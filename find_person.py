import multiprocessing as mp
import PIL.ImageDraw
import PIL.Image
import numpy as np
import requests
import io
import face_recognition
import PIL
import signal
import time
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument(
    "-i",
    "--input",
    default="photo_links.txt",
    type=str,
    help="path to txt file with photo links"
)
parser.add_argument(
    "--processed-file",
    default="processed.txt",
    type=str,
    help="path to txt file where to store processed links"
)
parser.add_argument(
    "--found-file",
    default="found.txt",
    type=str,
    help="path to txt file where to store links to photos where target was found"
)
parser.add_argument(
    "--target",
    default="target.jpg",
    type=str,
    help="path to target image. There should be only one person in the photo"
)
parser.add_argument(
    "--tolerance",
    default=0.6,
    type=float,
    help="the less tolerance is, the more similar faces are searched for"
)
parser.add_argument(
    "--request-retries",
    default=3,
    type=int,
    help="number of retries to download image"
)
parser.add_argument(
    "--cpu",
    default=4,
    type=int,
    help="number of processes to run"
)
parser.add_argument(
    "--no-highlight",
    action="store_true",
    default=False,
    help="do not highlight face on images where person was found",
)
args = parser.parse_args().__dict__


# makes possible to shutdown program by CTRL+C
def initializer():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

with open(args["processed_file"], "r") as processed_file:
    processed = list(map(str.strip, processed_file.readlines()))

with open(args["input"], "r") as input_file:
    urls = list(map(str.strip, input_file.readlines()))

total_urls = len(urls)

# load person to find from image
target_img = face_recognition.load_image_file(args["target"])
target = face_recognition.face_encodings(target_img)[0]

def safe_file_writer(filename, buffer):
    """
    Process for writing to files from buffer

    Args:
        filename (str): path to file
        buffer (multiprocessing.manager.Queue): buffer that contains text to save
    """
    file = open(filename, "a", encoding="utf-8")
    while True:
        text = buffer.get()
        if text == '&&&':
            file.close()
            break
        file.write(f"{text}\n")
        file.flush()


def find_person(i, url, target, found_buffer, processed_buffer):
    if url in processed:
        print(f"skip {str(i)} - {url}")
        return
    for retry in range(1, args["request_retries"] + 1):
        try:
            r = requests.get(url)
            break
        except:
            if retry == 3:
                print(f"Failed to request {str(i)} - {url}. Retry {str(retry)}/3")
                return
            print(f"Failed to request {str(i)} - {url}. Retry {str(retry)}/3. Wait 10s.")
            time.sleep(10)
    image_bytes = io.BytesIO(r.content)
    image = face_recognition.load_image_file(image_bytes)
    face_locations = face_recognition.face_locations(image, model="hog")
    face_encodings = face_recognition.face_encodings(image, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        is_person = face_recognition.compare_faces([target], face_encoding, tolerance=args["tolerance"])[0]
        if is_person:
            print(f"found {str(i)} - {url}")
            if args["no_highlight"]:
                with open(f"found/{str(i)}.jpg", "wb") as img_file:
                    img_file.write(image_bytes.getbuffer())
            else:
                top, right, bottom, left = face_location
                pil_image = PIL.Image.open(image_bytes)
                draw = PIL.ImageDraw.Draw(pil_image)
                draw.rectangle(((left, top), (right, bottom)), outline=(255, 0, 0))
                pil_image.save(f"found/{str(i)}.jpg")
            found_buffer.put(f"{url}")
            break
    processed_buffer.put(f"{url}")
    if i % 100 == 0:
        print(f"processing {str(i)}/{str(total_urls)}")

def main():
    manager = mp.Manager()
    found_buffer = manager.Queue()
    processed_buffer = manager.Queue()
    pool = mp.Pool(args["cpu"], initializer=initializer)
    try:
        processed_writer = pool.apply_async(safe_file_writer, (args["processed_file"], processed_buffer,))
        found_writer = pool.apply_async(safe_file_writer, (args["found_file"], found_buffer,))

        jobs = []
        for i, url in enumerate(urls, start=1):
            job = pool.apply_async(find_person, (i, url, target, found_buffer, processed_buffer))
            jobs.append(job)

        for job in jobs:
            job.get()

        processed_buffer.put('&&&')
        found_buffer.put('&&&')
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()

if __name__ == "__main__":
    main()
    
