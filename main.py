import math
import sqlite3
import Algofox
import FyresIntegration
import time
import traceback
import pandas as pd
from pathlib import Path
import pyotp
from Algofox import *
from datetime import datetime, timedelta, timezone
from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta
result_dict = {}
# optionsymbol = f"NSE:{params['Symbol']}{params['TradeExpiery']}22400CE"

from datetime import datetime, timedelta
def fetchcorrectstrike(strikelist):
    target_value = 0.6
    closest_key = None
    min_difference = float('inf')

    for key, value in strikelist.items():
        if value > target_value and value - target_value < min_difference:
            min_difference = value - target_value
            closest_key = key

    return closest_key
def convert_date_to_short_format(date_string):
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    # Format the datetime object into the desired short format
    short_format = date_obj.strftime("%y%b").upper()  # Convert to uppercase
    return short_format
def convert_julian_date(julian_date):
    input_format = "%y%m%d"
    parsed_date = datetime.strptime(str(julian_date), input_format)

    # Add the desired time (15:30:00) to the parsed date
    desired_time = "15:30:00"
    formatted_date_with_time = parsed_date.replace(hour=15, minute=30, second=0)

    return formatted_date_with_time


def get_delta(strikeltp,underlyingprice,strike,timeexpiery,riskfreeinterest,flag):
    from py_vollib.black_scholes.greeks.analytical import delta
    iv= implied_volatility(price=strikeltp,S=underlyingprice,K=strike,t=timeexpiery,r=riskfreeinterest,flag=flag)
    value = delta(flag,underlyingprice,strike,timeexpiery,riskfreeinterest,iv)
    print("delta",value)
    return value

def option_delta_calculation(symbol,expiery,strike,optiontype,underlyingprice,MODE):
    optionsymbol = f"NSE:{symbol}{expiery}{strike}{optiontype}"
    optionltp= FyresIntegration.get_ltp(optionsymbol)
    print("expiery: ",expiery)
    if MODE=="WEEKLY":
        distanceexp=convert_julian_date(expiery)
    if MODE=="MONTHLY":
        distanceexp=expiery
    print("distanceexp: ",distanceexp)
    t= (distanceexp-datetime.now())/timedelta(days=1)/365
    print("t: ",t)
    if optiontype=="CE":
        fg="c"
    else :
        fg = "p"
    print("optionltp: ",optionltp)
    print("underlyingprice: ", underlyingprice)
    print("strike: ", strike)
    value=get_delta(strikeltp=optionltp, underlyingprice=underlyingprice, strike=strike, timeexpiery=t,flag=fg ,riskfreeinterest=0.1)
    return value

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

def getstrikes_call(ltp, step , strikestep):
    result = {}
    result[int(ltp)] = None

    for i in range(step):
        result[int(ltp + strikestep * (i + 1))] = None
    return result

def getstrikes_put(ltp, step , strikestep):
    result = {}
    result[int(ltp)] = None
    for i in range(step):
        result[int(ltp - strikestep * (i + 1))] = None

    return result


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
                "lotsize": float(row['lotsize']),
                "STOPLOSS": float(row['STOPLOSS']),
                "BREAKEVEN": float(row['BREAKEVEN']),
                "NO_TARGET": float(row['NO_TARGET']),
                "NO_STOPLOSS": float(row['NO_TARGET']),
                "NO_BREAKEVEN": float(row['NO_BREAKEVEN']),
                "TradeExpiery":row['TradeExpiery'],
                "strikestep": int(row['strikestep']),
                "NumberOfstrike": int(row['NumberOfstrike']),
                'strategytag': row['strategytag'],
                "USEEXPIERY":row['USEEXPIERY'],
                'ep':None,
                'tgtcount': 0,
                'slcount': 0,
                'breakcount':0,
                'AlgoFoxSymbol':None,
                'OptionSymbol':None,
                'call_signal':False,
                'put_signal': False,
                'breakeven_value': False,
                'stoploss_value': False,
                'target_value': False,
                'TradeActive':None,
                'pattern':None,
                "runtime": datetime.now(),
                "cool": row['Sync'],
                "sp_current": None,
                "sp_previous": None,
                "rsi_current": None,
                "rsi_previous": None,
                "high":None,
                "low":None,
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

    return buy_price


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


def round_down_to_interval(dt, interval_minutes):
    remainder = dt.minute % interval_minutes
    minutes_to_current_boundary = remainder

    rounded_dt = dt - timedelta(minutes=minutes_to_current_boundary)

    rounded_dt = rounded_dt.replace(second=0, microsecond=0)

    return rounded_dt
