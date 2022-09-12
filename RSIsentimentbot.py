import praw
import config
from textblob import TextBlob
from binance.client import Client
from binance.enums import *
import config
from ta.momentum import RSIIndicator
import pandas as pd

#Order Function
def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print('sending order')
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print('an exception has occured - {}'.format(e))
        return False
    return True

#Connect to API
#info = client.get_account()
#print(info)
reddit = praw.Reddit(
    client_id=config.REDDIT_ID,
    client_secret=config.REDDIT_SECRET,
    password=config.REDDIT_PASS,
    user_agent="USERAGENT",
    username=config.REDDIT_USER,
)
client = Client(config.BINANCE_KEY, config.BINANCE_SECRET)

#Variables for Bot
lst = []
dogePrices = []
neededSentiments = 300
TRADE_SYMBOL = 'DOGEUSDT'
TRADE_QUANTITY = 100
in_position = False
UPPER_BAND = 70
LOWER_BAND = 30

def Average(lst):
    if len(lst) == 0:
        return len(lst)
    else:
        return sum(lst[-neededSentiments:]) / neededSentiments


#Connect to Reddit Stream for comments
#print(reddit)
for comment in reddit.subreddit("Gold").stream.comments():
    #print(comment.body)
    redditComment = comment.body
    blob = TextBlob(redditComment)
    #print(blob.sentiment)
    sent = blob.sentiment

    # print(redditComment)

    # print(" ******* Sentiment is: "+ str(sent.polarity))

    if sent.polarity != 0.0:
        lst.append(sent.polarity)
        avg = round(Average(lst), 2)
        #print("********** TOTAL SENTIMENT OF LIST IS: **********" + str())
        # print(" ********** Total Sentiment is currently: "+str(round(Average(lst), 4)) + " and there are " + str(len(lst)) + " elements")

        candles = client.get_historical_klines(TRADE_SYMBOL, Client.KLINE_INTERVAL_5MINUTE, "5 Minutes ago UTC")
        # print(candles[-1][1])
       
        if len(dogePrices) == 0:
            dogePrices.append(float(candles[-1][1]))
        elif dogePrices[-1] != float(candles[-1][1]):
            dogePrices.append(float(candles[-1][1]))

        # print(" *********** Length of Prices list is: " +  str(len(dogePrices)))

        rsi = RSIIndicator(pd.Series(dogePrices))
        df = rsi.rsi()
        print(rsi.rsi())

        df.iloc[-1]

        if(df.iloc[-1] < LOWER_BAND and round(Average(lst)) > 0.5 and len(lst) > neededSentiments):
            if in_position:
                print(" ********** BUY ******** BUT WE OWN!! ********")
            else: 
                print(" ********** BUY ORDER ********")
                # order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                #if order_succeeded:
                in_position = True
        elif(df.iloc[-1] > UPPER_BAND and Average(lst) < -0.5 and len(lst) > neededSentiments):
            if in_position:
                # order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                #if order_succeeded:
                in_position = False
            else:
                print('********** SELL ORDER *********** BUT WE DONT OWN **********')
