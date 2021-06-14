'''
Upload command: 'python upload.py -d transaction'
'''
import json
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d',
    help='Define the argument: "transaction"', 
    required=True)
args = parser.parse_args()


def send_post_request(entity):
    url = f"http://127.0.0.1:5000/{entity}"
    with open(f"{entity}.json", "r") as read_file:
        json_data = json.load(read_file)

        for el in json_data:
            print(el)
            x = requests.post(url, json = el)
            print('status code:', x.status_code)
            print('Response:',  x.content)


if args.d == "transaction":
    send_post_request("customertransactions")
