"""The views for Oauth of yellowant and the AWS credentials"""
import json
import urllib
import urllib.parse
import uuid
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.conf import settings
from yellowant import YellowAnt
from django.views.decorators.csrf import csrf_exempt
from yellowant.messageformat import MessageButtonsClass, MessageClass, MessageAttachmentsClass, AttachmentFieldsClass
from ..yellowant_command_center.command_center import CommandCenter
from .models import YellowAntRedirectState, UserIntegration, active_campaign
import requests


def request_yellowant_oauth_code(request):
    """Initiate the creation of a new user integration on YA.
    YA uses oauth2 as its authorization framework. This method requests for an oauth2 code from YA
    to start creating a new user integration for this application on YA.
    """
    # get the user requesting to create a new YA integrationrint
    user = User.objects.get(id=request.user.id)

    # generate a unique ID to identify the user when YA returns an oauth2 code
    state = str(uuid.uuid4())

    # save the relation between user and state
    #  so that we can identify the user when YA returns the oauth2 code
    YellowAntRedirectState.objects.create(user=user, state=state)

    # Redirect the application user to the YA authentication page.
    # Note that we are passing state, this app's client id,
    # oauth response type as code, and the url to return the oauth2 code at.
    return HttpResponseRedirect("{}?state={}&client_id={}&response_type=code&redirect_url={}"
                                .format(settings.YA_OAUTH_URL, state, settings.YA_CLIENT_ID,
                                        settings.YA_REDIRECT_URL))


def yellowant_oauth_redirect(request):
    """Receive the oauth2 code from YA to generate a new user integration
    This method calls utilizes the YA Python SDK to create a new user integration on YA.
    This method only provides the code for creating a new user integration on YA.
    Beyond that, you might need to authenticate the user on the actual application
    (whose APIs this application will be calling) and store a relation
    between these user auth details and the YA user integration.
    """
    # oauth2 code from YA, passed as GET params in the url
    code = request.GET.get("code")

    # the unique string to identify the user for which we will create an integration
    state = request.GET.get("state")

    # fetch user with the help of state
    yellowant_redirect_state = YellowAntRedirectState.objects.get(state=state)
    user = yellowant_redirect_state.user

    # initialize the YA SDK client with your application credentials
    ya_client = YellowAnt(app_key=settings.YA_CLIENT_ID, app_secret=settings.YA_CLIENT_SECRET,
                          access_token=None, redirect_uri=settings.YA_REDIRECT_URL)

    # get the access token for a user integration from YA against the code
    access_token_dict = ya_client.get_access_token(code)
    # print(access_token_dict)
    # print(type(access_token_dict))
    access_token = access_token_dict["access_token"]

    # reinitialize the YA SDK client with the user integration access token
    ya_client = YellowAnt(access_token=access_token)

    # get YA user details
    ya_user = ya_client.get_user_profile()

    # create a new user integration for your application
    user_integration = ya_client.create_user_integration()
    hash_str = str(uuid.uuid4()).replace("-", "")[:25]
    # save the YA user integration details in your database
    ut = UserIntegration.objects.create(user=user, yellowant_user_id=ya_user["id"],
                                        yellowant_team_subdomain=ya_user["team"]["domain_name"],
                                        yellowant_integration_id=user_integration["user_application"],
                                        yellowant_integration_invoke_name=user_integration["user_invoke_name"],
                                        yellowant_integration_token=access_token,
                                        webhook_id = hash_str)


    active_campaign.objects.create(id=ut, API_Access_URL="", API_Access_key="")
    # A new YA user integration has been created and the details have been successfully
    # saved in your application's database. However, we have only created an integration on YA.
    # As a developer, you need to begin an authentication process for the actual application,
    # whose API this application is connecting to. Once, the authentication process
    # for the actual application is completed with the user, you need to create a db
    # entry which relates the YA user integration, we just created, with the actual application
    # authentication details of the user. This application will then be able to identify
    #  the actual application accounts corresponding to each YA user integration.

    # return HttpResponseRedirect("to the actual application authentication URL")

    # return HttpResponseRedirect(reverse("accounts/"), kwargs={"id":ut})
    return HttpResponseRedirect("/")


@csrf_exempt
def yellowant_api(request):
    """Receive user commands from YA"""
    # print("reached")
    data = json.loads(request.POST.get("data"))
    # print(data)
    if data["verification_token"] == settings.YA_VERIFICATION_TOKEN:
        command = CommandCenter(data["user"], data['application'], data['function_name'],
                                data['args'], data['application_invoke_name'])
        reply = command.parse()
        # print (reply)
        # Return to command centre for processing the functin call
        return HttpResponse(reply)

    else:
        # If an error occurs to processthen show 403 response
        return HttpResponse(status=403)


