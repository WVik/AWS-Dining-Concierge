
import requests
import json
import random
import time
import boto3
import datetime

def collect(url,headers,params,count,ids):

  
  restaurants = []
  ids_type=ids
  while len(restaurants) < count and params['offset']<1000:

    # Make a request to the API
      response = requests.get(url, headers=headers, params=params)
      data = json.loads(response.text)
      if 'businesses' not in data.keys():
        print(data)
        break
      for restaurant in data['businesses']:
        if restaurant['id'] not in ids:
          ids_type.append(restaurant['id'])
          #restaurant['cuisine']=params['term']
          neccessary_info_params=['name','review_count','rating','location','coordinates','phone','display_address','zip_code']
          neccessary_info={}
          neccessary_info['business-id']=str(restaurant['id'])
          neccessary_info['cuisine']=params['term'].split(" ")[0]
          for nec_param in neccessary_info_params:
            if nec_param in restaurant.keys():
              neccessary_info[nec_param]=str(restaurant[nec_param])
          restaurants.append(neccessary_info)
          #restaurants.append(restaurant)
    
    # Add the businesses to the list of restaurants
     # restaurants += data['businesses']
    
    # Increase the offset to get the next page of results
      params['offset'] += params['limit']
    
    # Wait for a random amount of time to avoid overloading the API
      time.sleep(random.uniform(0.5, 1.5))
  return [restaurants,ids_type]

def insert_data(data_list, db=None, table='yelp-diners'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    for data in data_list:
        response = table.put_item(Item=data)
        time.sleep(0.5)
    print('@insert_data: response', response)
    return response

def yelp():
    #print("YES")
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {
    'Authorization': 'Bearer eEQLj3MfVVxXsx0s0gTsdWuwyiCFqA3JMGsxb4aUjMzVDwWbNsXovA2K5ExWHskhkYYXML8yUWcyNpWmJhdFQbK_VB0dVmPYy6CoQgonsNQwEo_fuJelQV_Tfqj2Y3Yx'
    }

# Set up the parameters for the API request
    params = {
    'location': 'Manhattan',
    'term': 'Indian dinner',
    'limit': 50, # Maximum limit per request
    'offset': 0 # Starting offset
    }
    cuisines=['Chinese','Italian','Indian','Mexican','Thai','Japanese','American','Greek','British']
    #count=2
    complete_list=[]
    ids=[]
    for cuisine in cuisines:
        print(cuisine)
        params['term']=cuisine+' dinner'
        params['offset']=0
        count=1000
        complete_list +=collect2(url,headers,params,count,ids)[0] #call collect1 and collect2 for elastic search and DynamoDb Data files
        ids += collect2(url,headers,params,count,ids)[1]
        print(len(complete_list))
    return complete_list


if __name__ == "__main__":
  data=yelp()
  with open("rest_final.json",'w') as f:
    
    json.dump(data,f)
      
  #print(len(data))
  #insert_data(data)

  print("Finished")
