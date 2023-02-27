import boto3
import json
import logging
from boto3.dynamodb.conditions import Key, Attr
##from botocore.vendored import requests
import requests
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-restaraunt-cukiwk3mrajoqtrryubnimlesa.us-east-1.es.amazonaws.com'
INDEX = 'diners'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    
    """
        Query SQS to get the messages
        Store the relevant info, and pass it to the Elastic Search
    """
    
    message = getSQSMsg() #data will be a json object
    print("Message-----", message)
    logger.debug("Message---------------------- %s" % message)
    if message is None:
        logger.debug("No Cuisine or PhoneNum key found in message")
        return
    cuisine = message["MessageAttributes"]["Cuisine"]["StringValue"]
    location = message["MessageAttributes"]["Location"]["StringValue"]
    #date = message["MessageAttributes"]["Date"]["StringValue"]
    time = message["MessageAttributes"]["Time"]["StringValue"]
    numOfPeople = message["MessageAttributes"]["NumPeople"]["StringValue"]
    phoneNumber = message["MessageAttributes"]["PhoneNumber"]["StringValue"]
    phoneNumber = "+1" + phoneNumber
    Email=message["MessageAttributes"]["Email"]["StringValue"]
    ids = query(cuisine)
    #for restaurant in esData:
    #    ids.append(restaurant["_source"]["id"])
    
    messageToSend = 'Hello! Here are my {cuisine} restaurant suggestions in {location} for {numPeople} people, at {diningTime}: '.format(
            cuisine=cuisine,
            location=location,
            numPeople=numOfPeople,
            #diningDate=date,
            diningTime=time,
        )

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-food')
    itr = 1
    for id in ids:
        if itr == 6:
            break
        response = table.scan(FilterExpression=Attr('business-id').eq(id))
        item = response['Items'][0]
        if response is None:
            continue
        restaurantMsg = '' + str(itr) + '. '
        name = item["name"]
        #address = item["coordinates"]
        restaurantMsg += name +', located at ' + '. '
        messageToSend += restaurantMsg
        itr += 1
        
    messageToSend += "Enjoy your meal!!"
    print(messageToSend)
    ses = boto3.client('ses')
    customer_email=Email
    response = ses.send_email(
        Destination={
            'ToAddresses': [
                customer_email
            ]
        },
        Message={
            'Body': {
                'Text': {
                    'Data': messageToSend
                }
            },
            'Subject': {
                'Data': 'Test email'
            }
        },
        Source='ks4070@columbia.edu'
    )
    #try:
    #    client = boto3.client('sns', region_name= 'ap-southeast-1')
    #    response = client.publish(
     #       PhoneNumber=phoneNumber,
     #       Message= messageToSend,
      #      MessageStructure='string'
       # )
    #except KeyError:
    #    logger.debug("Error sending ")
    #logger.debug("response - %s",json.dumps(response) )
    #logger.debug("Message = '%s' Phone Number = %s" % (messageToSend, phoneNumber))
    
    return {
        'statusCode': 200,
        'body': json.dumps(message["MessageAttributes"]["Cuisine"]["StringValue"])
    }
    # return messageToSend

def getSQSMsg():
    SQS = boto3.client("sqs")
    url = 'https://sqs.us-east-1.amazonaws.com/354298500412/DiningConciergeSQS'
    response = SQS.receive_message(
        QueueUrl=url, 
        AttributeNames=['SentTimestamp'],
        MessageAttributeNames=['All'],
        VisibilityTimeout=10,
        WaitTimeSeconds=0
    )
    try:
        message = response['Messages'][0]
        if message is None:
            logger.debug("Empty message")
            return None
    except KeyError:
        logger.debug("No message n the queue")
        return None
    message = response['Messages'][0]
    #SQS.delete_message(
    #        QueueUrl=url,
    #        ReceiptHandle=message['ReceiptHandle']
    #    )
    logger.debug('Received and deleted message: %s' % response)
    return message
def query(term):
    q = {'size': 5, 'query': {'multi_match': {'query': term}}}

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    res = client.search(index=INDEX, body=q)
    print(res)

    hits = res['hits']['hits']
    results = []
    for hit in hits:
        results.append(hit['_source']['business-id'])

    return results


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