def determine_min(minstr):
    min=0
    if minstr =="minute":
        min=1
    if minstr =="5minute":
        min=5
    if minstr =="15minute":
        min=15
    if minstr =="30minute":
        min=30

    return min



def main_strategy():
    global result_dict
    buyprice=0
    username = credentials_dict.get('algofoxusername')
    password = credentials_dict.get('algofoxpassword')
    role = credentials_dict.get('ROLE')
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
                print(FyresIntegration.get_ltp(formatedsymbol))
                if datetime.now() >= params["runtime"]:
                    try:
                        if params["cool"] == True :
                            time.sleep(1)
                            data= FyresIntegration.fetchOHLC(symbol=formatedsymbol,rsi_period=params['RSI_Period']
                                                             ,supertrend_period=params['SP_Period'],
                                                             supertrend_multiplier=params['SP_MULTIPLIER'])

                            params["sp_current"]= data.iloc[-2]['Supertrend Signal']
                            params["sp_previous"]= data.iloc[-3]['Supertrend Signal']
                            params["rsi_current"]= data.iloc[-2]['rsi']
                            params["rsi_previous"]= data.iloc[-3]['rsi']
                            params["high"]=data.iloc[-2]['high']
                            params["low"]=data.iloc[-2]['low']
                            print("Candle time_value: ", data.iloc[-1]["date"])
                            next_specific_part_time = datetime.now() + timedelta(
                                seconds=determine_min("minute") * 60)
                            next_specific_part_time = round_down_to_interval(next_specific_part_time,
                                                                             determine_min("minute"))
                            print("Next datafetch time = ", next_specific_part_time)
                            params['runtime'] = next_specific_part_time

                    except Exception as e:
                        print("Error happened in Histry data fetching  strategy loop: ", str(e))

                ltp = FyresIntegration.get_ltp(formatedsymbol)
                high= params["high"]
                low= params["low"]
                print("ltp: ", ltp)
                print("high: ",high)
                print("low: ", low)
                print("buyprice: ", buyprice)
                print("params['pattern']:",params['pattern'])
                print("params['TradeActive']:", params['TradeActive'])
                sp_current = params["sp_current"]
                sp_previous = params["sp_previous"]
                rsi_current = params["rsi_current"]
                rsi_previous = params["rsi_previous"]
                print("sp_current: ", sp_current)
                print("sp_previous: ", sp_previous)
                print("rsi_current: ", rsi_current)
                print("rsi_previous: ", rsi_previous)



            if  (
                    params['slcount']<=params["NO_STOPLOSS"] and
                    params['tgtcount']<=params["NO_TARGET"] and
                    params['breakcount']<=params["NO_BREAKEVEN"] and
                    sp_previous == 1 and sp_current == 1 and rsi_previous < params['RSI_LEVEL']
                    and rsi_current >  params['RSI_LEVEL'] and
                    params['call_signal']==False
            ):

                params['call_signal']= True
                params['put_signal']= False
                buyprice=callSticky(high)
                params['pattern'] = "CALL"
                params['ep'] = high
                params['breakeven_value']= high+params['BREAKEVEN']
                params['stoploss_value']= high-params['STOPLOSS']
                params['target_value']= high+ params['TARGET']
                orderlog=f"{timestamp} Call signal Genarated  {formatedsymbol},@ {buyprice} candle high {high}, Target = {params['target_value']}, Stoploss= {params['stoploss_value']}, Breakeven={params['breakeven_value']} "
                write_to_order_logs(orderlog)
                print(orderlog)


            if (
                    params['slcount']<=params["NO_STOPLOSS"] and
                    params['tgtcount']<=params["NO_TARGET"] and
                    params['breakcount']<=params["NO_BREAKEVEN"] and
                    sp_previous == -1 and sp_current == -1 and rsi_previous >  params['RSI_LEVEL'] and
                    rsi_current <  params['RSI_LEVEL'] and
                    params['put_signal']==False
            ):
                params['call_signal']= False
                params['put_signal']= True
                buyprice = putSticky(low)
                params['pattern']= "PUT"
                params['ep'] = low

                params['breakeven_value']= low - params['BREAKEVEN']
                params['stoploss_value']= low + params['STOPLOSS']
                params['target_value']= low - params['TARGET']
                orderlog = f"{timestamp} Put signal Genarated  {formatedsymbol},@ {buyprice} candle high {high}, Target = {params['target_value']}, Stoploss= {params['stoploss_value']}, Breakeven={params['breakeven_value']} "
                write_to_order_logs(orderlog)
                print(orderlog)


            if params['pattern']== "PUT":
                if ltp <= buyprice and buyprice>0 and params['put_signal']== True  and params['TradeActive']==None:
                    orderlog = f"{timestamp}  Put trade triggered wait for execution"
                    write_to_order_logs(orderlog)
                    print(orderlog)
                    strikelist = getstrikes_put(ltp=custom_round(price=ltp, symbol=symbol), step=params['NumberOfstrike'], strikestep=params['strikestep'])
                    for strike in strikelist:
                        delta = float(
                            option_delta_calculation(symbol=symbol, expiery=params['TradeExpiery'], strike=strike, optiontype="PE",
                                                     underlyingprice=ltp,MODE=params["USEEXPIERY"]))
                        strikelist[strike] = delta

                    print(strikelist)

                    strike=fetchcorrectstrike(strikelist)
                    if params["USEEXPIERY"] == "WEEKLY":
                        optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{strike}PE"
                    if params["USEEXPIERY"] == "MONTHLY":
                        optionsymbol = f"NSE:{symbol}{convert_date_to_short_format(params['TradeExpiery'])}{strike}PE"

                    # optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{strike}PE"
                    params['OptionSymbol'] =optionsymbol
                    optionltp = FyresIntegration.get_ltp(optionsymbol)
                    algofoxsymbol=f"{symbol}|{convert_julian_date(params['TradeExpiery'])}|{strike}|PE"
                    params['AlgoFoxSymbol'] = algofoxsymbol
                    Algofox.Buy_order_algofox(symbol=algofoxsymbol,quantity=params["lotsize"],instrumentType="OPTIDX",
                                              direction="BUY",product="MIS",strategy=params["strategytag"],order_typ="MARKET",price=optionltp,username=username,password=password,role=role,signal=signal)



                    params['TradeActive']= "PUTTRADEACTIVE"
                    put_trade = True  # in  put trade
                    orderlog = f"{timestamp}  Put trade executed @ {ltp} @ {params['OptionSymbol']}"
                    write_to_order_logs(orderlog)
                    print(orderlog)


                elif (rsi_current > 50 or sp_current == 1) and params['put_signal']== True:
                    params['put_signal'] = False
                    orderlog = f"{timestamp}  Put signal canceled {params['OptionSymbol']}"
                    write_to_order_logs(orderlog)
                    print(orderlog)

            if params['pattern'] == "CALL":
                if ltp >= buyprice and buyprice>0 and params['call_signal']== True  and params['TradeActive']==None:
                    orderlog = f"{timestamp}  Call trade triggered wait for execution"
                    write_to_order_logs(orderlog)
                    print(orderlog)
                    params['TradeActive'] = "CALLTRADEACTIVE"
                    strikelist = getstrikes_call(ltp=custom_round(price=ltp, symbol=symbol), step=params['NumberOfstrike'],
                                            strikestep=params['strikestep'])
                    for strike in strikelist:
                        delta = float(
                            option_delta_calculation(symbol=symbol, expiery=params['TradeExpiery'], strike=strike,
                                                     optiontype="CE",
                                                     underlyingprice=ltp,MODE=params["USEEXPIERY"]))
                        strikelist[strike] = delta

                    print(strikelist)
                    strike = fetchcorrectstrike(strikelist)
                    if params["USEEXPIERY"] == "WEEKLY":
                        optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{strike}CE"
                    if params["USEEXPIERY"] == "MONTHLY":
                        optionsymbol = f"NSE:{symbol}{convert_date_to_short_format(params['TradeExpiery'])}{strike}CE"
                    # optionsymbol = f"NSE:{symbol}{params['TradeExpiery']}{strike}CE"
                    optionltp = FyresIntegration.get_ltp(optionsymbol)
                    params['OptionSymbol'] = optionsymbol

                    algofoxsymbol = f"{symbol}|{convert_julian_date(params['TradeExpiery'])}|{strike}|CE"
                    params['AlgoFoxSymbol']= algofoxsymbol
                    Algofox.Buy_order_algofox(symbol=algofoxsymbol, quantity=params["lotsize"], instrumentType="OPTIDX",
                                              direction="BUY", product="MIS", strategy=params["strategytag"],
                                              order_typ="MARKET", price=optionltp, username=username, password=password,
                                              role=role, signal=signal)

                    call_trade = True  # in buy trade
                    orderlog = f"{timestamp}  Call trade executed @ {ltp} @ {params['OptionSymbol']}"
                    write_to_order_logs(orderlog)
                    print(orderlog)

                elif (rsi_current < 50 or sp_current == -1) and params['call_signal']== True:
                    params['call_signal'] = False
                    orderlog = f"{timestamp} Call signal canceled {params['OptionSymbol']}"
                    write_to_order_logs(orderlog)
                    print(orderlog)

            if params['TradeActive']== "PUTTRADEACTIVE" and params['put_signal']== True:
                if ltp<=params['breakeven_value'] and params['breakeven_value']>=0:
                    params['breakeven_value']=0
                    params['breakcount']=params['breakcount']+1
                    params['stoploss_value']=params['ep']
                    orderlog = f"{timestamp} Breakeven executed @ {ltp} @  {params['OptionSymbol']}"
                    write_to_order_logs(orderlog)
                    print(orderlog)

                if ltp<=params['target_value'] and params['target_value']>=0:
                    params['target_value']=0
                    params['put_signal'] = False
                    params['tgtcount'] = params['tgtcount'] + 1
                    orderlog = f"{timestamp} Target executed @ {ltp} @{params['OptionSymbol']}"
                    optionltp = FyresIntegration.get_ltp(params['OptionSymbol'] )
                    Algofox.Sell_order_algofox(symbol=params['AlgoFoxSymbol'], quantity=params["lotsize"], instrumentType="OPTIDX",
                                              direction="SELL", product="MIS", strategy=params["strategytag"],
                                              order_typ="MARKET", price=optionltp, username=username, password=password,
                                              role=role, signal=signal)
                    write_to_order_logs(orderlog)
                    print(orderlog)

                if ltp>=params['stoploss_value'] and params['stoploss_value']>=0:
                    params['stoploss_value']=0
                    params['put_signal'] = False
                    params['slcount'] = params['slcount'] + 1
                    orderlog = f"{timestamp} Stoploss executed @ {ltp} @{params['OptionSymbol']}"
                    optionltp = FyresIntegration.get_ltp(params['OptionSymbol'])
                    Algofox.Sell_order_algofox(symbol=params['AlgoFoxSymbol'], quantity=params["lotsize"],
                                               instrumentType="OPTIDX",
                                               direction="SELL", product="MIS", strategy=params["strategytag"],
                                               order_typ="MARKET", price=optionltp, username=username,
                                               password=password,
                                               role=role, signal=signal)
                    write_to_order_logs(orderlog)
                    print(orderlog)

            if params['TradeActive'] == "CALLTRADEACTIVE" and params['call_signal'] == True:
                if ltp >= params['breakeven_value'] and params['breakeven_value'] >= 0:
                    params['breakeven_value'] = 0
                    params['breakcount'] = params['breakcount'] + 1
                    params['stoploss_value'] = params['ep']
                    orderlog = f"{timestamp} Breakeven executed @ {ltp}  @{params['OptionSymbol']}"
                    write_to_order_logs(orderlog)
                    print(orderlog)

                if ltp >= params['target_value'] and params['target_value'] >= 0:
                    params['target_value'] = 0
                    params['call_signal']=False
                    params['tgtcount'] = params['tgtcount'] + 1
                    orderlog = f" {timestamp} Target executed @ {ltp} @{params['OptionSymbol']}"
                    optionltp = FyresIntegration.get_ltp(params['OptionSymbol'])
                    Algofox.Sell_order_algofox(symbol=params['AlgoFoxSymbol'], quantity=params["lotsize"],
                                               instrumentType="OPTIDX",
                                               direction="SELL", product="MIS", strategy=params["strategytag"],
                                               order_typ="MARKET", price=optionltp, username=username,
                                               password=password,
                                               role=role, signal=signal)
                    write_to_order_logs(orderlog)
                    print(orderlog)

                if ltp <= params['stoploss_value'] and params['stoploss_value'] >= 0:
                    params['stoploss_value'] = 0
                    params['call_signal'] = False
                    params['slcount'] = params['slcount'] + 1
                    orderlog = f"{timestamp} Stoploss executed @ {ltp} @{params['OptionSymbol']}"
                    optionltp = FyresIntegration.get_ltp(params['OptionSymbol'])
                    Algofox.Sell_order_algofox(symbol=params['AlgoFoxSymbol'], quantity=params["lotsize"],
                                               instrumentType="OPTIDX",
                                               direction="SELL", product="MIS", strategy=params["strategytag"],
                                               order_typ="MARKET", price=optionltp, username=username,
                                               password=password,
                                               role=role, signal=signal)
                    write_to_order_logs(orderlog)
                    print(orderlog)

    except Exception as e:
        print("Error happened in Main strategy loop: ", str(e))
        traceback.print_exc()



while True:
    main_strategy()
    time.sleep(1)


