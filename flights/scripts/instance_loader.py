import os
import sys
from pathlib import Path
import subprocess
import pexpect
import time
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.cloud import compute_v1
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
dotenv_path = secrets_path = str(Path(__file__).resolve().parents[2])
dot_path = os.path.join(secrets_path, '.env')
load_dotenv(dot_path)

# Path to your OAuth 2.0 client secret file
CLIENT_SECRET_FILE = '/Users/ramses/Desktop/PythonProjects/MySite/mysite/secrets/client_secret_159539856046-d4p846r7l3p7p5jofijj34c8r8ca5vr6.apps.googleusercontent.com.json'
service_account_email = os.getenv('SERVICE_ACCOUNT_EMAIL')
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


secrets_path = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, secrets_path)
venv_path = os.path.join(secrets_path, '.venv')



# Authenticate and obtain credentials

def get_credentials():
    import google.auth

    credentials, project = google.auth.default()
    return credentials

def list_instances(service, project, zone):
    request = service.instances().list(project=project, zone=zone)
    instances = []
    while request is not None:
        response = request.execute()

        for instance in response['items']:
            instances.append(instance['name'])
        request = service.instances().list_next(previous_request=request, previous_response=response)
    return instances

def list_instance_templates(service, project):
    try:
        request = service.instanceTemplates().list(project=project)
        templates = []
        while request is not None:
            response = request.execute()
            for template in response.get('items', []):
                templates.append(template['name'])
            request = service.instanceTemplates().list_next(previous_request=request, previous_response=response)
        return templates
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

def get_instance_template(service, project, template_name):
    try:
        template = service.instanceTemplates().get(project=project, instanceTemplate=template_name).execute()
        return template
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None


# Create an instance from a template
def create_instance_from_template(service, project, zone, template_name, instance_name, 
                                  startup_script_path, test_script_path, venv_path, 
                                  service_account_email, data_list):
        templates = list_instance_templates(service, project)
        if template_name not in templates:
            print(f"Instance template '{template_name}' not found in project '{project}'. Available templates: {templates}")
            return None
        
        # Retrieve the instance template
        template = service.instanceTemplates().get(project=project, instanceTemplate=template_name).execute()
        
        # Extract instance properties from the template
        instance_properties = template['properties']
        
        # Correctly format the machine type URL
        machine_type = f"zones/{zone}/machineTypes/{instance_properties['machineType'].split('/')[-1]}"
        
        # Correctly format the disk type URL for each disk
        disks = instance_properties['disks']
        for disk in disks:
            if 'initializeParams' in disk and 'diskType' in disk['initializeParams']:
                disk_type = disk['initializeParams']['diskType'].split('/')[-1]
                disk['initializeParams']['diskType'] = f"zones/{zone}/diskTypes/{disk_type}"
        
        # gsutil cp gs://alliround-selenium-scripts/startup.sh /home/ramses/

        # inject necessary scripts and venv to the instance 
        startup_script = f"""#!/bin/bash
        echo "Startup script running" > /dev/console
        gsutil cp gs://alliround-selenium-scripts/flight_search_controller.py /home/ramsesloaces/
        /home/ramsesloaces/venv/bin/python3 /home/ramsesloaces/flight_search_controller.py --data '{data_list}'
        echo "Startup script completed" > /dev/console

        """
        # gsutil cp gs://alliround-selenium-scripts/test_script.py /home/ramses/
        # python3 /home/ramses/test_script.py --data '{data_list}'

        

        #gsutil cp -r gs://alliround-selenium-scripts/.venv /home/ramsesloaces/


        # when in deployment change cp to gsutil cp (and use google storage bucket link)
        

        metadata = instance_properties.get('metadata', {})
        metadata['items'] = metadata.get('items', []) + [{
            'key': 'startup-script',
            'value': startup_script
        }]

        # Define the request body for creating an instance
        instance_body = {
            "name": instance_name,
            "machineType": machine_type,
            "disks": disks,
            "networkInterfaces": instance_properties['networkInterfaces'],
            "serviceAccounts": [{
                "email": service_account_email,
                "scopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ]
            }],
            "metadata": metadata # ,
            # "tags": instance_properties.get('tags', {})
        }

        # Send the request to create the instance
        request = service.instances().insert(project=project, zone=zone, body=instance_body)
        response = request.execute()
        # print(f"Instance creation initiated. Response: {response}")
        return response




def stop_instance(service, project, zone, instance_name):
    try:
        # Request to stop the instance
        request = service.instances().stop(project=project, zone=zone, instance=instance_name)
        response = request.execute()
        return response
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None


def delete_instance(service, project, zone, instance_name):
    try:
        # Request to stop the instance
        request = service.instances().delete(project=project, zone=zone, instance=instance_name)
        response = request.execute()
        return response
    except HttpError as err:
        print(f"An error occurred: {err}")
        return None

