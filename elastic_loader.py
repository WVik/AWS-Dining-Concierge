import json
with open("rest_final.json",'r') as f:
     #for d in data:
    data=json.load(f)

elastic=[]
info=[]
for restaurant in data:
   
   
   neccessary_info={}
   neccessary_info1={"index": {"_index":"diners","_id":restaurant['business-id']}}
   neccessary_info['business-id']=str(restaurant['business-id'])
   neccessary_info['cuisine']=restaurant['cuisine'].split(" ")[0]
   neccessary_info_params=['name']
   for nec_param in neccessary_info_params:
    if nec_param in restaurant.keys():
      neccessary_info[nec_param]=str(restaurant[nec_param])

   info.append(neccessary_info1)
   info.append(neccessary_info)


with open("rest_final_elast_f.json",'w') as f:
    for d in info:
      json.dump(d,f)
      f.write('\n')
