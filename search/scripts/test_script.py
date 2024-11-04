import requests
import argparse
from concurrent.futures import ThreadPoolExecutor

def process_data_point(data_point):
    # Extract the relevant information from the data_point
    result = data_point

    # Send results to the Django API
    api_url = 'https://e6f2-2601-58a-8980-80f0-d08e-8f06-88b2-fe07.ngrok-free.app/search/api/'
    payload = {'result': result}
    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        print("Results successfully sent to Django API.")
    else:
        print(f"Failed to send results. Status code: {response.status_code}")

def hello_world(data):
    with ThreadPoolExecutor() as executor:
        
        data = data.split(',')
        contents = []
        for i in data: 
            contents.append(i.split("_"))
        # print(contents)
        
        executor.map(process_data_point, contents)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Script takes parameters from the user and sends them to the backend")

    # Add arguments
    parser.add_argument('--data', type=str, required=True, help="airline and route information for multiple routes")

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    hello_world(args.data)


