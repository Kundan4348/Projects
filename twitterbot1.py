from http import client
from turtle import clear
import requests
import os
import json
import config
import preprocessor as p
from langdetect import detect
from csv import writer
from ernie import SentenceClassifier
import numpy as np
from binance.client import Client
from binance.enums import *

classifier = SentenceClassifier(model_path='./output')
client = Client(config.BINANCE_KEY, config.BINANCE_SECRET)

TRADE_SYMBOL = "BTCUSDT"
TRADE_QUANTITY = 0.001
in_position = np.False_
sentimentList = []
neededSentiments = 300

in_pos = 0
a = 25
b = 100

def Average(lst):
    if len(lst) == 0:
        return len(lst)
    else:
        return sum(lst[-neededSentiments: ])/ neededSentiments

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("Sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print(e)
        return False
    return True
# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = config.BEARER_TOKEN


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FilteredStreamPython"
    return r

  
def get_rules():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", auth=bearer_oauth
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def set_rules(delete):
    # You can adjust the rules if needed
    sample_rules = [
        {"value": "#bitcoin", "tag": "bitcoin"},
        # {"value": "cat has:images -grumpy", "tag": "cat pictures"},
    ]
    payload = {"add": sample_rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        auth=bearer_oauth,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))

in_pos = 0
def get_stream():
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream", auth=bearer_oauth, stream=True,
    )
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            # print(json.dumps(json_response, indent=4, sort_keys=True))
            tweet = json_response['data']['text']
            tweet = p.clean(tweet)
            tweet = tweet.replace(':','')

            try:
                if detect(tweet) == 'en':
                    print(tweet)
            except:
                pass

            try:
                        # -1 Bearish/Negative 0 Neutral 1 Bullish/Positive
                        classes = ["Bearish","Neutral","Bullish"]
                        probabilities = classifier.predict_one(tweet)
                        polarity = classes[np.argmax(probabilities)]
                        sentimentList.append(polarity)

                        if len(sentimentList) > 50:
                            endList = sentimentList[-50:]
                            print('** TOTAL BULLISH: '+ str(endList.count('Bullish')))
                            print('** TOTAL BEARISH: '+ str(endList.count('Bearish')))
                            countbullish = endList.count('Bullish')
                            countbearish = endList.count('Bearish')
                            if countbullish >= 15:
                                #BUY 
                                # print('************************************** HERE')
                                print(a)
                                if in_position:
                                    print('****************************** BUY!!! BUT WE OWN **********')
                                else:
                                    print('****************************** BUY!!! **********')
                                    print(b)
                                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                                    if order_succeeded:
                                       in_position = True

                            elif countbearish >= 15:
                                #SELL
                                if in_position:
                                    print('****************************** SELL!!!! **********')
                                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                                    if order_succeeded:
                                        in_position = False                                   
                                else:
                                    print('****************************** SELL!! BUT WE DONT OWN **********')
            except:
                pass

                    #  tweetLst = [tweet]
                    #  with open('bitcoindata.csv','a+', newline='') as write_obj:
                    #      csv_writer = writer(write_obj)
                    #      csv_writer.writerow(tweetLst)
def main():
    rules = get_rules()
    delete = delete_all_rules(rules)
    set = set_rules(delete)
    get_stream(set)


if __name__ == "__main__":
    main()