def get_vm_status(project_id, zone, instance_name):
    """Retrieve the status of a Google Cloud VM using default credentials."""
    try:
        # Get default credentials and project ID
        credentials, project = google.auth.default()

        # Initialize the compute client with the credentials
        compute_client = compute_v1.InstancesClient(credentials=credentials)

        # Get instance details
        instance = compute_client.get(project=project_id, zone=zone, instance=instance_name)
        return instance.status
    except Exception as e:
        print(f"Error retrieving VM status: {e}")


def check_startup_completion(instance_name, zone, project_id):
    """
    Check if the startup script has completed by checking serial port output.
    """
    completion_message = "Startup script completed"
    try:
        result = subprocess.run(
            [
                "gcloud", "compute", "instances", "get-serial-port-output",
                instance_name, "--zone", zone, "--project", project_id, "--port", "1"
            ],
            capture_output=True, text=True, check=True
        )
        return completion_message in result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching serial port output: {e}")
        return False

def monitor_instance(instance_name, zone, project_id):
    """
    Periodically monitor the instance startup script status.
    """
    while True:
        if check_startup_completion(instance_name, zone, project_id):
            print("Startup script has completed!")
            break
        else:
            print("Waiting for startup script to finish...")
            time.sleep(10)  # Check every 10 seconds


def initiate_search(instance_name, data_list):
            
            project = 'alliround'  # Replace with your project ID
            zone = 'us-central1-c'  # Replace with your zone
            template_name = 'default-instance-template-1'  # Replace with your instance template name
            instance_name = instance_name # Replace with your desired instance name

            # Start up script injects necessary packages into GCP VM and runs Script 
            startup_script_path = '/Users/ramses/Desktop/PythonProjects/MySite/mysite/search/scripts/startup.sh'
            test_script_path = '/Users/ramses/Desktop/PythonProjects/MySite/mysite/search/scripts/test_script.py'
            #startup_script_url = 'gs://alliround-selenium-scripts/startup.sh'
            # test_script_url = 'gs://alliround-selenium-scripts/test.py'

            creds = get_credentials()
            service = build('compute', 'v1', credentials=creds)
            
            while True:
                instances = list_instances(service=service, project=project, zone=zone)
                if len(instances) >= 7:
                    time.sleep(10)
                else:
                    break

            instances = list_instances(service, project, zone)
            # print(instances)
            if instance_name in instances: 
                while True:
                    try:
                        response = delete_instance(service, project, zone, instance_name)
                        print("Instance was Deleted Successfully")
                        break
                    except: 
                        print("Failed to Deleted Instance")
            else:
                while True:
                    try:
                        response = create_instance_from_template(service, project, zone, template_name, instance_name, startup_script_path, test_script_path, venv_path, service_account_email, data_list)
                        print( f"Instance: {instance_name}, was Created Successfully")
                        break
                    except:
                        print("Failed to create Instance")

        
            # Check if the instance is running. If the instance is running continue to call script.
            while True:
                status = get_vm_status(project_id=project, zone=zone, instance_name=instance_name)
                print(f"Status: {status}")
                if status == "RUNNING":
                    break
                    # time.sleep(11) 
            
                    # call script and return results to django server 
            print (data_list)
            # time.sleep(60)
            monitor_instance(instance_name, zone, project)


            """while True:
                    
                command = f"gcloud compute instances describe {instance_name} --zone {zone} --format='get(metadata.items.startup-script-status)'"
                result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if "ompleted" in result.stdout:
                    print("Startup script has completed.")
                    break
                else:
                    print("Startup script is still running.")
            """
            while True:
                try:
                    response = delete_instance(service, project, zone, instance_name)
                    print("Instance was Deleted Successfully")
                    break
                except: 
                    print("Failed to Deleted Instance")
                    

            """try:
                
                call_function_command = f"gcloud compute ssh {instance_name} --zone {zone} --command 'python3 /home/ramses/test_script.py --dep {dep} --arr {arr} --dep_date {dep_date} --arr_date {arr_date}'"
                child = pexpect.spawn(call_function_command, timeout=300)
                
                # Wait for the command to complete
                child.expect(pexpect.EOF)
                
                # Get the output
                output = child.before.decode()
                print(output)
                if "Connection refused" in output:
                    print("Connection Refused.")
                else:
                    # Delete instance
                    response = delete_instance(service, project, zone, instance_name)
                    print("Instance was Deleted Successfully"if response else "Failed to Delete Instance")

                    print("Search was Completed Successfully!")
                    print("Result: ", output)
                    break
            except pexpect.TIMEOUT:
                print("Command timed out.")
            except pexpect.EOF:
                print("Unexpected end of file.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            """
            
            
            """try:
                # Define the command
                call_function_command = f"gcloud compute ssh {instance_name} --zone {zone} --command 'python3 /home/ramses/test_script.py --dep {dep} --arr {arr} --dep_date {dep_date} --arr_date {arr_date}'"

                # Execute the command with shell=True
                result = subprocess.run(call_function_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Print the output and any errors
                print("Command output:", result.stdout)
                print("Command errors:", result.stderr)

            except subprocess.CalledProcessError as e:
                # Print the error details
                print(f"An error occurred: {e}")
                print(f"Error output: {e.stderr}")"""