'''
Upload command: 
    'python upload.py -d supplier'
    'python upload.py -d product'
    'python upload.py -d warehouse'
    'python upload.py -d customer'

1. Upload supplier data first before uploading product data.
2. Upload warehouse data first before uploading customer data.
'''
import json
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-d',
    help='Define the data: "supplier"/"product"/"customer"/"warehouse"', 
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


if args.d == "supplier":
    send_post_request("suppliers")
elif args.d == "product":
    send_post_request("products")
elif args.d == "customer":
    send_post_request("customers")
elif args.d == "warehouse":
    send_post_request("warehouses")
