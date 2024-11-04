import time 
import os
import certifi
import undetected_chromedriver as uc
import platform
import certifi
import undetected_chromedriver as uc
from flask import Flask, request, jsonify
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor
import sys
import time
import shutil
import tempfile
import logging
from pathlib import Path
import certifi
from selenium import webdriver
import undetected_chromedriver as uc 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import math
import networkx as nx
from heapq import heappush, heappop
from concurrent.futures import ThreadPoolExecutor, as_completed


# load the secrets folder path 
import os
import sys
import time
import logging
from pathlib import Path
# secrets_path = str(Path(__file__).resolve().parents[1].parents[0] / 'secrets')
# sys.path.insert(0, secrets_path)


app = Flask(__name__)

os.environ['SSL_CERT_FILE'] = certifi.where()

def create_chrome_driver():
    options = uc.ChromeOptions()
    # options.binary_location = '/usr/bin/google-chrome'
    options.add_argument("--headless")
    # options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("detached")
    # options.add_argument("--disable-web-security")
    options.add_argument("--lang=en-US")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = uc.Chrome(options=options, driver_executable_path='./undetected_chromedriver')
    # driver = webdriver.Chrome(options= options, service=ChromeService(ChromeDriverManager().install()))

    # Inject JavaScript to modify properties
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.navigator.chrome = {
                runtime: {},
                // Add other necessary properties if needed
            };

            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            Object.defineProperty(screen, 'availWidth', {
                get: () => screen.width,
            });

            Object.defineProperty(screen, 'availHeight', {
                get: () => screen.height,
            });

            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };
        """
    })
    return driver

def american_scraper(departure='', arrival='', round_=True, dates=[], passengers=1):
    try:
        driver = create_chrome_driver()
        action = ActionChains(driver)

        # set general timeout
        wait = WebDriverWait(driver, 120) # 60 second timeout 

        # load site
        driver.get("https://www.aa.com/")
        print(driver.title)
        wait.until(EC.presence_of_element_located((By.ID,"main" ))) # wait until main page has loaded 
       
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME,"adc-cookie-banner")))
        
            #dismiss cookies 
            shadow_host = driver.find_element(By.TAG_NAME, "adc-cookie-banner") 

            shadow_root = driver.execute_script('return arguments[0].shadowRoot', shadow_host)

            inner_element = shadow_root.find_element(By.ID, "toast-dismiss-button")
            inner_element.click()
        
        except TimeoutException:
            driver.quit()
        
        if not round_:
            elem = driver.find_element(By.XPATH, '//*[@id="bookingCheckboxContainer"]/div[1]/div[2]/label/span[1]') # One-way
            elem.click()
            time.sleep(1)
        
        # enter information from the user completed form
        elem = driver.find_element(By.NAME, 'originAirport') # departure destination
        elem.click()
        
        name = platform.system()
        if name == 'Windows' or name == 'Linux':  # Windows
            elem.send_keys(Keys.CONTROL, 'a')
        else:  # MacOS
            elem.send_keys(Keys.COMMAND, 'a')
        elem.send_keys(departure)

        elem = driver.find_element(By.NAME, 'destinationAirport') # arrival destination
        elem.click()
        if name == 'Windows' or name == 'Linux':  # Windows
            elem.send_keys(Keys.CONTROL, 'a')
        else:  # MacOS
            elem.send_keys(Keys.COMMAND, 'a')
        elem.send_keys(arrival)

        elem = driver.find_element(By.NAME, 'departDate') # departure date
        elem.click()
        if name == 'Windows' or name == 'Linux':  # Windows
            elem.send_keys(Keys.CONTROL, 'a')
        else:  # MacOS
            elem.send_keys(Keys.COMMAND, 'a')
        elem.send_keys(dates[0])

        if round_:
            elem = driver.find_element(By.NAME, 'returnDate') # return date
            elem.click()
            if name == 'Windows' or name == 'Linux':  # Windows
                elem.send_keys(Keys.CONTROL, 'a')
            else:  # MacOS
                elem.send_keys(Keys.COMMAND, 'a')
            elem.send_keys(dates[1])

        elem = driver.find_element(By.ID, 'flightSearchForm.button.reSubmit') # submit
        elem.click()


        wait.until(EC.presence_of_element_located((By.CLASS_NAME,"results-grid-container" ))) # wait until main page has loaded         
        
        contents = BeautifulSoup(driver.page_source, "html.parser")

        # origin to destination
        # route = contents.find('div', {'class': 'city-pair'}).text

        # returns each flights times, stops, price, plane, and route id 
        aa_results = {'origin_code' : [], 'destination_code' : [], 
                      'origin_depart_time': [], 'destination_arrival_time': [],
                      'duration': [], 'main_cabin_min': [], 'premium_cabin_min': []}


        results = contents.find('div',{'class': 'results-grid-container'}).find_all('app-slice-details') # ,{'class': 'ng-star-inserted'})
        print(len(results))

        # previous price extraction code currently not working as of 10/10/2024 
        def previous_price_extraction(result):
                try: 
                    try:
                        main_cabin_min = result.find('button',{'class': 'btn-flight MAIN ng-star-inserted'}).find('div',{'class':'price'}).find('span').text
                    except AttributeError:
                        try:
                            main_cabin_min = result.find('div',{'class': 'btn-not-available ng-star-inserted'}).text
                        except AttributeError:
                            main_cabin_min = result.find('button',{'class': 'btn-flight MAIN disabled ng-star-inserted'}).find('div',{'class':'price'}).find('span').text
                except: 
                    main_cabin_min = "Not Available"       

                try:                                    
                    try: 
                        premium_cabin_min = result.find('button',{'class': 'btn-flight PREMIUM ng-star-inserted'}).find('div',{'class':'price'}).find('span').text
                    except AttributeError:
                        try:
                            premium_cabin_min = result.find('div',{'class': 'btn-not-available ng-star-inserted'}).text
                        except AttributeError: 
                            premium_cabin_min = result.find('button',{'class': 'btn-flight PREMIUM disabled ng-star-inserted'}).find('div',{'class':'price'}).find('span').text
                
                except:
                    premium_cabin_min = "Not Available"
        
        def divide_chunks(l, n):
                        # looping till length l
                        for i in range(0, len(l), n): 
                            yield l[i:i + n]

        def current_price_exctraction(result, aa_results):  # created on 11/01/2024  extracts prices from buttons
            try: 
                btn_content = result.find_all('div', {'class': 'cell auto'})
                btn_contents_txt = []
                
                for btn in btn_content: 
                    btn_contents_txt.append(btn.find('div').text)

                for txt in list(divide_chunks(btn_contents_txt,2)): 
                    aa_results['main_cabin_min'].append(txt[0])
                    aa_results['premium_cabin_min'].append(txt[1])
            except AttributeError: 
                print("Attribute Error in cabin prices button: function current_price extraction ")

        for result in results: 

            try:
                origin_code = result.find('div', {'class': 'cell shrink origin'}).find('div',{'class':'city-code'}).text
                
            except AttributeError: 
                print("Attribbute error in origin code")
            try:
                origin_depart_time = result.find('div', {'class': 'cell shrink origin'}).find('div',{'class':'time'}).text
            except AttributeError: 
                print("Attribbute error in departure time")
            try:
                destination_code = result.find('div', {'class': 'cell large-3 destination'}).find('div',{'class':'city-code'}).text
            except AttributeError: 
                print("Attribbute error in destination code")
            try:
                destination_arrival_time = result.find('div', {'cell large-3 destination'}).find('div',{'class':'time'}).text
            except AttributeError: 
                print("Attribbute error in arrival time")


            try:
                duration = result.find('div',{'class': 'duration'}).text
            except AttributeError: 
                print("Attribute Error in duration")
            
            
            # Insert price extraction here
            
                

            aa_results['origin_code'].append(origin_code)
            aa_results['destination_code'].append(destination_code)
            aa_results['origin_depart_time'].append(origin_depart_time)
            aa_results['destination_arrival_time'].append(destination_arrival_time)
            aa_results['duration'].append(duration)
            current_price_exctraction(result, aa_results) # this includes the two lines that have been commented below 
            # aa_results['main_cabin_min'].append(main_cabin_min)
            # aa_results['premium_cabin_min'].append(premium_cabin_min)
            
        driver.quit()
        return aa_results
    except TimeoutException:
        raise TimeoutException("Site did not load within limit.")
    except Exception as e: 
        # error loacating driver 
        print(f"Failed to initiate driver.:  {e}")
        try:
            driver.quit()
        except Exception as e:
            print(f"Failed to close driver:   {e}")

def united_scraper(departure='', arrival='', round=True, dates=[], passengers=1):
    try:
        driver = create_chrome_driver()
        action = ActionChains(driver)

        # set general timeout
        wait = WebDriverWait(driver, 120) # 60 second timeout 

        # load site
        driver.get("https://www.aa.com/")
        print(driver.title)   





        united_results = {'origin_code' : [], 'destination_code' : [], 
                      'origin_depart_time': [], 'destination_arrival_time': [],
                      'duration': [], 'main_cabin_min': [], 'premium_cabin_min': []}





        driver.quit()
        return united_results
    except TimeoutException:
        raise TimeoutException("Site did not load within limit.")
    except Exception as e: 
        # error loacating driver 
        print(f"Failed to initiate driver.:  {e}")
        try:
            driver.quit()
        except Exception as e:
            print(f"Failed to close driver:   {e}")

def delta_scrapper(departure='', arrival='', round=True, dates=[], passengers=1):
    pass


# --------------------------------------------------------------------------------------------------------------

# available airlines and airline_search_dicr.keys should have the same values.

# Create graph network 
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# Determine Distance between nodes
def path_distance(graph, path):
    total_distance = 0
    for i in range(len(path) - 1):
        lat1, lon1 = graph.nodes[path[i]].get('latitude'), graph.nodes[path[i]].get('longitude')
        lat2, lon2 = graph.nodes[path[i + 1]].get('latitude'), graph.nodes[path[i + 1]].get('longitude')
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return float('inf')  # Return infinite distance if any node lacks coordinates
        total_distance += haversine(lat1, lon1, lat2, lon2)
    return total_distance

# Establish bounds for node to node lat and long
def is_within_bounds(node_lat, node_lon, source_lat, source_lon, target_lat, target_lon, lat_padding=1, long_padding=1):
    min_lat = min(source_lat, target_lat) - lat_padding
    max_lat = max(source_lat, target_lat) + lat_padding
    min_lon = min(source_lon, target_lon) - long_padding
    max_lon = max(source_lon, target_lon) + long_padding
    return min_lat <= node_lat <= max_lat and min_lon <= node_lon <= max_lon

# find the stops for each node
def find_paths_with_stops(graph, source, target, max_stops, exclude_nodes=None, exclude_lat=None, lat_padding=1, long_padding=1, max_routes=10):
    source_lat, source_lon = graph.nodes[source].get('latitude'), graph.nodes[source].get('longitude')
    target_lat, target_lon = graph.nodes[target].get('latitude'), graph.nodes[target].get('longitude')
    source_city = graph.nodes[source].get('city')
    target_city = graph.nodes[target].get('city')

    queue = []
    heappush(queue, (0, [source], {source_city}))
    paths = []

    while queue:
        current_distance, current_path, visited_cities = heappop(queue)
        current_node = current_path[-1]

        if current_node == target and len(current_path) - 1 <= max_stops:
            paths.append((current_path, current_distance))
            if len(paths) == max_routes:
                break

        if len(current_path) - 1 >= max_stops:
            continue

        for neighbor in graph.neighbors(current_node):
            lat_ = graph.nodes[neighbor].get('latitude')
            lon_ = graph.nodes[neighbor].get('longitude')
            city = graph.nodes[neighbor].get('city')

            if lat_ is None or lon_ is None or city is None:
                continue
            if city in visited_cities:
                continue
            if not is_within_bounds(lat_, lon_, source_lat, source_lon, target_lat, target_lon, lat_padding=lat_padding, long_padding=long_padding):
                continue
            if neighbor not in current_path:
                if exclude_nodes is None or graph.nodes[neighbor].get('country') not in exclude_nodes:
                    if exclude_lat is None or lat_ < exclude_lat:
                        new_path = current_path + [neighbor]
                        new_distance = current_distance + haversine(graph.nodes[current_node].get('latitude'), graph.nodes[current_node].get('longitude'), lat_, lon_)
                        new_visited_cities = visited_cities.copy()
                        new_visited_cities.add(city)
                        heappush(queue, (new_distance, new_path, new_visited_cities))

    return paths


# Example usage:
# graph = nx.Graph()
# Add nodes and edges to the graph, including 'latitude', 'longitude', and 'city' attributes for each node
# result = find_paths_with_stops(graph, source_node, target_node, max_stops, exclude_nodes, exclude_lat, lat_padding, long_padding)


# keys must match list of airlines in get_available_routes() 
airline_search_dict = {'American Airlines': american_scraper} # , 'United Airlines': united_scraper} # , 'Delta Air Lines': delta_scrapper} # , "All Nippon Airways": aa_test}

# return routes to search (uses find_paths_with_stops)
def get_available_routes(source, target, max_stops): 
    # available airlines list needs to match airline_search_dict
    available_airlines = ['American Airlines'] # , 'Delta Air Lines', 'Frontier Airlines', 'All Nippon Airways']
    # Countries to exclude from searches unless in destination 
    exclude =['Cuba', 'Myanmar', 'Iran', 'Yemen', 'Afghanistan', 'Iraq', 'Russia', 'South Sudan', 'Somalia', 'Mali', 'Central African Republic']

    #load data
    from route_data.load_routes import codes_found, routes_with_cords, airport_routes

    codes = codes_found['Airport Code'].to_list()
    lat = codes_found['Latitude'].to_list()
    long = codes_found['Longitude'].to_list()
    country = codes_found['Country Name'].to_list()
    city = codes_found['City Name'].to_list()

    depatures_cords = routes_with_cords['Departure_Airport_IATA'].to_list()
    arrivals_cords = routes_with_cords['Arrival_Airport_IATA'].to_list()

    # Create routes network 
    G = nx.Graph()

    # Create nodes
    for i in range(len(codes)):
        G.add_node(codes[i], latitude=lat[i], longitude=long[i], country=country[i], city=city[i])

    # Connect nodes
    for i in range(len(depatures_cords)):
        G.add_edge(depatures_cords[i], arrivals_cords[i])


    # Get available routes starts here

    target_country = G.nodes[target].get('country')
    if target_country in exclude: 
        exclude.remove(target_country)

    # Find all possible routes from source to target with specified number of stops and max number of routes
    routes = find_paths_with_stops (G, source, target, max_stops, lat_padding= 10, long_padding=40, exclude_nodes=exclude, max_routes=30)

    # create list of routes broken up by flight 
    routes_returned = [ [] for i in range(len(routes))]
    for i in range(len(routes)):
        for j in range(len(routes[i][0])):
            if j == len(routes[i][0]) -1:
                break
            else: 
                routes_returned[i].append([routes[i][0][j], routes[i][0][j+1]])

    # Added airlines to routes based on the airport routes database 
    routes = [[] for i in range(len(routes_returned))]
    for route in range(len(routes_returned)):
        airlines =[]
        for flight in routes_returned[route]: 
            flight_airlines = airport_routes.loc[(airport_routes['Departure_Airport_IATA'] == flight[0]) & (airport_routes['Arrival_Airport_IATA']==flight[1])]['Connection_Airline'].to_list()
            airlines.append(flight_airlines)
        
        if any(len(elem) == 0 for elem in airlines):
                pass
        else:
            for i in range(len(routes_returned[route])):
                    stripped_airlines = []
                    for route_airlines in airlines: 
                        stripped_route_airlines = []
                        for airline in route_airlines:
                            a = airline.strip(" ")
                            stripped_route_airlines.append(a)
                        stripped_airlines. append(stripped_route_airlines)
                    routes[route].append(stripped_airlines)
        routes[route].append(routes_returned[route])
    routes = [list(reversed(i)) for i in routes if len(i) > 0]

    #filter out routes with airlines who do not have a constructed sript
    available_routes = []
    for route in range(len(routes)):
        result =[]
        flights_in_route = []
        try:
            flight_route = routes[route][1]
        except:
            flight_route = routes[route][0]
        for flight in flight_route:
                airlines_in_flight = []
                for airline in flight: 
                    if airline in available_airlines:
                        airlines_in_flight.append(airline)
                flights_in_route.append(airlines_in_flight)
        
        
        if all(len(connection) >= 1 for connection in flights_in_route):
            available_routes.append([routes[route][0], flights_in_route])



    return available_routes


# Calls specific airline scrappers 
def call_function(contents, round_=False, passengers=1):
    
    try:
        print(contents)
        print(f"Running Search on {contents[1]} for connection {contents[2]} to {contents[3]}")
        func, params = airline_search_dict[contents[1]], (contents[2], contents[3], round_, [contents[4],contents[5]], passengers)
        result= func(*params)  # Call the function with the provided parameters and the additional parameter
        # print(result)
        # print(f"Success after {attempts +1 } attempts")
        if result is not None:
            return [contents, send_payload(result)]
        else: 
            return [contents,'Failed']
    except:
        return [contents,'Failed']
        

def send_payload(result):
    if result is not None:
        api_url = 'https://fee7-147-70-17-36.ngrok-free.app/flights/api/' 
        payload = {'result': result}
        print(payload)
        response = requests.post(api_url, json=payload)

        if response.status_code == 200:
            print("Results successfully sent to Django API.")
            return 'Success'
        else:
            print(f"Failed to send results. Status code: {response.status_code}")
            return 'Failed'
    else:
        return 'Failed'

# needs to run get_available_routes before running 
@app.route('/') #, methods=['GET'])
def initiator():
    data = request.args.get('data') #arguement 
    contents = []
    results = {}
    if data: 
            futures = []
            data = data.split(',')
            for i in data: 
                    contents.append(i.split("_"))
            
            with ThreadPoolExecutor(max_workers=7) as executor:
                for content in contents:
                    futures.append(executor.submit(call_function, content))
                    
                
                for future in as_completed(futures):
                    response = future.result()
                    results['_'.join(response[0])] = response[1]
            return results
    else: 
        return "Data Not Found."





# url = os.environ.get("url")
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
# hello_selenium()