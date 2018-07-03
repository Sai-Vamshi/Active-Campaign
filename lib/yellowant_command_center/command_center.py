"""This file contains the logic to understand a user message request
 from YA and return a response in the format of
 a YA message object accordingly
"""
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, AttachmentFieldsClass, MessageButtonsClass
from ..yellowant_api.models import active_campaign, UserIntegration
import requests

class CommandCenter(object):
    """Handles user commands
    Args:
        yellowant_integration_id (int): The integration id of a YA user
        self.commands (str): Invoke name of the command the user is calling
        args (dict): Any arguments required for the command to run
    """

    def __init__(self, yellowant_user_id, yellowant_integration_id, function_name,
                 args, application_invoke_name):
        self.yellowant_user_id = yellowant_user_id
        self.application_invoke_name = application_invoke_name
        self.yellowant_integration_id = yellowant_integration_id
        self.account_id = UserIntegration.objects.get(yellowant_integration_invoke_name=
                                                      self.application_invoke_name)
        self.API_Access_URL = active_campaign.objects.get(id_id=self.account_id).API_Access_URL
        self.API_Access_key = active_campaign.objects.get(id_id=self.account_id).API_Access_key
        self.function_name = function_name
        self.args = args

    def parse(self):
        """The connection between yellowant commands and functions in django"""
        self.commands = {
            "account-view": self.account_view,
            # "campaign-list": self.campaign_list,
            "list-view": self.list_view,
            "list-delete": self.list_delete,
            'campaign-delete': self.campaign_delete,
            'automation-list': self.automation_list,
            'deal-delete': self.deal_delete,
            'deal-list': self.deal_list,
            'deal-get': self.deal_get,
            'campaign-status': self.campaign_status,
            'bounce-totals': self.campaign_report_bounce_list,
            # 'c-bounce-totals': self.campaign_report_bounce_totals,
            # 'forward-list':self.campaign_report_forward_list,
            # 'forward-totals': self.campaign_report_forward_totals,
            # 'link-list': self.campaign_report_link_list,
            # 'open-list': self.campaign_report_open_list,
            # 'open-totals': self.campaign_report_open_totals,
            'totals': self.campaign_report_totals,
            # 'unopen-list': self.campaign_report_unopen_list,
            # 'unsubscription-list':self.campaign_report_unsubscription_list,
            # 'unsubscription-totals': self.campaign_report_unsubscription_totals,


        }

        return self.commands[self.function_name](self.args)

    def account_view(self,args):
        """For viewing the account details"""
        query = "api_key="+self.API_Access_key+"&api_action=account_view&api_output=json"
        url = (self.API_Access_URL + "/admin/api.php?"+ query)
        print(self.API_Access_URL)
        print(url)
        response = requests.get(url)
        response_json = response.json()

        message = MessageClass()
        message.message_text = "Account Details:"

        attachment = MessageAttachmentsClass()
        field1 = AttachmentFieldsClass()
        field1.title = "Account"
        field1.value = response_json['account']
        attachment.attach_field(field1)

        field2 = AttachmentFieldsClass()
        field2.title = "Email"
        field2.value = response_json['email']
        attachment.attach_field(field2)

        field3 = AttachmentFieldsClass()
        field3.title = "Subscriber Limit"
        field3.value = response_json['subscriber_limit']
        attachment.attach_field(field3)

        message.attach(attachment)
        return message.to_json()

    # def campaign_list(self, args):
    #     """For viewing the account details"""
    #     # try:
    #     #     id=1
    #     #     while(1):
    #     #         query = "api_key=" + self.API_Access_key + "&api_action=account_view&api_output=json&id=" + id
    #     #         url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     #         print(self.API_Access_URL)
    #     #         print(url)
    #     #         response = requests.get(url)
    #     #         response_json = response.json()
    #     #         id =id + 1
    #     #
    #     # except:
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_list&api_output=json&id="+"0"
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     print(self.API_Access_URL)
    #     print(url)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     message = MessageClass()
    #     message.message_text = "Account Details:"

    def campaign_delete(self, args):
        """For viewing the account details"""
        message = MessageClass()
        id = args['Id']
        query = "api_key=" + self.API_Access_key + "&api_action=campaign_delete&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        # print(self.API_Access_URL)
        # print(url)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        attachment = MessageAttachmentsClass()
        attachment.title = response_json['result_message']

        message.attach(attachment)
        message.message_text = ""
        return message.to_json()

    def campaign_status(self, args):
        """For viewing the account details"""
        message = MessageClass()
        id = args['Id']
        status = args['status']
        query = "api_key=" + self.API_Access_key + "&api_action=campaign_status&api_output=json&id="+id+"&status="+status
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        attachment = MessageAttachmentsClass()
        attachment.title = response_json['result_message']

        message.attach(attachment)
        message.message_text = ""
        return message.to_json()

    def campaign_report_bounce_list(self, args):
        """For viewing the account details"""
        message = MessageClass()
        id = args['Id']
        query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_bounce_list&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        response = requests.get(url)
        response_json = response.json()
        #print(response_json[str(1)]['descript'])

        i=0
        j=0
        for i in range(1000000):
            try:
                attachment = MessageAttachmentsClass()
                field1 = AttachmentFieldsClass()
                field1.title = "Description"
                field1.value = response_json[str(i)]['descript']
                attachment.attach_field(field1)

                field2 = AttachmentFieldsClass()
                field2.title = "Email"
                field2.value = response_json[str(i)]['email']
                attachment.attach_field(field2)
                i+=1
            except:
                break
        #print(i)
        for j in range(i):
            print(j)
            attachment = MessageAttachmentsClass()
            field1 = AttachmentFieldsClass()
            field1.title = "Description"
            field1.value = response_json[str(j)]['descript']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Email"
            field2.value = response_json[str(j)]['email']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "ID"
            field3.value = response_json[str(j)]['id']
            attachment.attach_field(field3)
            j += 1
            print(j)

        message.attach(attachment)
        message.message_text = "The Bounce list is"
        return message.to_json()

    # def campaign_report_bounce_totals(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     messageid = args['messageId']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_bounce_totals&api_output=json&id="+id+"&messageid="+messageid
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_forward_list(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     messageid = args['messageId']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_forward_list&api_output=json&id="+id+"&messageid="+messageid
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_forward_totals(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_forward_totals&api_output=json&id="+id
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_link_list(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     messageid = args['messageId']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_link_list&api_output=json&id="+id+"&messageid="+messageid
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_open_list(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_open_list&api_output=json&id="+id
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_open_totals(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     messageid = args['messageId']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_open_totals&api_output=json&id="+id+"&messageid="+messageid
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()

    def campaign_report_totals(self, args):
        """For viewing the account details"""
        message = MessageClass()
        id = args['Campaign-ID']
        query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_totals&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        attachment = MessageAttachmentsClass()
        field1 = AttachmentFieldsClass()
        field1.title = "Unsubscribes"
        field1.value = response_json['unsubscribes']
        attachment.attach_field(field1)

        field2 = AttachmentFieldsClass()
        field2.title = "Unique opens"
        field2.value = response_json['uniqueopens']
        attachment.attach_field(field2)

        field3 = AttachmentFieldsClass()
        field3.title = "Unique Replies"
        field3.value = response_json['uniquereplies']
        attachment.attach_field(field3)

        field4 = AttachmentFieldsClass()
        field4.title = "Forwards"
        field4.value = response_json['forwards']
        attachment.attach_field(field4)

        field5 = AttachmentFieldsClass()
        field5.title = "Social shares"
        field5.value = response_json['socialshares']
        attachment.attach_field(field5)

        field6 = AttachmentFieldsClass()
        field6.title = "Unique Replies"
        field6.value = response_json['subscriberclicks']
        attachment.attach_field(field6)

        message.attach(attachment)
        message.message_text = "The Report of the Campaign:"
        return message.to_json()

    # def campaign_report_unopen_list(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     messageid = args['messageId']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_unopen_list&api_output=json&id="+id+"&messageid="+messageid
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_unsubscription_list(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     status = args['status']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_unsubscription_list&api_output=json&id="+id
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()
    #
    # def campaign_report_unsubscription_totals(self, args):
    #     """For viewing the account details"""
    #     message = MessageClass()
    #     id = args['Id']
    #     messageid = args['messageId']
    #     query = "api_key=" + self.API_Access_key + "&api_action=campaign_report_unsubscription_totals&api_output=json&id="+id+"&messageid="+messageid
    #     url = (self.API_Access_URL + "/admin/api.php?" + query)
    #     response = requests.get(url)
    #     response_json = response.json()
    #     print(response_json)
    #     attachment = MessageAttachmentsClass()
    #     attachment.title = response_json['result_message']
    #
    #     message.attach(attachment)
    #     message.message_text = ""
    #     return message.to_json()

    def list_view(self, args):
        """For viewing the account details"""
        id = args['Id']
        query = "api_key=" + self.API_Access_key + "&api_action=list_view&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        print(self.API_Access_URL)
        print(url)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)

        message = MessageClass()
        message.message_text = "Account Details:"

        attachment = MessageAttachmentsClass()
        try:
            field1 = AttachmentFieldsClass()
            field1.title = "User ID"
            field1.value = response_json['userid']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Name"
            field2.value = response_json['name']
            attachment.attach_field(field2)

            attachment = MessageAttachmentsClass()
            button2 = MessageButtonsClass()
            button2.text = "Delete List"
            button2.value = "Delete List"
            button2.name = "Delete List"
            button2.command = {"service_application": self.yellowant_integration_id,
                               "function_name": "list-delete",
                               "data": {"Id": args['Id']}}
            attachment.attach_button(button2)
            message.attach(attachment)
            message.message_text = "The Details of the list are:"

        except:
            message.message_text = "The Given list Does not exist"

        return message.to_json()

    def list_delete(self, args):
        """For viewing the account details"""
        id = args['Id']
        query = "api_key=" + self.API_Access_key + "&api_action=list_delete&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        print(self.API_Access_URL)
        print(url)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        message = MessageClass()
        attachment = MessageAttachmentsClass()
        attachment.title = response_json['result_message']

        message.attach(attachment)
        message.message_text = ""
        return message.to_json()

    def automation_list(self, args):
        """For viewing the account details"""
        query = "api_key=" + self.API_Access_key + "&api_action=automation_list&api_output=json"
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        print(self.API_Access_URL)
        print(url)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        message = MessageClass()

        attachment = MessageAttachmentsClass()
        url = response_json['result_message']
        if url.endswith('Automation(s) found'):
            url = url[:-19]
        n = int(url)
        if(n==0):
            message.message_text = "No Automations present"
            return message.to_json()
        i = 0
        while i<n:
            j = str(i)
            field1 = AttachmentFieldsClass()
            field1.title = "ID"
            field1.value = response_json[j]['id']
            attachment.attach_field(field1)

            field3 = AttachmentFieldsClass()
            field3.title = "Name"
            field3.value = response_json[j]['name']
            attachment.attach_field(field3)
            i+=1

        message.attach(attachment)
        message.message_text = "The Automations present are:"
        return message.to_json()

    def deal_delete(self, args):
        """For viewing the account details"""
        id = args['Id']
        query = "api_key=" + self.API_Access_key + "&api_action=deal_delete&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        print(self.API_Access_URL)
        print(url)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        message = MessageClass()
        attachment = MessageAttachmentsClass()
        attachment.title = response_json['result_message']

        message.attach(attachment)
        message.message_text = ""
        return message.to_json()

    def deal_list(self, args):
        """For viewing the account details"""
        query = "api_key=" + self.API_Access_key + "&api_action=deal_list&api_output=json"
        url = (self.API_Access_URL + "/admin/api.php?" + query)

        response = requests.get(url)
        response_json = response.json()

        message = MessageClass()
        attachment = MessageAttachmentsClass()
        for i in response_json['deals']:

            field1 = AttachmentFieldsClass()
            field1.title = "Title"
            field1.value = i['title']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Email"
            field2.value = i['contact_email']
            attachment.attach_field(field2)

        message.attach(attachment)
        message.message_text = "List of deals:"
        return message.to_json()

    def deal_get(self, args):
        """For viewing the account details"""
        id = args['Id']
        query = "api_key=" + self.API_Access_key + "&api_action=deal_get&api_output=json&id="+id
        url = (self.API_Access_URL + "/admin/api.php?" + query)
        print(self.API_Access_URL)
        print(url)
        response = requests.get(url)
        response_json = response.json()
        print(response_json)
        message = MessageClass()
        message.message_text = "Account Details:"

        attachment = MessageAttachmentsClass()
        field1 = AttachmentFieldsClass()
        field1.title = "Title"
        field1.value = response_json['title']
        attachment.attach_field(field1)

        field2 = AttachmentFieldsClass()
        field2.title = "Contact Email"
        field2.value = response_json['contact_email']
        attachment.attach_field(field2)

        field3 = AttachmentFieldsClass()
        field3.title = "Deal Notes"
        field3.value = response_json['deal_notes']
        attachment.attach_field(field3)

        message.attach(attachment)
        message.message_text = "The Details of Deal are:"
        return message.to_json()

