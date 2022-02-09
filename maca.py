# -*- coding: utf-8 -*-
from app.BinanceAPI import BinanceAPI
from app.authorization import api_key,api_secret
from data.runBetData import RunBetData
from app.dingding import Message
from data.calcIndex import CalcIndex
import time
import datetime
import requests
requests.packages.urllib3.disable_warnings()




binan = BinanceAPI(api_key,api_secret)
runbet = RunBetData()
msg = Message()

class Run_Main():

    def __init__(self):
        self.coinList = runbet.get_coinList()
        pass

    def pre_data(self,cointype):

        grid_buy_price = runbet.get_buy_price(cointype)  # 
        grid_sell_price = runbet.get_sell_price(cointype)  # 
        quantity = runbet.get_quantity(cointype)  # 
        step = runbet.get_step(cointype)  # 
        cur_market_price = binan.get_ticker_price(cointype)  # 
        right_size = len(str(cur_market_price).split(".")[1])
        return [grid_buy_price,grid_sell_price,quantity,step,cur_market_price,right_size]
    def cam5(self,coinType,interval,data):
        ma5 = 0
        for i in range(len(data)):
            ma5+=float(data[i][4])
        return round(ma5/5,2)
    def cam25(self,coinType,interval,data):
        ma25 = 0
        for i in range(len(data)):
            ma25+=float(data[i][4])
        return round(ma25/25,2)
    def loop_run(self):
        print("时间：   ",datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("开始运行")
        data=binan.get_klines("NEARUSDT","15m", 25)
        cha=self.cam5("NEARUSDT","15m",data[-6:-1])-self.cam25("NEARUSDT","15m",data)
        bianhua.append(cha)
        while True:
            print("时间：   ",datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            #price=binan.get_klines("NEARUSDT", "15m", 25)[0][4]
            data=binan.get_klines("NEARUSDT","15m", 25)
            print("price",data[-1][4])
            cha=self.cam5("NEARUSDT","15m",data[-6:-1])-self.cam25("NEARUSDT","15m",data)
            bianhua.append(cha)
            if cha>0:     #短时均线高于长时均线，价格被高估
                if bianhua[-1]<bianhua[-2]:
                    time.sleep(600)
                    data=binan.get_klines("NEARUSDT","15m", 25)
                    cha=self.cam5("NEARUSDT","15m",data[-6:-1])-self.cam25("NEARUSDT","15m",data)
                    bianhua.append(cha)
                    if bianhua[-1]<bianhua[-2] :   #再次确认
                        #price=binan.get_klines("NEARUSDT", "15m", 1)[0][4]
                        sell.append(float(data[-1][4]))
            elif cha<0:    #短时均线低于长时均线，价格被低估  
                if bianhua[-1]>bianhua[-2]:
                    time.sleep(600)
                    data=binan.get_klines("NEARUSDT","15m", 25)
                    cha=self.cam5("NEARUSDT","15m",data[-6:-1])-self.cam25("NEARUSDT","15m",data)
                    bianhua.append(cha)
                    if bianhua[-1]>bianhua[-2] :   #再次确认
                        time.sleep(600)
                        #price=binan.get_klines("NEARUSDT", "15m", 1)[0][4]
                        buy.append(float(data[-1][4]))
            if len(bianhua)>5:bianhua.pop(0)
            print("变化：",bianhua)
            print("已经买了：",buy) 
            print("已经卖了：",sell)
            print("买卖的总价,买：   卖：    ",sum(buy),sum(sell)) 
            time.sleep(600)
if __name__ == "__main__":
    bianhua,buy,sell=[],[],[]
    warn_count=0
    while True:
        try:
            instance = Run_Main()
            instance.loop_run()
        except Exception as e:
            print("时间：   ",datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            warn_count+=1
            print("出错原因：",e)
            print("出错次数：",warn_count)

            time.sleep(600)

    #try:
    
    #except Exception as e:
    #    error_info = "报警：均线策略停止"
    #    msg.dingding_warn(error_info)            

            