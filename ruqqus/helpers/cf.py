from collections import deque
import requests
import time
import redis
from os import environ
from flask import request
from ruqqus.__main__ import app

CF_KEY = environ.get("CLOUDFLARE_KEY").lstrip().rstrip()
CF_ZONE = environ.get("CLOUDFLARE_ZONE").lstrip().rstrip()
recent_reqs=deque([],200)



headers = {
    "Authorization": f"Bearer {CF_KEY}",
    "Content-Type": "application/json"
    }

url=f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/settings/security_level"




r=redis.Redis(host=app.config["CACHE_REDIS_URL"][8:], decode_responses=True, ssl_cert_reqs=None)

config={}
config['UNDER_ATTACK']=int(r.get("under_attack")) or 0
config['TIMEOUT_STAMP']=int(r.get("timeout_stamp")) or 0

config['COUNTER']=0

ip_list={}

def site_performance(t):

    config['COUNTER']+=1

    #every 100 requests update status from shared cache
    if not config['COUNTER']%100:
        config['UNDER_ATTACK']=int(r.get("under_attack")) or 0
        config['TIMEOUT_STAMP']=int(r.get("timeout_stamp")) or 0


    recent_reqs.append(t)

    if not config['UNDER_ATTACK'] and len(recent_reqs)>=20:
        avg=sum(recent_reqs)/len(recent_reqs)

        if avg>=0.45:

            try:
                print("turning on UA mode")
            except:
                pass

            data={"value":"under_attack"}
            x=requests.patch(url, headers=headers, json=data)
            #print(x.json())

            if x.status_code<300:
                r.set("under_attack",1)
                config['UNDER_ATTACK']=1
                ts=int(time.time())+3600
                r.set("timeout_stamp", ts)
                config['TIMEOUT_STAMP']=ts

    elif config['UNDER_ATTACK']==1:

        if request.remote_addr in ip_list:
            ip_list[request.remote_addr]+=1
            if ip_list[request.remote_addr]>=10:
                print(request.remote_addr)
                ip_list.pop(request.remote_addr)
        else:
            ip_list[request.remote_addr]=1



        if time.time()>config['TIMEOUT_STAMP']:

            try:
                print("turning off UA mode")
            except:
                pass

            data={"value":"high"}
            x=requests.patch(url, headers=headers, json=data)

            if x.status_code<300:
                r.set("under_attack",0)
                config['UNDER_ATTACK']=0
            else:
                try:
                    print(x.json())
                except:
                    pass


