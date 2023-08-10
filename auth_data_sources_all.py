import requests
import urllib3
import configparser
import csv
import os
import json
from itertools import zip_longest


# Disable SSL certificate verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Take user input -start of script 
print("\033[1mMIGRATE BULK DATA SOURCES FROM ONE COLLECTOR VM TO ANOTHER \033[0m")
print ("=============================================================")
print ("=============================================================\n")
print ("Follow the instructions below :-\n")
print("Input Old and New Collector Name (Format - Collector_xxxxxxxx)","\n")
user_input_old_collector = input("Enter Old Collector VM : ")
user_input_new_collector = input("Enter New Collector VM : ")

print("\n")

#user_input_old_collector = "Collector_10.220.233.39" #I41370WMY333DJ6QPKQOM546LI
#user_input_new_collector = "Collector_10.220.235.75" #IEV141I3IFNA8SJDP07FKPP9WJ

config = configparser.ConfigParser()
config.read("api_config.ini")

# Function to call the private API and retrieve the authentication token
def get_auth_token(api_url, username, password):
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(api_url, json=payload, verify=False)
    if response.status_code == 200:
        token = response.json().get('csrfToken')
        cookie = response.cookies['VRNI-JSESSIONID']
        return token, cookie 
    else:
        return None

# Function to call the GET API using the authentication token
def call_get_api(api_url, auth_token,cookie):
    headers = {
        'Content-Type' : 'application/json',
        'x-vrni-csrf-token': auth_token,
        'Cookie': f'VRNI-JSESSIONID={cookie}'
    }
    response = requests.get(api_url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to update the data source    
def call_update_data_source (api_url, auth_token, cookie, obj, data_source, new_collector_VM):
            headers = {
                'Content-Type' : 'application/json',
                'x-vrni-csrf-token': auth_token,
                'Cookie': f'VRNI-JSESSIONID={cookie}'
                }    
            key_values = []
            for key, value in obj.items():
                if key == "_collectorId":
                     key_value = {
                        "key": key,
                        "value": new_collector_VM
                }
                else:     
                    key_value = {
                        "key": key,
                        "value": value
                }
                key_values.append(key_value) 
            payload = {
                 "dataSource" : data_source,
                 "keyValueList" : key_values 
            }
            json_payload = json.dumps(payload)
            if json_payload is not None:
                response = requests.post(api_url, headers=headers, json=payload, verify=False)  
                if response.status_code == 200:
                    return response.json
                else :
                    return None 
            else:
                return None

# Function to create the data source csv file
def create_csv(data):
    data_source_csvfilename = None
    key_to_check_subtype = 'DS_SUB_TYPE'
    key_to_check_snmp = '_snmp_metric_enabled'
    org_dataSource = data['dataSource']
    newkey_flag = False
    
    for key_value_dict in data['keyValueList']:
        if isinstance(key_value_dict, dict) and 'key' in key_value_dict and key_value_dict['key'] == key_to_check_subtype:
            data_source_csvfilename = key_value_dict['value']

    if data_source_csvfilename is None:
        data_source_csvfilename = data['dataSource']

    for key_value_dict in data['keyValueList']:
        if isinstance(key_value_dict, dict) and 'key' in key_value_dict and key_value_dict['key'] == key_to_check_snmp:
            snmpflag = key_value_dict['value']
            if snmpflag == 'true':
                data_source_csvfilename = data_source_csvfilename + 'snmp'

    # Defining the CSV file path and field names
    csv_file = f'{data_source_csvfilename}.csv'

    # Check if the CSV file exists and get existing headers
    existing_headers = []
    if os.path.exists(csv_file):
        with open(csv_file, mode="r", newline="") as file:
            reader = csv.reader(file)
            if reader:
                existing_headers = next(reader, [])
    
    # Prepare the list of keys and values to write
    keys_to_write = existing_headers.copy()
    values_to_write = [''] * len(existing_headers)  # Initialize with empty strings

    for key_value_dict in data['keyValueList']:
        key = key_value_dict.get('key', '')
        value = key_value_dict.get('value', '')

        if key:
            if key in existing_headers:
                # Update the value for existing keys
                index = existing_headers.index(key)
                values_to_write[index] = value  # Update value at the right index
            else:
                # Append new keys to the header row and update values accordingly
                keys_to_write.append(key)
                # Extend values_to_write with empty strings for new keys
                values_to_write.extend([''] * (len(keys_to_write) - len(values_to_write)))
                # Update the value at the correct index for the new key
                index = keys_to_write.index(key)
                values_to_write[index] = value
                newkey_flag = True
    # If the CSV file does not exist, create it and write the header row
    if newkey_flag:
        if not os.path.exists(csv_file):
            with open(csv_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(keys_to_write)
        else:
            # Read the existing header from the CSV file
            with open(csv_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                existing_headers = next(reader)

        # Merge the existing header with the new keys
        merged_header = existing_headers + [key for key in keys_to_write if key not in existing_headers]

        # Write the merged header back to the CSV file
        with open(csv_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(merged_header)
    # Write the data to the CSV file
    with open(csv_file, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(values_to_write)  # Write the corresponding values on the next row

    print(f"CSV file '{csv_file}' updated successfully!")
    return data_source_csvfilename, org_dataSource

# Function to create update data source request for API
def form_datasource_update_request(data_source):
    keys_to_skip = ['lastModifiedTimestamp','lastActivityTimestamp','lastConfigActivityTimestamp',
                'thumb.print','healthErrorCode' , 'healthError','healthStatus', 
                'certificate','vmCount','skip.certificate.validation']
    
    filename = data_source + ".csv"   
    with open( filename, 'r') as file:
        reader = csv.DictReader(file)
        payload_keyvalueList = {}
        # Skip the keys to be skipped
        filtered_row = {key: value for key, value in row.items() if key not in keys_to_skip}
        
        # Create payload
        for key, value in filtered_row.items():
            payload_keyvalueList[key] = value  
        if payload_keyvalueList is not None:
                return payload_keyvalueList
        else:
                return None

# Function to update the passwords in the CSV files
def write_to_specific_header(file_path, pwd_header_array, data_to_write):
    # Check if the CSV file exists
    if not os.path.isfile(file_path):
        print(f"CSV file '{file_path}' not found. Skipping update.")
        return

    # Read the existing CSV file and get the header names
    existing_headers = []
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        if not reader:
            print(f"CSV file '{file_path}' is empty. Skipping update.")
            return
        existing_headers = next(reader)

    # Find the columns indices to update for all headers in headers_to_search
    columns_indices_to_update = [existing_headers.index(header) for header in pwd_header_array if header in existing_headers]

    if (file_path == "CISCON7K") :
        print (existing_headers)
        print (columns_indices_to_update)

    if not columns_indices_to_update:
        print(f"No headers found in CSV '{file_path}' to update. Skipping update.")
        return

    # Update the CSV file rows (skip the header row)
    updated_rows = []
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        updated_rows.append(next(reader))  # Add the header row as is
        for row in reader:
            for index in columns_indices_to_update:
                row[index] = data_to_write
            updated_rows.append(row)

    # Write the updated data back to the CSV file
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(updated_rows)

# Main code
if __name__ == '__main__':

    # Read IP address and port from the config file
    ip_address = config.get("API", "ip_address")
    port = config.get("API", "port")
    apiValue = config.get("API","authapi")
    apiValue1 = config.get("API", "datasourceALL")
    updateDataSource = config.get("API", "updateDataSourceURL")
    getCollectorIDURL = config.get("API", "getCollectorIDURL")

    # API URLs
    private_api_url = f"https://{ip_address}:{port}/{apiValue}"
    getDataSouces_api_url = f"https://{ip_address}:{port}/{apiValue1}"
    update_Data_source_url = f"https://{ip_address}:{port}/{updateDataSource}"
    getCollectorID_api_url = f"https://{ip_address}:{port}/{getCollectorIDURL}"

    # Credentials for the private API
    username = config.get("API","username")
    password = config.get("API","password")
    
    #initalize varirables
    old_collector_VM = None
    new_collector_VM = None
    datasource_array =[]
    data_source = None
    # Call the private API to obtain the authentication token
    auth_token,cookie = get_auth_token(private_api_url, username, password)
    print('Generated new auth token -',auth_token,"\n")

    if auth_token:

        #Call the GET API to get nodeID from user input of collector name
        collectorid_response = call_get_api(getCollectorID_api_url, auth_token, cookie)
        for item in collectorid_response:
                  nameCollector = item['name']
                  if (nameCollector == user_input_old_collector):
                        old_collector_VM = item['nodeId']       
                  elif (nameCollector == user_input_new_collector):
                       new_collector_VM = item['nodeId'] 
       
        # Call the GET API for fetching data sources using the authentication token
        response = call_get_api(getDataSouces_api_url, auth_token,cookie)   
        #print (response)
        for item in response:
                collector_id = None
                model_key = None
                dpID = None
                host = None
                nickName = None
                dpState = None
                for kv in item["keyValueList"]:
                    data_source = item['dataSource']
                    if kv["key"] == "dpState":
                        dpState = kv["value"]
                    if kv["key"] == "_collectorId":
                        collector_id = kv["value"]
                    if kv["key"] == "modelKey":
                        model_key = kv["value"]
                    if kv["key"] == "dpId":
                        dpID = kv["value"]
                    if kv["key"] == "HOST":
                        host = kv["value"]
                    if kv["key"] == "nickName":
                        nickName = kv ["value"]
                #print (collector_id ,"also", host, "also more", model_key)
                #print (old_collector_VM)
                    if kv["key"] == "dpState":
                        dpState = kv["value"]
                if collector_id == old_collector_VM and data_source is not None and model_key is not None and dpState == 'ACTIVE':
                    #create CSV file 
                    data_source_response,org_datasource = create_csv(item) 
                    if data_source_response in datasource_array:
                        continue
                    else:
                        datasource_array.append(data_source_response)                        
                else:
                    print("Collector ID not matching with the input from user.")   
        # prompt user to update CSV files with password/paraphase for further processing
        user_input = input ("All data sources has the common password? (yes/no)")
        if user_input.lower() == "yes":
        #take commmon password as input from user and update all files with this value
            user_input = input ("Enter the password: ")
            #print (datasource_array)  
            for data_source_response in datasource_array:
                filename = data_source_response + ".csv"   
                pwd_header_array = {'PWD', 'N5K_PWD', '_snmp_auth_pass','N7K_PWD'}
                response_csvupdate = write_to_specific_header(filename, pwd_header_array,user_input)    
        if user_input.lower() == "no":
            print ("You will have to update them manually", "\n")   
        
        user_input = input("Have you reviewed/update CSV files manually ? (yes/no): ")
        if user_input == "yes":  
            for data_source_response in datasource_array:
                filename = data_source_response + ".csv"   
                with open(filename, "r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        org_datasource = row ['dpId']
                        parts = org_datasource.split('_')
                        data_source = parts[0]
                        new_payload = form_datasource_update_request(data_source_response)
                        print ("Migrating Data Source ",host, "of Type", data_source_response)
                        response = call_update_data_source(update_Data_source_url, auth_token, cookie, new_payload, data_source,new_collector_VM)
                    if response:
                         # Process the response from the GET API
                        print("Migration Completed for", host)
                        print("\n")
                    else:
                        print("Migration Failed")    
        if user_input == "no" :
            print("Exiting from migration. Thank you")        
    else:
        print('Error: Failed to obtain the authentication token.')
