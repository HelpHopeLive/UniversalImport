import pandas as pd
import os
import sys
import json
import requests
from datetime import datetime
from datetime import date

def convert(import_csv, existing_const):
    today = date.today()
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.float_format', '{:.0f}'.format)
    existing_constituents = pd.read_csv(existing_const)
    raceroster = pd.read_csv(import_csv)
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


    #This will fill the django campaigns  pandas structure
    def get_django_campaign(search_term):
        print(search_term)
        headers = {'Authorization': ('Token ' + api_token)}
        if type(search_term)==float or type(search_term)==int:
            search_url=(api_url + "?campaign_id=" + str(int(search_term)))
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
    def fill_team_codes(source_data):
        for i, row in source_data.iterrows():
            if (str(row['Is team captain']) == 'Y' and str(row['Team Campaign Code']) != "nan"):
                camp_code = row['Team Campaign Code']
                team = row['Team ID - String']
                for x, row_second in source_data.iterrows():
                    if (team == row_second['Team ID - String']):
                        source_data.loc[x, 'Team Campaign Code'] = camp_code
            elif ((str(row['Is team captain']) == 'Y') and str(row['Team Campaign Code']) == "nan"):
                #query django api with first + last name here
                team = row['Team ID - String']
                django_campaign = get_django_campaign((row['First Name'] + "%20" + row['Last Name']))
                django_campaign.head()
                camp_code = django_campaign['campaign_id'].values
                for y, row_third in source_data.iterrows():
                    if (team == row_third['Team ID - String']):
                        source_data.loc[y, 'Team Campaign Code'] = camp_code


    fill_team_codes(raceroster)
    constituents = pd.DataFrame(columns=const_cols)
    gifts = pd.DataFrame(columns=gifts_cols)
    gifts_attr = pd.DataFrame(columns=gifts_attr_cols)
    #replicates the Team Campaign Id for all team member, only on captain by default
    raceroster.head()

    # Need a function here to decide on weather gift is restricted or not . Plan is to have multiple unrestricted teams. along with multiple restricted
    gift_desc = "LRCC"

    print(gift_desc)


    #fills up constituent array, runs lookup of both Email and Phone Number. If none found in existing_constituents prim_add and prim_sal (FirstName LastName) is grabbed from the givesmart csv
    for i, row in raceroster.iterrows():
        date_time_obj = datetime.strptime(row['Date Registered'], '%Y-%m-%d %H:%M:%S EST')
        constituent_id = None
        prim_add = None
        prim_sal = None
        GFImpID = None
        if row['Phone Number']:
            constituent_id = find_matching_phone_number(row['Phone Number'])
        if constituent_id == None:
            constituent_id = find_matching_emails(row['Email'])
        if (constituent_id != None ):
            constituent = find_constituent(constituent_id)
            prim_add = constituent['Name'].values[0]
            prim_sal = constituent['Name'].values[0]
        else:
            prim_add = (row['First Name'] + ' ' + row['Last Name'])
            prim_sal = (row['First Name'] + ' ' + row['Last Name'])
            #generate const id here
            constituent_id = generate_constituent_id(row['Unique participant ID'])
        #generate gift code
        g_code = generate_gift_code(row['Event ID'],row['Confirmation No.'])

        django_campaign = get_django_campaign(row['Team Campaign Code'])
        fund_id=(django_campaign['ntaf_id'].values)
        fund_id = str(fund_id).strip("['']")

        constituents.loc[i] = {'PrimAddText': prim_add, 'PrimSalText':prim_sal, 'ConsID':constituent_id, 'KeyInd':'I', 'LastName': row['Last Name'] }
        gifts.loc[i] = {'GFTAmt' : (row['Registration Total'] + row['Swag Total']),'GFType':"Cash", 'FundID': fund_id, 'GFDate': date_time_obj.strftime('%m/%d/%Y'), 'ConsID': constituent_id, 'GFImpID': g_code}
        gifts_attr.loc[i] = {'GFAttrCat':"Gift Code", 'GFAttrDesc':gift_desc, 'GFImpID': g_code}



    constituents.head()

    gifts.head()

    gifts_attr.head()


    today = date.today()

    const_label = ("constituents" + '-' + str(today) + ".csv")
    constituents.to_csv( ("media/documents/" + const_label) , index=False)

    gifts_label = ("gifts" + '-' + str(today) + ".csv")
    gifts.to_csv(("media/documents/" + gifts_label), index=False)


    gifts_attr_label = ("gifts_attr" + '-' + str(today) + ".csv")
    gifts_attr.to_csv(("media/documents/" + gifts_attr_label), index=False)

    return (const_label, gifts_label, gifts_attr_label)