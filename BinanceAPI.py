# -*- coding: utf-8 -*
import requests, time, hmac, hashlib,json,os
from app.authorization import dingding_token, recv_window,api_secret,api_key
import ssl

# from app.dingding import Message
# linux
#data_path = os.getcwd()+"/data/data.json"
# windows
data_path = os.getcwd() + "\data\data.json"
try:
    from urllib import urlencode
# python3
except ImportError:
    from urllib.parse import urlencode
requests.adapters.DEFAULT_RETRIES=5
requests.packages.urllib3.disable_warnings()
s = requests.session()
s.keep_alive = False


class BinanceAPI(object):
    BASE_URL = "https://www.binance.com/api/v1"
    FUTURE_URL = "https://fapi.binance.com"
    BASE_URL_V3 = "https://api.binance.com/api/v3"
    PUBLIC_URL = "https://www.binance.com/exchange/public/product"

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def ping(self):
        path = "%s/ping" % self.BASE_URL_V3
        with requests.get(path, timeout=180, verify=False, stream=True) as re:
            res=re.json()
        #return requests.get(path, timeout=180, verify=False).json()
        return res

    def get_ticker_price(self,market,rotate_count=0):
        path = "%s/ticker/price" % self.BASE_URL_V3
        params = {"symbol":market}
        res =  self._get_no_sign(path,params)
        while res == 443 : 
            rotate_count += 1
            time.sleep(20)
            self.get_ticker_price(market,rotate_count)
        time.sleep(2)
        #print("res:    ",res)
        #print("res['price']:    ",res['price'])
        return float(res['price'])

    def get_ticker_24hour(self,market):
        path = "%s/ticker/24hr" % self.BASE_URL_V3
        params = {"symbol":market}
        res =  self._get_no_sign(path,params)
        return res

    def get_klines(self, market, interval, limit,startTime=None, endTime=None,rotate_count = 0):
        path = "%s/klines" % self.BASE_URL
        params = None
        #if startTime is None:
        params = {"symbol": market, "interval":interval, "limit":limit}
        #else:
        #    params = {"symbol": market,"limit":limit, "interval":interval, "startTime":startTime, "endTime":endTime}
        #print("params",params)
        res =  self._get_no_sign(path, params)
        while res == 443 and rotate_count<4: 
            rotate_count += 1
            time.sleep(600)
            self.get_klines(market, interval, limit,rotate_count)
        time.sleep(2)
        return res

    def buy_limit(self, market, quantity, rate):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "BUY", rate)
        return self._post(path, params)

    def sell_limit(self, market, quantity, rate):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "SELL", rate)
        return self._post(path, params)

    def buy_market(self, market, quantity):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "BUY")
        return self._post(path, params)

    def sell_market(self, market, quantity):
        path = "%s/order" % self.BASE_URL_V3
        params = self._order(market, quantity, "SELL")
        return self._post(path, params)
    
    def get_ticker_24hour(self,market):
        path = "%s/ticker/24hr" % self.BASE_URL
        params = {"symbol":market}
        res =  self._get_no_sign(path,params)
        return round(float(res['priceChangePercent']),1)
    
    def get_positionInfo(self, symbol):
        
        path = "%s/positionRisk" % self.BASE_URL
        params = {"symbol":symbol}
        time.sleep(1)
        return self._get(path, params)

    def get_future_positionInfo(self, symbol):
        
        path = "%s/fapi/v2/positionRisk" % self.FUTURE_URL
        params = {"symbol":symbol}
        res = self._get(path, params)
        print(res)
        return res

    def dingding_warn(self,text):
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        api_url = "https://oapi.dingtalk.com/robot/send?access_token=%s" % dingding_token
        json_text = json_text = {
            "msgtype": "text",
            "at": {
                "atMobiles": [
                    "11111"
                ],
                "isAtAll": False
            },
            "text": {
                "content": text
            }
        }
        requests.post(api_url, json.dumps(json_text), headers=headers,verify=False).content
    def get_cointype(self):
        
        tmp_json = {}
        with open(data_path, 'r') as f:
            tmp_json = json.load(f)
            f.close()
        return tmp_json["config"]["cointype"]
    
    def _order(self, market, quantity, side, price=None):
        '''
        :param market:BTCUSDT???ETHUSDT
        :param quantity: 
        :param side: 
        :param price: 
        :return:
        '''
        params = {}

        if price is not None:
            params["type"] = "LIMIT"
            params["price"] = self._format(price)
            params["timeInForce"] = "GTC"
        else:
            params["type"] = "MARKET"

        params["symbol"] = market
        params["side"] = side
        params["quantity"] = '%.8f' % quantity

        return params

    def _get(self, path, params={}):
        params.update({"recvWindow": recv_window}) 
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.key,'Connection': 'close'}
        requests.packages.urllib3.disable_warnings()
        #res = requests.get(url, headers=header,timeout=30, verify=False).json()
        with requests.get(url, timeout=30, verify=False, stream=True) as re:
            res=re.json()
        if isinstance(res,dict):
            if 'code' in res:
                error_info = "{info}".format(info=str(res))
                self.dingding_warn(error_info)
        return res

    def _get_no_sign(self, path, params={}):
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        s = requests.session()
        s.keep_alive = False
        requests.adapters.DEFAULT_RETRIES=5
        #res = requests.get(url, timeout=10, verify=False).json()
        with requests.get(url, timeout=10, verify=False, stream=True) as re:
            res=re.json()
        #requests.session.close()
        return res

    def _sign(self, params={}):
        data = params.copy()

        ts = int(1000 * time.time())
        data.update({"timestamp": ts})
        h = urlencode(data)
        b = bytearray()
        b.extend(self.secret.encode())
        signature = hmac.new(b, msg=h.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        data.update({"signature": signature})
        return data

    def _post(self, path, params={}):
        params.update({"recvWindow": recv_window})
        query = self._sign(params)
        url = "%s" % (path)
        header = {"X-MBX-APIKEY": self.key,'Connection': 'close'}
        res = requests.post(url, headers=header, data=query, timeout=180, verify=False).json()

        if isinstance(res,dict):
            if 'code' in res:
                error_info = "{info}".format( info=str(res))
                self.dingding_warn(error_info)

        return res

    def _format(self, price):
        return "{:.8f}".format(price)

if __name__ == "__main__":
    instance = BinanceAPI(api_key,api_secret)
    # print(instance.buy_limit("EOSUSDT",5,2))
    # print(instance.get_ticker_price("WINGUSDT"))
    print(instance.get_ticker_24hour("WINGUSDT"))
