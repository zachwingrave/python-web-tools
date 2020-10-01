from json import dump, dumps, load, loads
from requests import get, post
from pandas import read_csv
from csv import writer

from datetime import datetime, timedelta
from os import system, name, path
from time import time

from threading import Thread
from itertools import cycle

# Define OS variables.
if name == "nt":
    SEP = "\\"
    CLEAR = "cls"
else:
    SEP = "/"
    CLEAR = "clear"

# A noscan response.text is an empty list.
NOSCAN = []

# Directory file path constants for this project.
ROOT_DIR = path.dirname(path.abspath(__file__))
AUTH_DIR = SEP.join((ROOT_DIR, "auth"))
TRACK_DIR = SEP.join((ROOT_DIR, "track"))

# Authentication file path constants for this project.
AUTH_FILE = SEP.join((AUTH_DIR, "fastway_auth.json"))
TOKEN_FILE = SEP.join((AUTH_DIR, "fastway_token.json"))

# Log file path constants for this project.
LOG_FILE = SEP.join((TRACK_DIR, "log.json"))
LABELS_FILE = SEP.join((TRACK_DIR, "labels.csv"))
RESULTS_FILE = SEP.join((TRACK_DIR, "results.csv"))

# Endpoint URLs for the myFastway API service.
TOKEN_URL = "https://identity.fastway.org/connect/token"
TRACK_URL = "https://api.myfastway.com.au/api/track/label/"

def sort_keys(data):
    """Return key-sorted dict using JSON conversion."""
    return loads(dumps(data, sort_keys=True))

def get_labels(file=LABELS_FILE):
    """Return tracking labels from spreadsheet as a list."""
    with open(file, "r") as file:
        data = read_csv(file, usecols=["Tracking Number"]).values.tolist()
    labels = []
    for label in data:
        labels.append(label[0])
    return labels

def get_token(file=TOKEN_FILE):
    """Return API bearer token for tracking endpoint as a header string."""
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

def renew_token(auth_file=AUTH_FILE, token_file=TOKEN_FILE):
    """Put new token in /auth/fastway_token.json and return get_token()."""
    try:
        with open(auth_file, "r") as file:
            authorization = load(file)
    except FileNotFoundError as exception:
        raise exception

    response = post(TOKEN_URL, data=authorization)

    token = loads(response.text)
    expiry = datetime.now() + timedelta(hours=1)
    token["token_expiry"] = expiry.isoformat()

    with open(token_file, "w") as file:
        dump(token, file, indent=4, sort_keys=True)
    print("Generated new access token:", token["access_token"][-4:])
    return get_token()

def track_items(labels=["BD0010915392", "BD0010915414"]):
    """Return tracking API results for labels as a dict."""
    start = time()
    results = []

    token = get_token()

    for label in labels:
        response = get("".join((TRACK_URL, label)), headers=token)
        response_data = loads(response.text)["data"]
        if response_data == NOSCAN:
            data = {
                "courierNo": None,
                "description": "This parcel was never scanned.",
                "franchiseCode": "UNK",
                "franchiseName": "Unknown",
                "labelNo": label,
                "scanType": "N",
                "scanTypeDescription": "No scan",
                "scannedDateTime": None,
                "status": "NSC"
            }
            response_data.append(data)
        results.append(sort_keys(response_data[-1]))

    curr_date = datetime.now().isoformat()
    token_id = token["Authorization"][-4:]
    duration = round(time() - start, 2)
    records = len(results)

    return {
        "results": results,
        "datetime": curr_date,
        "token_id": str(token_id),
        "duration": str(duration),
        "records": str(records),
    }

def print_results(response):
    """Print tracking API results for each label in response."""
    counter = 0
    for item in response["results"]:
        print(dumps(item, indent=4, sort_keys=True))
        print(" ".join(("Record", str(counter + 1), "of", response["records"])))
        print(" ".join(("Fetched with access token:", response["token_id"])))
        print(" ".join(("Fetched in", str(response["duration"]), "seconds")))
        input("Press [ENTER] to continue: ")
        counter = counter + 1
        system(CLEAR)

def write_results(response, file=RESULTS_FILE):
    """Write tracking API results for labels into /track/results.csv."""
    with open(file, "w", newline="") as file:
        csv_writer = writer(file)

        headers = response["results"][0].keys()
        csv_writer.writerow(headers)

        for item in response["results"]:
            csv_writer.writerow(item.values())

    response.pop("results", None)
    response["records"] = " ".join(("Fetched ", response["records"], "records"))
    response["token_id"] = " ".join(("Fetched with access token:", response["token_id"]))
    response["duration"] = " ".join(("Fetched in", str(response["duration"]), "seconds"))

    with open(LOG_FILE, "a", newline="\n") as file:
        dump(response, file, indent=4)
        file.write("\n")

def main():
    """Main function of the program."""
    system(CLEAR)

    labels = get_labels()
    response = track_items(labels)

    write_results(response)

    system(CLEAR)

# Execute the main function.
if __name__ == "__main__":
    main()
