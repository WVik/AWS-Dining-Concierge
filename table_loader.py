import requests
import json
import random
import time
import boto3
import datetime

x = datetime.datetime.now()

#print(x)
import json
#data=[]
#for line in open('data.json', 'r'):
#    data.append(json.loads(line))

#print(data)
def insert_data(data_list, db=None, table='yelp-diners'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    for data in data_list:
        data['insertedAtTimestamp']=str(x)
        response = table.put_item(Item=data)
        time.sleep(0.5)
    print('@insert_data: response', response)
    return response


with open("rest_final.json",'r') as f:
     #for d in data:
    data=json.load(f)

