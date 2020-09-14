from datetime import datetime, timedelta
from json import dump, dumps, load, loads
from os import system, name, path
from requests import get, post
from threading import Thread
from time import time, sleep
from itertools import cycle
from pandas import read_csv
from sys import stdout

if name == "nt":
    SEP = "\\"
    CLEAR = "cls"
else:
    SEP = "/"
    CLEAR = "clear"

NOSCAN = []
# LOADING = False

ROOT_DIR = path.dirname(path.abspath(__file__))
AUTH_DIR = SEP.join((ROOT_DIR, "auth"))
TRACK_DIR = SEP.join((ROOT_DIR, "track"))

AUTH_FILE = SEP.join((AUTH_DIR, "fastway_auth.json"))
TOKEN_FILE = SEP.join((AUTH_DIR, "fastway_token.json"))
LABELS_FILE = SEP.join((TRACK_DIR, "labels.csv"))

TOKEN_URL = "https://identity.fastway.org/connect/token"
TRACK_URL = "https://api.myfastway.com.au/api/track/label/"

# def animate():
#     frames = ["|", "/", "-", "\\"]
#     message = "Loading, please wait..."

#     print("LOADING in animate():", LOADING)

#     while LOADING:
#         print("Test")
#         sleep(1)
#         for frame in frames:
#             stdout.write(message, frame)
#             stdout.flush()
#             sleep(0.1)

#     print("Done loading.")

# def set_loading(loading):
#     LOADING = loading
#     return LOADING

def get_labels(file=LABELS_FILE):
    with open(file, "r") as file:
        data = read_csv(file, usecols=["Tracking Number"]).values.tolist()
    labels = []
    for label in data:
        labels.append(label[0])
    return labels

def get_token(file=TOKEN_FILE):
    try:
        with open(file, "r") as file:
            token = load(file)
            if datetime.now().isoformat() < token["token_expiry"]:
                credentials = (token["token_type"], token["access_token"])
                return { "Authorization": " ".join(credentials) }
            else:
                return renew_token()
    except FileNotFoundError:
        return renew_token()

def renew_token(files=(AUTH_FILE, TOKEN_FILE)):
    try:
        with open(files[0], "r") as file:
            authorization = load(file)
    except FileNotFoundError as exception:
        raise exception

    response = post(TOKEN_URL, data=authorization)

    token = loads(response.text)
    expiry = datetime.now() + timedelta(hours=1)
    token["token_expiry"] = expiry.isoformat()

    with open(files[1], "w") as file:
        dump(token, file, indent=4, sort_keys=True)
    print("Generated new access token:", token["access_token"][-4:])
    return get_token()

def track_items(labels=["BD0010915392","BD0010915414"]):
    results = []
    for label in labels:
        try:
            response = get("".join((TRACK_URL, label)), headers=get_token())
            response_data = loads(response.text)["data"]
            if response_data != NOSCAN:
                results.append(response_data[-1])
            else:
                results.append(response_data)
        except IndexError as exception:
            print(": ".join(("Error", str(response.status_code), label)))
            raise exception
    return results

def main():
    system(CLEAR)
    start = time()

    # set_loading(True)
    # print("LOADING in main():", LOADING)
    # Thread(daemon=True, target=animate).start()

    labels = get_labels()
    response = track_items(labels)

    # set_loading(False)
    duration = time() - start
    length = str(len(response))
    token = get_token()["Authorization"][-4:]

    counter = 0

    for item in response:
        system(CLEAR)
        if item == NOSCAN:
            print("Error: No data for this record.")
        else:
            print(dumps(item, indent=4, sort_keys=True))
        print(" ".join(("Record", str(counter + 1), "of", length)))
        print(" ".join(("Fetched with access token:", token)))
        print(" ".join(("Fetched in", str(duration), "seconds.")))
        input("Press [ENTER] to continue: ")
        counter = counter + 1

    system(CLEAR)
    print("Done.")
    input("Press [ENTER] to exit: ")
    system(CLEAR)

if __name__ == "__main__":
    main()
