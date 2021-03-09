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

def convert(RR_Reg, RR_Don):
    today = date.today()
    pd.set_option('display.max_colwidth', None)
    existing_constituent_object = get_object_or_404(ConstituentFile)
    pd.set_option('display.float_format', '{:.0f}'.format)
    existing_constituents = pd.read_csv(existing_constituent_object.document)
    racerosterreg = pd.read_csv(RR_Reg)
    racerosterdon = pd.read_csv(RR_Don)
    racerosterreg['ntaf'] = pd.Series()
    #to track when a constituent is found and should be dropped from the constituent export
    racerosterreg['found_constituent'] = pd.Series()
    racerosterdon['ntaf'] = pd.Series()
    #executes env.py to grab os.env variables
    exec(open("settings/local_dev.py").read())
    api_url = os.getenv('API_URL')
    api_token = os.getenv('API_TOKEN')

    def clean_donation_phones(donation_data):
         for i, row in donation_data.iterrows():
             phone_number = row['Phone number']
             if not isinstance(phone_number, float):
                cleaned_number = re.findall(r'[0-9]+', phone_number)
                if len(cleaned_number) > 1:
                     cleaned_number = ''.join(cleaned_number)
                elif len(cleaned_number) == 1:
                    cleaned_number = cleaned_number[0]
                else:
                    cleaned_number = np.nan
             donation_data.loc[i, 'Phone number'] = cleaned_number
         return donation_data

    #def clean_registration_phones(registration_data):
    #    for i, row in registration_data.iterrows():
    #        phone_number = row['Phone Number']
    #        if not isinstance(phone_number, float):
    #            cleaned_number = re.findall(r'[0-9]+', phone_number)
    #            if len(cleaned_number) > 1:
    #                cleaned_number = ''.join(cleaned_number)
    #            elif len(cleaned_number) == 1:
    #                cleaned_number = cleaned_number[0]
    #            else:
    #                cleaned_number = np.nan
    #            registration_data.loc[i, 'Phone'] = cleaned_number
    #            print("Currently on row: {}; Currently iterrated {}% of rows".format(i, (i + 1) / len(existing_constituents.index) * 100))
    #    return registration_data


    const_cols = ["ImportID", "PrimAddText", "PrimSalText", "ConsID", "KeyInd", "LastName", "FirstName", "AddrLines", "AddrCity", "AddrState", "AddrZIP", "PhoneNum.0", "PhoneType.0", "PhoneNum.1", "PhoneType.1"]
    gifts_cols = ["GFTAmt","GFType", "FundID", "GFDate", "ConsID", "GFImpID"]
    gifts_attr_cols = ["GFAttrCat", "GFAttrDesc", "GFImpID"]
    #existing_constituents = clean_phones(existing_constituents)

    def find_matching_emails(email):
        constituent_id = None
        constituent = None
        if(email):
            constituent = existing_constituents.loc[existing_constituents['Email address'] == email]
        if(len(constituent) > 0):
            constituent_id = constituent['Constituent ID'].values[0]
        return constituent_id

    def find_matching_phone_number(number):
        constituent = None
        constituent_id = None
        existing_constituents.head()
        constituent = existing_constituents.loc[existing_constituents['Phone'] == number]
        if constituent.empty:
            us_number = str(number)[1:]
            constituent = existing_constituents.loc[existing_constituents['Phone'] == int(us_number)]
        if(len(constituent)>0):
            constituent_id = constituent['Constituent ID'].values[0]
        return constituent_id

    def find_matching_name(first, last):
        constituent = None
        constituent_id = None
        existing_constituents.head()
        constituent = existing_constituents.loc[existing_constituents['Name'].str.lower() == ((first + " " + last).lower())]
        if (len(constituent) > 0):
            constituent_id = constituent['Constituent ID'].values[0]
        return constituent_id

    #simple constituent ID lookup
    def find_constituent(id):
        constituent = None
        constituent = existing_constituents.loc[existing_constituents['Constituent ID'] == id]
        return constituent

    def generate_constituent_id(source_id):
        c_id = None
        c_id = ("RR-" + str(source_id))
        return c_id

    def generate_gift_code(event_id, confirmation_num, participant_id):
        g_id = None
        if isinstance(participant_id, str):
            g_id = (str(event_id) + str(confirmation_num) + ((participant_id[-1]) + participant_id[-2]))
        else:
            g_id = (str(event_id) + str(confirmation_num) + str(participant_id))
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
        if row['ntaf'] == "HHL25":
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

    def new_constituent_cleanup(constituents, gifts, gifts_attr):
        print("test")

    def duped_constituent_scanner(output_data):
        for i, row in output_data.iterrows():
            count = 0
            for j, row_second in output_data.iterrows():
                if row_second['PrimAddText'] == row['PrimAddText'] and row_second['AddrLines'] == row['AddrLines'] and row_second['AddrCity'] == row['AddrCity'] and row_second['AddrState']  == row['AddrState'] and row_second['AddrZIP'] == row['AddrZIP'] and row_second['PhoneNum.1'] == row['PhoneNum.1']:
                    count+=1
                if count > 1:
                    output_data.drop(j, inplace=True)
        return output_data


    def gift_dropper(gifts, gifts_attr):
        g_code = None
        for i, row in gifts.iterrows():
            if row['GFTAmt'] == 0:
                g_code = row['GFImpID']
                gifts.drop(i, inplace=True)

            for j, row_second in gifts_attr.iterrows():
                if row_second['GFImpID'] == g_code:
                    gifts_attr.drop(j, inplace=True)

    def find_previously_generated_constituent(constituents, row):
        for j, row_second in constituents.iterrows():
            if ((row_second['FirstName'] + " " + row_second['LastName']).lower()) == ((row['Donor first name'] + ' ' + row['Donor last name']).lower()):
                constituent_id = row_second['ConsID']
                return constituent_id


    #redo this, some constituents will have the RR- once these start importing
    def constituent_dropper(racerosterreg,constituents):
        for i, row in racerosterreg.iterrows():
            if (row['found_constituent'] == True):
                for j, row_second in constituents.iterrows():
                    if ((row_second['FirstName'] + " " + row_second['LastName']).lower()) == ((row['First Name'] + ' ' + row['Last Name']).lower()):
                        constituents.drop(j, inplace=True)


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
    def fill_registration_ntaf_codes(source_data):
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

    #fills ntaf codes on specifically the donation array(fields have different names ....go figure)
    def fill_donation_ntaf_codes(source_data):
        for i, row in source_data.iterrows():
            if row['Team ID']:
                try:
                    team = get_object_or_404(Team, number=int(row['Team ID']))
                    row['fund_id'] = team.fund_id
                    source_data.loc[i, 'ntaf'] = team.fund_id
                except:
                    print("didnt find a team , assuming unrestricted")
                    source_data.loc[i, 'ntaf'] = "HHL25"

    #to be expanded later on
    def scan_for_existing(constituents, existing_constituents):
            similarities = 0
            total_factors = 8

    fill_registration_ntaf_codes(racerosterreg)
    team_gen(racerosterreg)
    fill_donation_ntaf_codes(racerosterdon)

    constituents = pd.DataFrame(columns=const_cols)
    gifts = pd.DataFrame(columns=gifts_cols)
    gifts_attr = pd.DataFrame(columns=gifts_attr_cols)
    #racerosterreg = clean_registration_phones(racerosterreg)

    # Need a function here to decide on weather gift is restricted or not . Plan is to have multiple unrestricted teams. along with multiple restricted
    #fills up constituent array, runs lookup of both Email and Phone Number. If none found in existing_constituents prim_add and prim_sal (FirstName LastName) is grabbed from the roster csv
    for i, row in racerosterreg.iterrows():
        date_time_obj = datetime.strptime(row['Date Registered'], '%Y-%m-%d %H:%M:%S EST')
        constituent_id = None
        prim_add = (row['First Name'] + ' ' + row['Last Name'])
        prim_sal = (row['First Name'] + ' ' + row['Last Name'])
        GFImpID = None
        if row['Phone Number']:
            constituent_id = find_matching_phone_number(row['Phone Number'])
            if constituent_id != None:
                racerosterreg.loc[i, 'found_constituent'] = True
        if constituent_id == None:
            constituent_id = find_matching_emails(row['Email'])
            if constituent_id != None:
                racerosterreg.loc[i, 'found_constituent'] = True
        if constituent_id == None:
            constituent_id = find_matching_name(row['First Name'], row['Last Name'])
            if constituent_id != None:
                racerosterreg.loc[i, 'found_constituent'] = True
        if (constituent_id == None):
            #generate const id here
            constituent_id = generate_constituent_id(row['Unique participant ID'])
        #generate gift code
        g_code = generate_gift_code(row['Event ID'], row['Confirmation No.'], row['Unique participant ID'])
        fund_id = row['ntaf']

        if not (row['Sponsor name for acknowledgement']):
            gift_desc = sponsor_gift_describer(row)
        else:
            gift_desc = registration_gift_describer(row)

            # swag handler here


        if int(row['Swag Total']) != 0:
            medal_qty = int(row['Medal (Quantity)'])
            if (int(row['Swag Total'] - 15) == 2):
                swag_gift = pd.DataFrame({'GFTAmt': [2], 'GFType': ["Cash"], 'FundID': [fund_id],'GFDate': [date_time_obj.strftime('%m/%d/%Y')], 'ConsID': [constituent_id],'GFImpID': [(g_code + str(0))]})
                gifts = gifts.append(swag_gift, ignore_index=True)
                swag_gift_attr = pd.DataFrame({'GFAttrCat': ["Gift Code"], 'GFAttrDesc': [swag_gift_describer(row)],'GFImpID': [(g_code  + str(0))]})
                gifts_attr = gifts_attr.append(swag_gift_attr, ignore_index=True)

            while medal_qty != 0 and not np.isnan(medal_qty):
                swag_gift = pd.DataFrame({'GFTAmt': [15], 'GFType': ["Cash"], 'FundID': [fund_id], 'GFDate': [date_time_obj.strftime('%m/%d/%Y')], 'ConsID': [constituent_id], 'GFImpID': [(g_code + str(medal_qty) + str(1))]})
                gifts = gifts.append(swag_gift, ignore_index=True)
                swag_gift_attr = pd.DataFrame({'GFAttrCat':["Gift Code"], 'GFAttrDesc': [swag_gift_describer(row)], 'GFImpID': [(g_code + str(medal_qty) + str(1))]})
                gifts_attr = gifts_attr.append(swag_gift_attr, ignore_index=True)
                medal_qty-=1

            if not np.isnan(row['T-shirt 2 (Quantity)']):
                paid_shirt_qty = row['T-shirt 2 (Quantity)']
                while paid_shirt_qty != 0 and not np.isnan(paid_shirt_qty):
                    swag_gift = pd.DataFrame({'GFTAmt': [25], 'GFType': ["Cash"], 'FundID': [fund_id],
                                              'GFDate': [date_time_obj.strftime('%m/%d/%Y')],
                                              'ConsID': [constituent_id],
                                              'GFImpID': [(g_code + str(medal_qty) + str(2))]})
                    gifts = gifts.append(swag_gift, ignore_index=True)
                    swag_gift_attr = pd.DataFrame({'GFAttrCat': ["Gift Code"], 'GFAttrDesc': [swag_gift_describer(row)],
                                                   'GFImpID': [(g_code + str(medal_qty) + str(2))]})
                    gifts_attr = gifts_attr.append(swag_gift_attr, ignore_index=True)
                    paid_shirt_qty-=1
        constituent = pd.DataFrame({'ImportID':[''],'PrimAddText': [prim_add], 'PrimSalText': [prim_sal], 'ConsID': [constituent_id], 'KeyInd':['I'], 'LastName': row['Last Name'], 'FirstName': row['First Name'],'AddrLines': row['Address'], 'AddrCity': row['City'], 'AddrState': row['State'], 'AddrZIP':row['ZIP/Postal Code'], "PhoneType.0" : "Home Phone", 'PhoneNum.0': row['Phone Number'], 'PhoneNum.1': row['Email'], 'PhoneType.1':'Email'})
        constituents = constituents.append(constituent, ignore_index=True)

        gift = pd.DataFrame({'GFTAmt' : row['Registration Total'],'GFType':"Cash", 'FundID': [fund_id], 'GFDate': [date_time_obj.strftime('%m/%d/%Y')], 'ConsID': [constituent_id], 'GFImpID': [g_code]})
        gifts = gifts.append(gift, ignore_index=True)

        gift_attr = pd.DataFrame({'GFAttrCat': ["Gift Code"], 'GFAttrDesc':[gift_desc], 'GFImpID': [g_code]})
        gifts_attr = gifts_attr.append(gift_attr, ignore_index=True)

    racerosterdon = clean_donation_phones(racerosterdon)
    for i, row in racerosterdon.iterrows():
        date_time = str(row['Date'])
        datetime.strptime(date_time, '%m/%d/%y %H:%M')
        constituent_id = None
        prim_add = (row['Donor first name'] + ' ' + row['Donor last name'])
        prim_sal = (row['Donor first name'] + ' ' + row['Donor last name'])
        GFImpID = None
        if row['Phone number']:
            constituent_id = find_matching_phone_number(row['Phone number'])
            print(constituent_id)
        if constituent_id == None:
            constituent_id = find_matching_emails(row['Email address'])
            print(constituent_id)
        if constituent_id == None:
            constituent_id = find_matching_name(row['Donor first name'], row['Donor last name'])
        if constituent_id == None:
            constituent_id = find_previously_generated_constituent(constituents, row)
        if (constituent_id == None):
            #generate const id here
            constituent_id = generate_constituent_id(str(row['Transaction ID']))

        g_code = (generate_gift_code( row['Event ID'], str(row['Transaction ID']), 3))
        donation_constituent = pd.DataFrame(
            {'ImportID': [''], 'PrimAddText': [prim_add], 'PrimSalText': [prim_sal], 'ConsID': [constituent_id],
             'KeyInd': ['I'], 'LastName': row['Donor last name'], 'FirstName': row['Donor first name'], 'AddrLines': row['Address'],
             'AddrCity': row['City'], 'AddrState': row['Subdivision'], 'AddrZIP': row['Postal code'],
             'PhoneNum.0': row['Phone number'], 'PhoneType.0':"Home Phone", 'PhoneNum.1': row['Email address'], 'PhoneType.1': 'Email'})
        constituents = constituents.append(donation_constituent, ignore_index=True)

        donation = pd.DataFrame({'GFTAmt': row['Received(less fees)'], 'GFType': ["Cash"], 'FundID': row['ntaf'],
                                 'GFDate': [date_time_obj.strftime('%m/%d/%Y')], 'ConsID': [constituent_id],
                                 'GFImpID': [(g_code + str(3))]})
        gifts = gifts.append(donation, ignore_index=True)
        donation_attr = pd.DataFrame({'GFAttrCat': ["Gift Code"], 'GFAttrDesc': [donation_gift_describer(row)], 'GFImpID':[(g_code + str(3))]})
        gifts_attr = gifts_attr.append(donation_attr, ignore_index=True)

    constituent_dropper(racerosterreg, constituents)
    constituents=duped_constituent_scanner(constituents)

    gift_dropper(gifts, gifts_attr)
    #gifts = gifts.drop_duplicates()
    #gifts_attr = gifts_attr.drop_duplicates()

    today = date.today()
    const_label = ("constituents" + '-' + str(today) + ".csv")
    constituents.to_csv(("media/documents/" + const_label), index=False)
    gifts_label = ("gifts" + '-' + str(today) + ".csv")
    gifts.to_csv(("media/documents/" + gifts_label), index=False)
    gifts_attr_label = ("gifts_attr" + '-' + str(today) + ".csv")
    gifts_attr.to_csv(("media/documents/" + gifts_attr_label), index=False)
    return (const_label, gifts_label, gifts_attr_label)