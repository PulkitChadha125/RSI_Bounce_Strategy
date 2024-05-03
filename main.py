import math
import sqlite3

import FyresIntegration
import time
import traceback
import pandas as pd
from pathlib import Path
import pyotp
from Algofox import *
from datetime import datetime, timedelta, timezone
result_dict = {}



def custom_round(price, symbol):
    rounded_price = None
    if symbol == "NIFTY":
        last_two_digits = price % 100
        if last_two_digits < 25:
            rounded_price = (price // 100) * 100
        elif last_two_digits < 75:
            rounded_price = (price // 100) * 100 + 50
        else:
            rounded_price = (price // 100 + 1) * 100
            return rounded_price

    elif symbol == "BANKNIFTY":
        last_two_digits = price % 100
        if last_two_digits < 50:
            rounded_price = (price // 100) * 100
        else:
            rounded_price = (price // 100 + 1) * 100
        return rounded_price

    else:
        pass

    return rounded_price

def write_to_order_logs(message):
    with open('OrderLog.txt', 'a') as file:  # Open the file in append mode
        file.write(message + '\n')


def delete_file_contents(file_name):
    try:
        # Open the file in write mode, which truncates it (deletes contents)
        with open(file_name, 'w') as file:
            file.truncate(0)
        print(f"Contents of {file_name} have been deleted.")
    except FileNotFoundError:
        print(f"File {file_name} not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
def get_user_settings():
    global result_dict
    try:
        csv_path = 'TradeSettings.csv'
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        result_dict = {}
        # Symbol,expiery,RSI_Period,SP_Period,SP_MULTIPLIER,RSI_LEVEL,TARGET,STOPLOSS,BREAKEVEN,NO_TARGET,NO_STOPLOSS,NO_BREAKEVEN
        for index, row in df.iterrows():
            # Create a nested dictionary for each symbol
            symbol_dict = {
                'Symbol': row['Symbol'],
                'expiery': row['expiery'],
                'RSI_Period': row['RSI_Period'],
                'SP_Period': row['SP_Period'],
                'SP_MULTIPLIER': float(row['SP_MULTIPLIER']),
                "RSI_LEVEL": float(row['RSI_LEVEL']),
                "TARGET": float(row['TARGET']),
                "STOPLOSS": float(row['STOPLOSS']),
                "BREAKEVEN": float(row['BREAKEVEN']),
                "NO_TARGET": float(row['NO_TARGET']),
                "NO_STOPLOSS": float(row['NO_TARGET']),
                "NO_BREAKEVEN": float(row['NO_BREAKEVEN']),
                'call_signal':False,
                'put_signal': False,
                'breakeven_value': False,
                'stoploss_value': False,
                'target_value': False,
                'TradeActive':None,
                'pattern':None,
            }
            result_dict[row['Symbol']] = symbol_dict
        print("result_dict: ", result_dict)
    except Exception as e:
        print("Error happened in fetching symbol", str(e))


get_user_settings()
def get_api_credentials():
    credentials = {}
    delete_file_contents("OrderLogs.txt")
    try:
        df = pd.read_csv('Credentials.csv')
        for index, row in df.iterrows():
            title = row['Title']
            value = row['Value']
            credentials[title] = value
    except pd.errors.EmptyDataError:
        print("The CSV file is empty or has no data.")
    except FileNotFoundError:
        print("The CSV file was not found.")
    except Exception as e:
        print("An error occurred while reading the CSV file:", str(e))

    return credentials


credentials_dict = get_api_credentials()
redirect_uri=credentials_dict.get('redirect_uri')
client_id=credentials_dict.get('client_id')
secret_key=credentials_dict.get('secret_key')
grant_type=credentials_dict.get('grant_type')
response_type=credentials_dict.get('response_type')
state=credentials_dict.get('state')
TOTP_KEY=credentials_dict.get('totpkey')
FY_ID=credentials_dict.get('FY_ID')
PIN=credentials_dict.get('PIN')
url = credentials_dict.get('algofoxurl')
username= credentials_dict.get('algofoxusername')
password=credentials_dict.get('algofoxpassword')
role= credentials_dict.get('ROLE')
createurl(url)
processed_order_ids = set()
loginresult=login_algpfox(username=username, password=password, role=role)

FyresIntegration.automated_login(client_id=client_id, redirect_uri=redirect_uri, secret_key=secret_key, FY_ID=FY_ID,
                                     PIN=PIN, TOTP_KEY=TOTP_KEY)


if loginresult!=200:

    print("Algofoz credential wrong, shutdown down Trde Copier, please provide correct details and run again otherwise program will not work correctly ...")
    time.sleep(10000)



def putSticky(low):
    price = math.floor(low)
    price2 = price % 100
    slcal = price
    if (3 >= price2 >= 0) or (83 >= price2 >= 80) or (63 >= price2 >= 60) or (53 >= price2 >= 50)or (33 >= price2 >= 30) or (23 >= price2 >= 20) or (12 >= price2 >= 8):
        remainder = price2 % 10
        buy_price = price - remainder
        buy_price = buy_price - 1.1
    else:
        buy_price = price - 0.10
        buy_price = price - 0.10
#
# def putSignal(buy_price):
#         """After put signal this block is responsible for taking trade or cancel signal"""
#     print("buy price = ", buy_price)
#     if ltp <= buy_price and put_signal:
#         symbole_gen_Put()
#         put_trade = True # in  put trade
#         self.send_msg("put trade Taken")
#     elif (currsi > 50 or currside == 1) and put_signal:
#         put_signal = False
#         print("signal void")


def callSticky(high):
    price = math.ceil(high)
    price2 = price % 100
    slcal = price
    if (8 <= price2 <= 12) or (97 <= price2 <= 100) or (15 <= price2 <= 20) or (27 <= price2 <= 30) or (
            47 <= price2 <= 50) or (57 <= price2 <= 60) or (77 <= price2 <= 80):
        remainder = price % 10
        if remainder == 0:
            buy_price = (price) + 1.1
        else:
            buy_price = (price + (10 - remainder)) + 1.1
    else:
        buy_price = price + 0.10

    return buy_price
#
# def callSignal():
#         """After call signal this block is responsible for taking trade or cancel signal"""
#     if ltp >= buy_price and call_signal:
#         symbole_gen_Call()
#         call_trade = True # in buy trade
#         send_msg("call trade taken")
#     elif (currsi < 50 or currside == -1) and call_signal:
#         call_signal = False
#         send_msg("signal void")



def main_strategy():
    global result_dict
    buyprice=0
    try:
        for symbol, params in result_dict.items():
            symbol_value = params['Symbol']
            timestamp = datetime.now()
            timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            if isinstance(symbol_value, str):
                date_object = datetime.strptime(params['expiery'], '%d-%b-%y')
                new_date_string = date_object.strftime('%y%b').upper()
                formatedsymbol= f"NSE:{params['Symbol']}{new_date_string}FUT"
                print(formatedsymbol)
                data= FyresIntegration.fetchOHLC(symbol=formatedsymbol,rsi_period=params['RSI_Period'] ,supertrend_period=params['SP_Period'],supertrend_multiplier=params['SP_MULTIPLIER'])
                print("data: ",data)
                # print("relevant data= ",data.iloc[-2]['date'])//current
                sp_current=data.iloc[-2]['Supertrend Signal']
                sp_previous=data.iloc[-3]['Supertrend Signal']
                rsi_current=data.iloc[-2]['rsi']
                rsi_previous=data.iloc[-3]['rsi']
                high=data.iloc[-2]['high']
                prevhigh=data.iloc[-3]['high']
                low=data.iloc[-2]['low']
                close=data.iloc[-2]['close']
                prevclose=data.iloc[-3]['close']
                prevthirdclose=data.iloc[-4]['close']
                prevlow=data.iloc[-3]['low']
                ltp="Fetch current symbol ltp task to be done"

            # callSignalGenerator

            if sp_previous == 1 and sp_current == 1 and rsi_previous < params['RSI_LEVEL'] and rsi_current >  params['RSI_LEVEL'] and params['call_signal']==False:
                params['call_signal']= True
                params['put_signal']= False
                buyprice=callSticky(high)
                params['pattern'] = "CALL"
                params['breakeven_value']= high+params['BREAKEVEN']
                params['stoploss_value']= high-params['STOPLOSS']
                params['target_value']= high+ params['TARGET']

            # putSignalGenerator
            if sp_previous == -1 and sp_current == -1 and rsi_previous >  params['RSI_LEVEL'] and rsi_current <  params['RSI_LEVEL'] and params['put_signal']==False:
                params['call_signal']= False
                params['put_signal']= True
                buyprice = putSticky(low)
                params['pattern']= "PUT"
                params['breakeven_value']= low - params['BREAKEVEN']
                params['stoploss_value']= low + params['STOPLOSS']
                params['target_value']= low - params['TARGET']


            if params['pattern']== "PUT":
                if ltp <= buyprice and buyprice>0 and params['put_signal']== True  and params['TradeActive']==None:
                    # symbole_gen_Put()
                    params['TradeActive']= "PUTTRADEACTIVE"
                    put_trade = True  # in  put trade
                    print("put trade Taken")
                elif (rsi_current > 50 or sp_current == 1) and params['put_signal']== True:
                    params['put_signal'] = False
                    print("signal void")

            if params['pattern'] == "CALL":
                if ltp >= buyprice and buyprice>0and params['call_signal']== True  and params['TradeActive']==None:
                    # symbole_gen_Call()
                    params['TradeActive'] = "CALLTRADEACTIVE"
                    call_trade = True  # in buy trade
                    print("call trade taken")
                elif (rsi_current < 50 or sp_current == -1) and params['call_signal']== True:
                    params['call_signal'] = False
                    print("signal void")

            if params['TradeActive']== "PUTTRADEACTIVE" and params['put_signal']== True:
                if ltp<=params['breakeven_value'] and params['breakeven_value']>=0:
                    params['breakeven_value']=0
                    print("Breakeven executed")

                if ltp<=params['target_value'] and params['target_value']>=0:
                    params['target_value']=0
                    params['put_signal'] = False
                    print("target executed")

                if ltp>=params['stoploss_value'] and params['stoploss_value']>=0:
                    params['stoploss_value']=0
                    params['put_signal'] = False
                    print("stoploss executed")

            if params['TradeActive'] == "CALLTRADEACTIVE" and params['call_signal'] == True:
                if ltp >= params['breakeven_value'] and params['breakeven_value'] >= 0:
                    params['breakeven_value'] = 0
                    print("Breakeven executed")

                if ltp >= params['target_value'] and params['target_value'] >= 0:
                    params['target_value'] = 0
                    params['call_signal']=False
                    print("target executed")

                if ltp <= params['stoploss_value'] and params['stoploss_value'] >= 0:
                    params['stoploss_value'] = 0
                    params['call_signal'] = False
                    print("stoploss executed")

    except Exception as e:
        print("Error happened in Main strategy loop: ", str(e))
        traceback.print_exc()

while True:
    main_strategy()


