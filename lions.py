from file_helper import fileExists, initD
from bottrix import send_loan_room_msg, send_direct_msg, send_loan_attachment, send_attachment
from fileinput import filename
import requests
from colorama import init, Fore
from bs4 import BeautifulSoup
from datetime import datetime as dt
from datetime import date, timedelta
import pandas as pd
from tqdm import tqdm
import urllib3

initD()
tqdm.pandas(desc='Processsing DataFrame', leave=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

USER = ''
PASS = ""
loginURL = 'https://lions-ng.cisco.com/laravel/login'
cases = 'https://lions-ng.cisco.com/project/14976'
case = 'https://lions-ng.cisco.com'
today = dt.now()
stripFormat = '%d/%m/%Y'
buildFormat = '%b %d, %Y'
DONE = 'Done'
PLUS = '+'


def init():
    yesterday = today - timedelta(days=1)
    prevScrape = pd.read_excel(
        f'loaned_devices_{yesterday.day}-{yesterday.year}.xlsx')

    ...

# Logs into lions-ng
# Goes to login page
# Collects Cookies and csrf token
# Creates payload with creds and token
# Posts payload to login endpoint
# Send session to parse_cases()


def login():
    s = requests.session()
    resp = s.get(loginURL, verify=False)
    tempSoup = BeautifulSoup(resp.text, 'html.parser')
    token = tempSoup.find('meta', attrs={'name': 'csrf-token'})['content']
    payload = {'username': USER, 'password': PASS, '_token': token}
    s.post(loginURL, data=payload)
    parse_cases(s)

    ...

# Receives session
# Gets the cases page
# Soupifys the html for that page
# Collects the cases table
# Parses the cases table for <a> tags with links to specific cases
# Filters out non loan cases
# Parses partial links from a tags in loanCases list


def parse_cases(s):
    data = s.get(cases)
    soup = BeautifulSoup(data.text, 'html.parser')
    casesTable = soup.select(
        'table.table.table-hover.table-responsive')[1]  # Cases Table
    caseLinks = casesTable.select('a.btn.btn-primary')
    loanCases = [
        link for link in caseLinks if 'Loan' in link.parent.find_next_sibling('td').text]
    loanLinks = [a.get('href') for a in loanCases]
    parse_case(s, loanLinks)

    ...

# Receives session and partial Links
# loops through links
# Creates a full link from each partial
# Goes to link and soupifys the html
# Finds all divs of class ui-grid-stackable inside of a div with class of content
# The drop down div on lions case page with loan details
# Goes into the first div and selects the <a> tag with the id of req_end_date and gets its data value
# Goes into the sencond div and collects the table from within
# Collects all table rows from that table
# Loops over rows and gets all relevant data
# Device, quantity, returned quantity
# Builds loan obj from collected data and appends to loans list
# Sends loans to organize()


def parse_case(s, partialLinks):
    loans = []
    for pl in tqdm(partialLinks, desc='Parsing Case Data', leave=False):
        link = case + pl
        respData = s.get(link)
        soup = BeautifulSoup(respData.text, 'html.parser')
        divs = soup.select(
            'div.content div.ui.grid.stackable')

        date = divs[0].select_one('a#req_end_date').get('data-value')
        deviceTable = divs[1].table
        # Collect all devices if more then one device of diffrnet model is loaned out
        deviceRows = deviceTable.select('tr.requested-devices')
        for i, row in enumerate(deviceRows):
            # Collecting all data from tr
            td = row.select('tr.requested-devices > td')
            # Parseing only the td ele we need (the first two & the fourth)
            td = td[0:4]
            loan = {
                'device': td[0].text,
                'quantity': td[1].find('a').get('data-value'),
                'return_date': date,
                'returned_quantity': td[3].text,
                'case': link
            }
            loans.append(loan)
    organize(loans)
    ...

# Func to organize the scrapped data into a dataframe
# Takes the loans list
# Creates the loan dataframe
# Formats the loan dataframe return date column
# Creates a count_down column with the days between loan return date and todays day
# Checks if filename exisits
# Saves the df to excel with filename
# sends df to twoWeeksChecker()


def organize(loans):
    # fileName = f'C:\\Users\\carjames\\OneDrive - Cisco\\Documents\\Code\\CIsco Code\\Bottrix\\sheets\\loaned_devices_{today.month}-{today.day}.xlsx'
    fileName = (f'sheets\\loaned_devices_{today.month}-{today.day}.xlsx')
    loans_df = pd.DataFrame(loans)
    loans_df['return_date'] = pd.to_datetime(
        loans_df['return_date'], format=stripFormat)

    loans_df['count_down'] = loans_df['return_date'].progress_apply(lambda x: date(
        x.year, x.month, x.day) - date(today.year, today.month, today.day))
    loans_df['count_down'] = loans_df['count_down'].progress_apply(
        lambda x: f'Due in {x.days} days' if x.days >= 0 else f'{abs(x.days)} days late')
    loans_df['return_date'] = loans_df['return_date'].dt.strftime(buildFormat)

    fileExists(fileName)
    loans_df.to_excel(fileName)
    twoWeeksChecker(loans_df)
    ...
# sheets\loaned_devices_3-23.xlsx
# Func to activate Bottrix and send updates to team on loaned devivces
# Turns return date column into datetime obj again to get the days between return date and now into a list called days
# Copy loans df to create a late loans df
# loop thru days list
# Test how many days bettwen return date and now
# If 14 or less df row with same index is removed
# and added to deadline approcing list
# New filename is created for outstanding loans
# Checks if that file exisits
# Creates excel sheet for late loans
# Loop throuigh deadline approcing list
# Send loan room message about apporcing loans that need to be returned
# Checking if late loans df is empty if not send a late loans excel sheet as an attachment the loan room


def twoWeeksChecker(df):
    df['return_date'] = pd.to_datetime(df['return_date'])
    days = df['return_date'].apply(lambda x: date(
        x.year, x.month, x.day) - date(today.year, today.month, today.day))
    df['return_date'] = df['return_date'].dt.strftime(buildFormat)
    late_loans = df.copy(deep=True)
    days = [x.days for x in days]

    deadlineApprocing = []

    for i, day in enumerate(days):
        if day <= 14 and day >= 0:
            deadlineApprocing.extend(
                df.iloc[[i]].to_dict(orient='records'))
            late_loans.drop([i], inplace=True)
    fileName = f'sheets\\Outstanding_Loans_{today.month}-{today.day}.xlsx'
    fileExists(fileName)
    late_loans.to_excel(fileName)
    if len(deadlineApprocing) == 0:
        print(Fore.GREEN + '[✔]', end='')
        print('No Uppcoming Return Dates')
    else:
        for device in deadlineApprocing:
            resp = send_loan_room_msg(
                ['Loaned Devices Due:', f'\n\n\t{device["device"]}x{device["quantity"]} is {device["count_down"]} \n\t{device["returned_quantity"]} devices returned \n\tReturn Date: {device["return_date"]} \n\tCase: {device["case"]}'])
            # resp = send_direct_msg(  # Testing Code
            #     ['Loaned Devices Due:', f'\n\n\t{device["device"]}x{device["quantity"]} is {device["count_down"]} \n\t{device["returned_quantity"]} devices returned \n\tReturn Date: {device["return_date"]} \n\tCase: {device["case"]}'], "carjames@cisco.com")
        print(
            Fore.GREEN + '[+]', end='') if resp.status_code == 200 else print(Fore.RED + '[-]', end='')
        print(f'Approaching Loans Notified') if resp.status_code == 200 else print(
            'Error\n\t'+resp.text)
    if late_loans.empty:
        print(Fore.GREEN + '[✔]', end='')
        print('No Late Loans')
        return
    else:
        resp = send_loan_attachment('Outstanding Loans', fileName,)
        # resp = send_attachment('Outstanding Loans', fileName,
        #    'Y2lzY29zcGFyazovL3VybjpURUFNOnVzLWVhc3QtMl9hOmlkZW50aXR5TG9va3VwL1JPT00vOTBhOTg1ZDAtYTU2ZC0xMWVjLTliMTktMTliYjBjMTMwOTk5')  # Testing Code
        print(
            Fore.GREEN + '[+]', end='') if resp.status_code == 200 else print(Fore.RED + '[-]', end='')
        print(f'Late Loans Notified') if resp.status_code == 200 else print(
            'Error\n\t'+resp.text)
        return
    ...
    ...


login()
print('---------------------Done---------------------')
# loans = []
# organize(loans)