def api_key(request):
    """ This function is used for taking the AWS Credentials from user and store it in the database"""
    data = json.loads(request.body)

    # The data is received from screens-account-Settings page and is redirected
    # here which is now assigned as follows:
    # This try catch is used to verify the Credentials,
    # if they are right then we save it in the database
    # else we show the message Invalid Credentials.
    # For storing the data in our database and updating that it is stored.
    try:
        query = "api_key=" + data["AWS_APISecretAccess"] + "&api_action=account_view&api_output=json"
        url = (data["AWS_APIAccessKey"] + "/admin/api.php?" + query)
        response = requests.get(url)
        aby = active_campaign.objects.get(id_id=int(data["integration_id"]))
        user = UserIntegration.objects.get(id =int(data["integration_id"]) )
        print(int(data["integration_id"]))
        aby.API_Access_URL = data["AWS_APIAccessKey"]
        aby.API_Access_key = data["AWS_APISecretAccess"]
        aby.AWS_update_login_flag = True
        aby.save()
        headers = {
            "Content-Type":"application/x-www-form-urlencoded"
        }
        body = {
            'name': 'My Site',
            'url': settings.BASE_URL+'webhook/'+user.webhook_id+"/",
            'action[]': "subscribe",
            # 'action[]': "unsubscribe,share",
            # 'action[]': "share",
            # 'action[]': "update",
            # 'action[]': "list_add",
            # 'action[]': "deal_add",
            # 'action[]': "deal_update",
            # 'action[]': "deal_pipeline_add",
            # 'action[]': "deal_stage_add",
            # 'action[]': "deal_task_add",
            # 'action[]': "deal_task_complete",
            # 'action[]': "open",
            # 'init[]': 'public',
        }
        webhook_url = data["AWS_APIAccessKey"]+"/admin/api.php?api_key="+data["AWS_APISecretAccess"]+"&api_action=webhook_add&api_output=json"
        data = urllib.parse.urlencode(body)
        # data = "name=My+site&url=http%3A%2F%2F715b81c1.ngrok.io%2Fwebhook%2Fdbc2c6ede4eb44f3a3ae7b0e3%2F&action%5B%5D=contact_tag_added&action%5B%5D=subscribe&init%5B%5D=public"
        data = data + "&action%5B%5D=unsubscribe&action%5B%5D=share&action%5B%5D=deal_task_complete&action%5B%5D=open&init%5B%5D=public"
        webhook_response= requests.post(webhook_url,data = data,headers= headers)
        body = {
            'name': 'My Site',
            'url': settings.BASE_URL + 'webhook/' + user.webhook_id + "/",
        }
        data = urllib.parse.urlencode(body)
        data = data + "&action%5B%5D=list_add&action%5B%5D=deal_add&action%5B%5D=deal_update"
        data = data + "&action%5B%5D=deal_pipeline_add&action%5B%5D=deal_stage_add&action%5B%5D=deal_task_add&init%5B%5D=public"
        webhook_response = requests.post(webhook_url, data=data, headers=headers)
        return HttpResponse("Success", status=200)

    except:
        return HttpResponse("Invalid credentials,either API Url or API Access is wrong")

@csrf_exempt
def webhook(request, hash_str=""):


    data=request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)
    print(params['type'])
    print("\n")
    if(params['type']=="open"):
        campaign_open(request,hash_str)
    elif (params['type'] == "share"):
        campaign_share(request,hash_str)
    elif (params['type'] == "subscribe"):
        contact_added(request, hash_str)
    elif (params['type'] == "unsubscribe"):
        contact_unsubscribe(request, hash_str)
    elif (params['type'] == "list_add"):
        list_added(request, hash_str)
    elif (params['type'] == "deal_add"):
        deal_add(request, hash_str)
    elif (params['type'] == "deal_update"):
        deal_update(request, hash_str)
    elif (params['type'] == "deal_pipeline_add"):
        deal_pipeline_add(request, hash_str)
    elif (params['type'] == "deal_stage_add"):
        deal_stage_add(request, hash_str)
    elif (params['type'] == "deal_task_add"):
        deal_task_add(request, hash_str)
    elif (params['type'] == "deal_task_complete"):
        deal_task_complete(request, hash_str)



    return HttpResponse("ok")


