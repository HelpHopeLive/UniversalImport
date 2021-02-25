import re

import numpy as np
import pandas as pd
import os
import sys
import json
import requests
from datetime import datetime
from datetime import date

from django.shortcuts import get_object_or_404
from numpy import nan
from .models import Team, ConstituentFile

def convert(import_csv):
    today = date.today()
    pd.set_option('display.max_colwidth', None)
    existing_constituent_object = get_object_or_404(ConstituentFile)

    pd.set_option('display.float_format', '{:.0f}'.format)
    existing_constituents = pd.read_csv(existing_constituent_object.document)
    raceroster = pd.read_csv(import_csv)

    raceroster['ntaf'] = pd.Series()
    print(raceroster.head())
    #executes env.py to grab os.env variables

    exec(open("settings/local_dev.py").read())
    api_url = os.getenv('API_URL')
    api_token = os.getenv('API_TOKEN')

    const_cols = ["PrimAddText", "PrimSalText", "ConsID", "KeyInd", "LastName"]
    gifts_cols = ["GFTAmt","GFType", "FundID", "GFDate", "ConsID", "GFImpID"]
    gifts_attr_cols = ["GFAttrCat", "GFAttrDesc", "GFImpID"]
    existing_constituents.head()

    def find_matching_emails(email):
        found = False
        constituent_id = None
        constituent = None
        if(email):
            constituent = existing_constituents.loc[existing_constituents['Email address'] == email]
            found = True
        if(len(constituent) > 0):
            constituent_id = constituent['Constituent ID'].values[0]
        return constituent_id




    def find_matching_phone_number(number):
        constituent = None
        constituent_id = None
        existing_constituents.head()
        constituent = existing_constituents.loc[existing_constituents['Phone'] == number]
        if(len(constituent)>0):
            constituent_id = constituent['Constituent ID'].values[0]
        return constituent_id
    test = find_matching_phone_number(2159048455)

    print (test)
    #simple constituent ID lookup
    def find_constituent(id):
        constituent = None
        constituent = existing_constituents.loc[existing_constituents['Constituent ID'] == id]
        return constituent


    def generate_constituent_id(source_id):
        c_id = None
        c_id = ("RR-" + str(source_id))
        return c_id


    def generate_gift_code(event_id, confirmation_num):
        g_id = None
        g_id = (str(event_id) + str(confirmation_num))
        return g_id


    def registration_gift_describer(row):
        gift_desc = None
        if row['Is this to benefit a Help Hope Live client?'] == "no":
            gift_desc = "EVT21-Tkt" #For unrestricted registration funds
        else:
            gift_desc = "RCA21"  #For restricted registration funds
        return gift_desc

    def donation_gift_describer(row):
        gift_desc = None
        if row['Is this to benefit a Help Hope Live client?'] == "no":
            gift_desc = "EVT21" #For unrestricted donation funds
        else:
            gift_desc = "RCA21"  #For restricted donation funds
        return gift_desc

    def swag_gift_describer(row):
        gift_desc = None
        if row['Is this to benefit a Help Hope Live client?'] == "no":
            gift_desc = "EVT21-Auc" #For unrestricted donation funds
            #restricted gifts are the same in this case
        else:
            gift_desc = "EVT21-Auc"  #For restricted donation funds
        return gift_desc

    def sponsor_gift_describer(row):
        gift_desc = None
        if row['Is this to benefit a Help Hope Live client?'] == "no":
            gift_desc = "EVT21-SP" #For unrestricted donation funds
        else:
            gift_desc = "RCA21"  #For restricted donation funds
        return gift_desc


    def team_gen(source_data):
        for i, row in source_data.iterrows():
            if row['Is team captain'] == 'Y':
                number = int(row['Team ID - Numeric'])
                if number:
                    try:
                        team = get_object_or_404(Team, number=number)
                    except:
                        print("didnt find that ")
                        Team.objects.create_team(number, row['Team Name'], (row['First Name'] + " " + row['Last Name']), row['ntaf'])


    def dupe_scanner(output_data):
        return output_data.drop_duplicates()

    def gift_dropper(gifts, gifts_attr):
        g_code = None
        for i, row in gifts.iterrows():
            if row['GFTAmt'] == 0:
                g_code = row['GFImpID']
                gifts.drop(i, inplace=True)

            for j, row_second in gifts_attr.iterrows():
                if row_second['GFImpID'] == g_code:
                    gifts_attr.drop(j, inplace=True)

    def constituent_dropper(constituents):
        for i, row in constituents.iterrows():
            if row['ConsID']:
                matchObj = re.match(r"^(?!RR-).*", str(row['ConsID']))
                if matchObj:
                    constituents.drop(i, inplace=True)


    #This will fill the django campaigns pandas structure
    def get_django_campaign(search_term):
        print(search_term)
        headers = {'Authorization': ('Token ' + api_token)}
        if type(search_term)==float or type(search_term)==int:
            search_url=(api_url + "?campaign_id=" + str(search_term))
        else:
            search_url=(api_url + "?full_name=" + search_term)
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            django = json.loads(response.content.decode('utf-8'))
            search_url = None
            frame = pd.json_normalize(django['results'])
            return frame
        else:
            search_url = None
            return None



    # This needs to be expanded, we are going to ask that all team captains add their campaign codes
    # , but if they do not , just look up campaign by captains first + last and grab fund id from there when we fill the gifts array
    def fill_ntaf_codes(source_data):
        camp_code = None
        fund_id = None
        for i, row in source_data.iterrows():
            if (str(row['Is team captain']) == 'Y'):
                team = row['Team ID - String']
                if row['Is this to benefit a Help Hope Live client?'] == "yes":
                    client_name = row['If yes, please enter client name:'].split()
                    django_campaign = get_django_campaign(client_name[0] + "%20" + client_name[1])
                    fund_id = django_campaign['ntaf_id'].values
                    for y, row_second in source_data.iterrows():
                        if (team == row_second['Team ID - String']):
                            source_data.loc[y, 'ntaf'] = fund_id
                else:
                    for y, row_third in source_data.iterrows():
                        if (team == row_third['Team ID - String']):
                            source_data.loc[y, 'ntaf'] = "HHL25"
            else:
                source_data.loc[i, 'ntaf'] = "HHL25"
                # elif lookup benefit client name next then else flag that row for review.


    fill_ntaf_codes(raceroster)
    team_gen(raceroster)
    constituents = pd.DataFrame(columns=const_cols)
    gifts = pd.DataFrame(columns=gifts_cols)
    gifts_attr = pd.DataFrame(columns=gifts_attr_cols)

    # Need a function here to decide on weather gift is restricted or not . Plan is to have multiple unrestricted teams. along with multiple restricted
    #fills up constituent array, runs lookup of both Email and Phone Number. If none found in existing_constituents prim_add and prim_sal (FirstName LastName) is grabbed from the roster csv
    for i, row in raceroster.iterrows():
        date_time_obj = datetime.strptime(row['Date Registered'], '%Y-%m-%d %H:%M:%S EST')
        constituent_id = None
        prim_add = None
        prim_sal = None
        GFImpID = None
        if row['Phone Number']:
            constituent_id = find_matching_phone_number(row['Phone Number'])
            print(constituent_id)
        if constituent_id == None:
            constituent_id = find_matching_emails(row['Email'])
            print(constituent_id)
        if (constituent_id != None):
            constituent = find_constituent(constituent_id)
            prim_add = (row['First Name'] + ' ' + row['Last Name'])
            prim_sal = (row['First Name'] + ' ' + row['Last Name'])
        else:
            prim_add = (row['First Name'] + ' ' + row['Last Name'])
            prim_sal = (row['First Name'] + ' ' + row['Last Name'])
            #generate const id here
            constituent_id = generate_constituent_id(row['Unique participant ID'])
        #generate gift code
        g_code = generate_gift_code(row['Event ID'], row['Confirmation No.'])
        fund_id = row['ntaf']

        if not np.isnan(row['Sponsor name for acknowledgement']):
            gift_desc = sponsor_gift_describer(row)
        else:
            gift_desc = registration_gift_describer(row)

            # swag handler here
        if int(row['Swag Total']) != 0:
            medal_qty = int(row['Medal (Quantity)'])
            while medal_qty != 0 and not np.isnan(medal_qty):
                swag_gift = pd.DataFrame({'GFTAmt': [15], 'GFType': ["Cash"], 'FundID': [fund_id], 'GFDate': [date_time_obj.strftime('%m/%d/%Y')], 'ConsID': [constituent_id], 'GFImpID': [(g_code + str(medal_qty) + str(1))]})
                gifts = gifts.append(swag_gift, ignore_index=False)
                swag_gift_attr = pd.DataFrame({'GFAttrCat':["Gift Code"], 'GFAttrDesc': [swag_gift_describer(row)], 'GFImpID': [(g_code + str(medal_qty) + str(1))]})
                gifts_attr = gifts_attr.append(swag_gift_attr, ignore_index=False)
                medal_qty-=1

            if not np.isnan(row['T-shirt 2 (Quantity)']) :
                paid_shirt_qty = row['T-shirt 2 (Quantity)']
                while paid_shirt_qty != 0 and not np.isnan(paid_shirt_qty):
                    swag_gift = pd.DataFrame({'GFTAmt': [25], 'GFType': ["Cash"], 'FundID': [fund_id],
                                              'GFDate': [date_time_obj.strftime('%m/%d/%Y')],
                                              'ConsID': [constituent_id],
                                              'GFImpID': [(g_code + str(medal_qty) + str(2))]})
                    gifts = gifts.append(swag_gift, ignore_index=False)
                    swag_gift_attr = pd.DataFrame({'GFAttrCat': ["Gift Code"], 'GFAttrDesc': [swag_gift_describer(row)],
                                                   'GFImpID': [(g_code + str(medal_qty) + str(2))]})
                    gifts_attr = gifts_attr.append(swag_gift_attr, ignore_index=False)
                    paid_shirt_qty-=1
        # donation handler here
        if int(row['Pledges'] != 0):
                donation = pd.DataFrame({'GFTAmt': row['Pledges'], 'GFType': ["Cash"], 'FundID': [fund_id], 'GFDate': [date_time_obj.strftime('%m/%d/%Y')], 'ConsID': [constituent_id], 'GFImpID': [(g_code + str(3))]})
                donation_attr = pd.DataFrame({'GFAttrCat': ["Gift Code"], 'GFAttrDesc': [donation_gift_describer(row)], 'GFImpID':[(g_code + str(3))]})
                gifts = gifts.append(donation, ignore_index=False)
                gifts_attr = gifts_attr.append(donation_attr, ignore_index=False)

        constituents = dupe_scanner(constituents)
        constituents.loc[i] = {'PrimAddText': prim_add, 'PrimSalText':prim_sal, 'ConsID': constituent_id, 'KeyInd':'I', 'LastName': row['Last Name']}
        gifts = dupe_scanner(gifts)
        gifts.loc[i] = {'GFTAmt' : row['Registration Total'],'GFType':"Cash", 'FundID': fund_id, 'GFDate': date_time_obj.strftime('%m/%d/%Y'), 'ConsID': constituent_id, 'GFImpID': g_code}
        gifts_attr = dupe_scanner(gifts_attr)
        gifts_attr.loc[i] = {'GFAttrCat' : "Gift Code", 'GFAttrDesc':gift_desc, 'GFImpID': g_code}
        gift_dropper(gifts, gifts_attr)
        constituent_dropper(constituents)


    today = date.today()

    const_label = ("constituents" + '-' + str(today) + ".csv")
    constituents.to_csv( ("media/documents/" + const_label) , index=False)

    gifts_label = ("gifts" + '-' + str(today) + ".csv")
    gifts.to_csv(("media/documents/" + gifts_label), index=False)


    gifts_attr_label = ("gifts_attr" + '-' + str(today) + ".csv")
    gifts_attr.to_csv(("media/documents/" + gifts_attr_label), index=False)

    return (const_label, gifts_label, gifts_attr_label)