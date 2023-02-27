"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.
For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json
import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
SQS = boto3.client("sqs")
regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def getQueueURL():
    """Retrieve the URL for the configured queue name"""
    q = SQS.get_queue_url(QueueName='DiningConciergeSQS').get('QueueUrl')
    return q
    
def record(event):
    """The lambda handler"""
    logger.debug("Recording with event %s", event)
    data = event.get('data')
    try:
        logger.debug("Recording %s", data)
        u = getQueueURL()
        logging.debug("Got queue URL %s", u)
        resp = SQS.send_message(
            QueueUrl=u, 
            MessageBody="Dining Concierge message from LF1 ",
            MessageAttributes={
                "Location": {
                    "StringValue": str(get_slots(event)["Location"]["value"]["originalValue"]),
                    "DataType": "String"
                },
                "Cuisine": {
                    "StringValue": str(get_slots(event)["Cuisine"]["value"]["originalValue"]),
                    "DataType": "String"
                },
                "Time" : {
                    "StringValue": str(get_slots(event)["DiningTime"]["value"]["originalValue"]),
                    "DataType": "String"
                },
                "NumPeople" : {
                    "StringValue": str(get_slots(event)["NumberOfPeople"]["value"]["originalValue"]),
                    "DataType": "String"
                },
                "PhoneNumber" : {
                    "StringValue": str(get_slots(event)["PhoneNumber"]["value"]["originalValue"]),
                    "DataType": "String"
                },
                "Email" : {
                    "StringValue": str(get_slots(event)["Email"]["value"]["originalValue"]),
                    "DataType": "String"
                }
            }
        )
        logger.debug("Send result: %s", resp)
    except Exception as e:
        raise Exception("Could not record link! %s" % e)

def get_slots(intent_request):
    temp = intent_request['sessionState']['intent']['slots']
    return temp


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message = None):
    session_attributes['dialogAction'] = {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    if(message is None):
       return {
        'sessionState': session_attributes
       } 

    return {
        'sessionState': session_attributes,
        'messages':[message]
    }


def close(session_attributes, fulfillment_state, message):
    session_attributes['dialogAction'] = {
            'type': 'Delegate',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    response = {
        'sessionState': session_attributes,
    }

    return response


def delegate(session_attributes, slots):
    print("Delegate: ",slots)
    session_attributes['dialogAction'] = {
            'type': 'Delegate',
            'slots': slots
        }
    return {
        'sessionState': session_attributes,
        # 'dialogAction': {
        #     'type': 'Delegate',
        #     'slots': slots
        # }
    }


""" --- Helper Functions --- """
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n

def isvalid_cuisine(cuisine):
    cuisines = ['indian', 'thai', 'mediterranean', 'chinese', 'italian']
    return cuisine.lower() in cuisines

def isvalid_numberofpeople(numPeople):
    numPeople = safe_int(numPeople)
    print("Num people: ", numPeople)
    print("Num People Compare: ", numPeople<20)
    if ((numPeople < 0)):
        return False
    return True
        
def isvalid_date(diningdate):
    if datetime.datetime.strptime(diningdate, '%Y-%m-%d').date() <= datetime.date.today():
        return False

def isvalid_time(diningdate, diningtime):
    if datetime.datetime.strptime(diningdate, '%Y-%m-%d').date() == datetime.date.today():
        if datetime.datetime.strptime(diningtime, '%H:%M').time() <= datetime.datetime.now().time():
            return False

def validate_dining_suggestion(location, cuisine, diningtime, numPeople, phoneNumber, email):

    print("Location: ", location)
    allowed_locations = ["new york","manhattan","queens","Jersey","New Jersey"]
    if location is not None:
        
        if(location.lower() not in allowed_locations):
            return build_validation_result(False, 'Location', "Oh snap! We don't serve that location yet. Please try another one!")

    if cuisine is not None:
        if not isvalid_cuisine(cuisine):
            return build_validation_result(False, 'Cuisine', "I don't find any {cs} cuisines nearby in my database. Please try any other cuisine".format(cs=cuisine))
            
    # if diningdate is not None:
    #     if not isvalid_date(diningdate):
    #         return build_validation_result(False, 'diningdate', 'Please enter valid date')
    
    if diningtime is not None:
        if len(diningtime)!=5:
            return build_validation_result(False, 'DiningTime', 'Please enter valid time')

    if numPeople is not None:
        if not isvalid_numberofpeople(numPeople):
            return build_validation_result(False, 'NumberOfPeople', 'Maximum 20 people allowed. Try again')

    if phoneNumber is not None:
        if len(phoneNumber)<8 or len(phoneNumber)>10:
            return build_validation_result(False, 'PhoneNumber', "Hmm..That doesn't look right. Please re-enter your phone number!")
    
    if email is not None:
        if not re.fullmatch(regex, email):
            return build_validation_result(False, 'Email', "Seems like that's an invalid email, kindly reenter")
        
            

    return build_validation_result(True, None, None)



""" --- Functions that control the bot's behavior --- """


def diningSuggestions(intent_request,context):
    
    print("Intent Request: ",intent_request)
    location = get_slots(intent_request)["Location"]["value"]["originalValue"]  if get_slots(intent_request)["Location"] is not None else None
    cuisine = get_slots(intent_request)["Cuisine"]["value"]["originalValue"]  if get_slots(intent_request)["Cuisine"] is not None else None
    time = get_slots(intent_request)["DiningTime"]["value"]["resolvedValues"][0]  if get_slots(intent_request)["DiningTime"] is not None else None
    numberOfPeople = get_slots(intent_request)["NumberOfPeople"]["value"]["originalValue"]  if get_slots(intent_request)["NumberOfPeople"] is not None else None
    phoneNumber = get_slots(intent_request)["PhoneNumber"]["value"]["originalValue"]  if get_slots(intent_request)["PhoneNumber"] is not None else None
    email = get_slots(intent_request)["Email"]["value"]["originalValue"]  if get_slots(intent_request)["Email"] is not None else None
    source = intent_request['invocationSource']
    print(location, cuisine, time, numberOfPeople, phoneNumber, source)
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)
        
        validation_result = validate_dining_suggestion(location, cuisine, time, numberOfPeople, phoneNumber, email)
        print("Validation Result", validation_result)
        
        message = validation_result['message'] if ('message' in validation_result) else None
        print("Message: ", message)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionState'],
                               intent_request['sessionState']['intent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               message
                               )


        print("-----Getting here-----")
        print("Intent request: ", intent_request)
        output_session_attributes = intent_request['sessionState'] if intent_request['sessionState'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    print("got here after all intents fulfilled")
    record(intent_request)
    return close(intent_request['sessionState'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thank you for the information, we are generating our recommendations, we will send the recommendations to your phone when they are generated'})


""" --- Intents --- """

def welcome(intent_request):
    return close(intent_request['sessionState'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Hey there, How may I serve you today?'})

def thankYou(intent_request):
    return close(intent_request['sessionState'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'My pleasure, Have a great day!!'})


def dispatch(intent_request,context):
    """
    Called when the user specifies an intent for this bot.
    """

    #logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['sessionState']['intent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        val = diningSuggestions(intent_request,context)
        return val
    elif intent_name == 'ThankYouIntent':
        return thankYou(intent_request)
    elif intent_name == 'WelcomeIntent':
        return welcome(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    print("Lambda Handled")
    print(event, context)
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    #logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event,context)