def campaign_open(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['contact[email]']
    name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "Campaign Opened"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "The Campaign is Opened by "+ str(name)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="campaign-open", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def campaign_share(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['contact[email]']
    name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "Campaign Shared"
    shared_on = params['share[network]']
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "The Campaign is Shared by "+ str(name)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Shared on"
    field2.value = params['share[network]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Share Content"
    field2.value = params['share[content]']
    attachment.attach_field(field2)

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
        "Shared_on": shared_on,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="campaign-share", **webhook_message.get_dict())
    print("aqsdfghj")
    return HttpResponse("OK", status=200)


def contact_added(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['contact[email]']
    name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "Campaign Opened"
    time = params['date_time']

    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "A new Contact is added"

    field2 = AttachmentFieldsClass()
    field2.title = "Name"
    field2.value = name
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="contact-added", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def contact_unsubscribe(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['contact[email]']
    name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "Campaign Opened"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "The Contact has Unsubscribed "+ str(name)

    field2 = AttachmentFieldsClass()
    field2.title = "Name"
    field2.value = name
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Reason"
    field2.value = params['unsubscribe[reason]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="contact-unsubscribe", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def list_added(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    # email = params['contact[email]']
    # name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "List Added"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "A new list is created"

    field2 = AttachmentFieldsClass()
    field2.title = "Sender URL"
    field2.value = params['list[sender_state]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Sender Address 1"
    field2.value = params['list[sender_addr1]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Sender Address 2"
    field2.value = params['list[sender_addr2]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Sender Remainder"
    field2.value = params['list[sender_reminder]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        # "Name": name,
        # "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="list-added", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def deal_add(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['deal[contact_email]']
    name =  params['deal[contact_firstname]']+" "+params['deal[contact_lastname]']
    type = "Deal Added"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "A new deal is added "+ str(name)

    field2 = AttachmentFieldsClass()
    field2.title = "Name"
    field2.value = name
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Currency"
    field2.value = params['deal[currency]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal title"
    field2.value = params['deal[title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Pipeline title"
    field2.value = params['deal[pipeline_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Stage title"
    field2.value = params['deal[stage_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Note"
    field2.value = params['deal[note]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Value"
    field2.value = params['deal[value]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="deal-add", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def deal_update(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['deal[contact_email]']
    name =  params['deal[contact_firstname]']+" "+params['deal[contact_lastname]']
    type = "Deal Updated"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "A new deal is added "+ str(name)

    field2 = AttachmentFieldsClass()
    field2.title = "Name"
    field2.value = name
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Currency"
    field2.value = params['deal[currency]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal title"
    field2.value = params['deal[title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Pipeline title"
    field2.value = params['deal[pipeline_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Stage title"
    field2.value = params['deal[stage_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Note"
    field2.value = params['deal[note]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Value"
    field2.value = params['deal[value]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="deal-update", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def deal_pipeline_add(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    # email = params['contact[email]']
    # name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "Deal Pipeline Add"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "The Deal Pipeline is added. "

    field2 = AttachmentFieldsClass()
    field2.title = "Pipeline ID"
    field2.value = params['pipeline[id]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Pipeline Title"
    field2.value = params['pipeline[title]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="deal-pipeline-add", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def deal_stage_add(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    # email = params['contact[email]']
    # name = params['contact[first_name]']+" "+params['contact[last_name]']
    type = "Deal Stage Add"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "The Deal Stage is added. "

    field2 = AttachmentFieldsClass()
    field2.title = "Stage ID"
    field2.value = params['stage[id]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Stage Title"
    field2.value = params['stage[title]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="deal-stage-add", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def deal_task_add(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['deal[contact_email]']
    name =  params['deal[contact_firstname]']+" "+params['deal[contact_lastname]']
    type = "Deal Task Added"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "A new Deal task is added "

    field2 = AttachmentFieldsClass()
    field2.title = "Name"
    field2.value = name
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Currency"
    field2.value = params['deal[currency]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal title"
    field2.value = params['deal[title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Pipeline title"
    field2.value = params['deal[pipeline_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Stage title"
    field2.value = params['deal[stage_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Note"
    field2.value = params['deal[note]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Task Note"
    field2.value = params['task[note]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Value"
    field2.value = params['deal[value]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="deal-task-add", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


def deal_task_complete(request, webhook_id):
    """
            Webhook function to notify user about newly added pipeline
    """

    data = request.body.decode('utf-8')
    # print(type(data))
    urllib.parse.unquote(data)
    params_dict = urllib.parse.parse_qsl(data)
    params = dict(params_dict)

    email = params['deal[contact_email]']
    name =  params['deal[contact_firstname]']+" "+params['deal[contact_lastname]']
    type = "Deal Task Completed"
    time = params['date_time']
    # Fetching yellowant object
    yellow_obj = UserIntegration.objects.get(webhook_id=webhook_id)
    access_token = yellow_obj.yellowant_integration_token
    integration_id = yellow_obj.yellowant_integration_id
    service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    attachment = MessageAttachmentsClass()
    webhook_message.message_text = "A new deal task is Completed"

    field2 = AttachmentFieldsClass()
    field2.title = "Name"
    field2.value = name
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Email"
    field2.value = email
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Currency"
    field2.value = params['deal[currency]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal title"
    field2.value = params['deal[title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Pipeline title"
    field2.value = params['deal[pipeline_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Stage title"
    field2.value = params['deal[stage_title]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Note"
    field2.value = params['deal[note]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Task Note"
    field2.value = params['task[note]']
    attachment.attach_field(field2)

    field2 = AttachmentFieldsClass()
    field2.title = "Deal Value"
    field2.value = params['deal[value]']
    attachment.attach_field(field2)

    # button_get_pipeline = MessageButtonsClass()
    # button_get_pipeline.name = "1"
    # button_get_pipeline.value = "1"
    # button_get_pipeline.text = "Get all pipelines"
    # button_get_pipeline.command = {
    #     "service_application": service_application,
    #     "function_name": 'list_pipelines',
    #     "data": {
    #         'data': "test",
    #     }
    # }

    # attachment.attach_button(button_get_pipeline)
    webhook_message.attach(attachment)

    webhook_message.data = {
        "Name": name,
        "Email": email,
        "Type": type,
        "Time": time,
        "Deal-Name": params['deal[title]']
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    send_message = yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="deal-task-complete", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)

