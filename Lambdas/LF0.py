import boto3
# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')
def lambda_handler(event, context):
    print(event)
    print(context)
    msg_from_user = event['messages'][0]['unstructured']['text']
    print(msg_from_user)

    print(f"Message from frontend: {msg_from_user}")
    # Initiate conversation with Lex
    response = client.recognize_text(
            botId='1LMSNEMFVB', # MODIFY HERE
            botAliasId='RDOJLLYT8V', # MODIFY HERE
            localeId='en_US',
            sessionId='testuser3',
            text=msg_from_user)
    print(response)
    
    intent = response.get('sessionState')
    intent = intent.get('intent').get('name')
    print("Intent: ",intent)
    
    msg_from_lex = response.get('messages', [])
    print(msg_from_lex)
    if msg_from_lex:
        resp = {}
        if(True):
        #if(intent == "GreetingIntent"):
            print("Here")
            resp = {
                'statusCode': 200,
                'messages': [{"type": "unstructured", "unstructured":{"text":msg_from_lex[0]['content']}}],
                "headers": { 
                "Access-Control-Allow-Origin": "*" 
                }  
            }
       
        return resp
