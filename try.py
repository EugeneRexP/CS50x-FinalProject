# -*- coding: utf-8 -*-
from pyoxr import OXRClient

if __name__ == "__main__":
    oxr_cli = OXRClient(app_id="281e3d3bb93840828f7da169c7279b65")
    # rates = oxr_cli.get_latest()['rates']
    # PHP = result['USD']
    # print(PHP)
    # x = 'banana'
    
    # if x in rates.keys():
    #     print(x)
    # else:
    #     print("no")
    
    currencies = oxr_cli.get_currencies()
    print(currencies)
        
