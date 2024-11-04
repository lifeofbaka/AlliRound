from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db import transaction
from .models import Flight, FlightSearchBreakdown, FlightSearchCache
from .forms import FlightSearchForm
from .serializers import ResultsSerializer

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import json
import time
import subprocess
import itertools
from datetime import datetime
import sys
import os
from pathlib import Path
from collections import ChainMap
import pandas as pd
import requests
from .scripts.hello_world import get_available_routes, call_function_threads
from .scripts.instance_loader import initiate_search

import json
# load the secrets folder path 
secrets_path = str(Path(__file__).resolve().parents[1] / 'secrets')
sys.path.insert(0, secrets_path)

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# Create your views here.

@csrf_exempt
def index(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        print(latitude,longitude)
        form = FlightSearchForm(request.POST)
        if form.is_valid():
            flight_search = form.save()
            id = flight_search.id
            session_id = request.session.session_key
            print(session_id)

            if not session_id:
                request.session.create()
                session_id = request.session.session_key
                print(session_id)

            # for GCE VM copy files to bucket
            """
            subprocess.run(['gsutil','cp', 
                        '/Users/ramses/Desktop/PythonProjects/MySite/mysite/search/scripts/test_script.py',
                        'gs://alliround-selenium-scripts'], check=True)
            
            subprocess.run(['gsutil','cp', 
                        '/Users/ramses/Desktop/PythonProjects/MySite/mysite/search/scripts/flight_search_controller.py',
                        'gs://alliround-selenium-scripts'], check=True)
        
            
            query = "_".join([form.cleaned_data['departure_text'],
                              form.cleaned_data['departure_text'],
                              str(form.cleaned_data['departure_date'].strftime("%m/%d/%Y")), 
                              str(form.cleaned_data['return_date'].strftime("%m/%d/%Y"))])
            """
            # Generate a unique hash for the query
            # query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()

            # Try to retrieve from cache
            # cached_result = FlightSearchCache.objects.filter(query_hash=query_hash).first()

            start_time = time.time()
            
            # find routes for search
            available_routes = get_available_routes(source=form.cleaned_data['departure_text'],
                                                    target=form.cleaned_data['arrival_text'], 
                                                    max_stops=3)
            
            # each individual connection with airline for connection
            r_id = 1
            done = []
            chunks = []


            # Breakup available route groups into a list of all the connections for all returned routes.
            if len(available_routes) > 0:
                for route in range(len(available_routes)):
                    for i in range(len(available_routes[route][0])):
                        current_connection = available_routes[route][0][i]
                        if current_connection not in done:
                            for airline in available_routes[route][1][i]:
                                # outgoing flight 
                                item = [session_id, airline, current_connection[0], current_connection[1], 
                                                str(form.cleaned_data['departure_date'].strftime("%m/%d/%Y")), 
                                                str(form.cleaned_data['return_date'].strftime("%m/%d/%Y"))] 
                                # return flight 
                                item_2 = [session_id, airline, current_connection[1], current_connection[0], 
                                                str(form.cleaned_data['return_date'].strftime("%m/%d/%Y")), 
                                                str(form.cleaned_data['return_date'].strftime("%m/%d/%Y"))]
                                if item not in chunks:
                                    chunks.append(item)
                                if item_2 not in chunks: 
                                    chunks.append(item_2)
            
                # reduce number of times an item is searched per day by checking if it has already been searched 
                
                #check if the chunks have been looked up today 
                today = timezone.now().date()
                flight_searched = FlightSearchBreakdown.objects.filter(search_date__date=today)

                chunks_to_Search = []

                for item in chunks: 
                    dep_datetime_obj = datetime.strptime(item[4], "%m/%d/%Y")
                    dep_date_obj = dep_datetime_obj.date()

                    ret_datetime_obj = datetime.strptime(item[5], "%m/%d/%Y")
                    ret_date_obj = ret_datetime_obj.date()
                    
                    try: 
                        flight_searched.get(
                            departure_text=item[2], 
                            arrival_text=item[3], 
                            departure_date=dep_date_obj, 
                            return_date=ret_date_obj
                        )
                        print(f"Connection has been searched today:  {item}")

                        # return item from cached table 

                        

                    except FlightSearchBreakdown.DoesNotExist: 
                        # If item has not been searched, add it to chunks to search 
                        print(f"Connection has not been searched today:  {item}")
                        chunks_to_Search.append(item)

                # the results in the nodes needs to be greater than 0 
                if len(chunks_to_Search) > 0: 
                    
                    def divide_chunks(l, n):
                        # looping till length l
                        for i in range(0, len(l), n): 
                            yield l[i:i + n]

                    def flight_search_request(url, item):
                        criteria = '/?data=' + item
                        # print(criteria)
                        complete_url = url + criteria
                        while True: 
                            result = requests.get(complete_url)
                            if result.text != 'Service Unavailable': # check if container failed to load if not retry 
                                break  
                        results_dict = json.loads(result.text)
                       # not necessary for 1 item chunks 
                        if list(results_dict.values())[0] == 'Failed': # this only works for 1 item chunks if the chunk sized is changed it will fail
                            flight_search_request(url, list(results_dict.keys())[0])
                    

                    # TODO ======= Determine the best way to divde chunks ========
                    n = len(chunks_to_Search)
                    
                    chunk_lists = list(divide_chunks(chunks_to_Search, 1)) # the number of items in each chunks 
                    # print("Chunks: ", chunk_lists, "|  Searches per chunk: ", [len(i) for i in chunk_lists])

                    
                    url = 'https://flight-search-test-159539856046.us-central1.run.app' 

                    futures = []
                    with ThreadPoolExecutor() as executor:  
                        for item in chunk_lists:
                            item = ",".join(["_".join(i) for i in item])
                            futures.append(executor.submit(flight_search_request, url, item))

                    # add all completed search criteria to the searches breakdown table in database 
                    for item in chunks_to_Search: 
                        dep_datetime_obj = datetime.strptime(item[4], "%m/%d/%Y")
                        dep_date_obj = dep_datetime_obj.date()

                        ret_datetime_obj = datetime.strptime(item[5], "%m/%d/%Y")
                        ret_date_obj = ret_datetime_obj.date()
                        searched_chunk = FlightSearchBreakdown(departure_text=item[2], arrival_text=item[3], departure_date=dep_date_obj, return_date=ret_date_obj)
                        
                        with transaction.atomic():
                            searched_chunk.save()
                        
                    # working code up to here 
                """  with ThreadPoolExecutor(max_workers=7) as executor:  
                    # TODO ==== Create Search ID form field
                    for item in chunk_lists:
                        item = ",".join(["_".join(i) for i in item])
                        print(item)
                        # TODO === Initiate Search via GCP ===  
                        instance_name = "-".join([current_connection[0].lower(), current_connection[1].lower(), "-".join(
                            airline.split()).lower(), str(id)+ str(r_id)])
                        executor.submit(initiate_search, instance_name, item)
                        r_id += 1
                        # Add SubSearch to finished list
                        
                        
                        # done.append(current_connection)

                                    # Run Call Function within the Compute Engine 
                """
                                    

            combined_results_df = pd.DataFrame()
            search_result = {} 
            for item in chunks: 
                combined_dict = {}
                for item in FlightSearchCache.objects.filter(origin_code=item[2], destination_code=item[3]).values():
                    for key, value in item.items():
                        if key not in combined_dict:
                            combined_dict[key] = []
                        combined_dict[key].append(value)

                combined_results_df = pd.concat((combined_results_df, pd.DataFrame(combined_dict)), axis=0, ignore_index=True)

            
            result =combined_results_df.to_dict()

            # print(result.keys())


            
            for i in result['main_cabin_min']: 
                if str(result['main_cabin_min'][i].split("$")[-1].split(', ')[0]) != 'Not available':
                    result['main_cabin_min'][i] = '$' + str(result['main_cabin_min'][i].split("$")[-1].split(', ')[0])
                else:
                    result['main_cabin_min'][i] = str(result['main_cabin_min'][i].split("$")[-1].split(', ')[0])
            
            for i in result['premium_cabin_min']: 
                if str(result['premium_cabin_min'][i].split("$")[-1].split(', ')[0]) != 'Not available':
                    result['premium_cabin_min'][i] = '$' + str(result['premium_cabin_min'][i].split("$")[-1].split(', ')[0])
                else:
                    result['premium_cabin_min'][i] = str(result['premium_cabin_min'][i].split("$")[-1].split(', ')[0])



            # TODO ==== Join Search Results Stored in Cache ====
            # map routes and prices to a user view dictionary
            user_view_result = {}
            for route in available_routes: 
                route_flights =  []
                [route_flights.append(i) for i in list(itertools.chain.from_iterable(route[0])) if i not in route_flights]
                
                
                # print(route_flights)
                
                if len(route[0]) > 1: 
                    for n in range(len(route[0])): 

                        # TODO ==== create logic for routes with multiple flights 
                        pass
                else:
                    for flight in route[0]:
                        # find the outbound flights from the loaded cache 
                        outbound_flights = combined_results_df.loc[(combined_results_df['origin_code'] == flight[0]) & (combined_results_df['destination_code'] == flight[1])][['main_cabin_min', 'origin_depart_time', 'destination_arrival_time']]
                        
                        # add route and outbound to dictionary 
                        user_view_result['Route'] = [route_flights for i in range(len(outbound_flights))]
                        
                        
                        
                        # TODO ==== Create logic to return the cheapest flight if one way combination is greater price than round trip ====

                        return_flights = combined_results_df.loc[(combined_results_df['origin_code'] == flight[1]) & (combined_results_df['destination_code'] == flight[0])][['main_cabin_min', 'origin_depart_time', 'destination_arrival_time']]
                        
                

            end_time = time.time()

            # Calculate the elapsed time
            print(end_time - start_time)

            length =len(result['origin_code']) # used to iterate dict in user view


            return render(request, 'search/index.html', { 
                                                            'flight_results': result, #dict of results
                                                            'range': range(length),
                                                            'origin': form.cleaned_data['departure_text'],
                                                            'destination': form.cleaned_data['arrival_text'],
                                                            'departure_date': str(form.cleaned_data['departure_date'].strftime("%A, %B %d, %Y")),
                                                            })  # Redirect to a list view or success page
        


            
    else:
        form = FlightSearchForm()
    return render(request, 'search/index.html', {'form': form})
    """
    if request.method == 'POST':
        form = FlightSearchForm(request.POST)
        if form.is_valid():
                
            form.save()
            # current_search = Flight.objects.filter(departure_text='MIA').last()
            # search options from form 
            available_routes = get_available_routes(source=form.cleaned_data['departure_text'],
                                                    target=form.cleaned_data['arrival_text'], 
                                                    max_stops=3)
            results = call_function_threads(available_routes=available_routes,
                                            round_=False, 
                                            dates=[str(form.cleaned_data['departure_date'].strftime("%m/%d/%Y")),
                                                    str(form.cleaned_data['return_date'].strftime("%m/%d/%Y"))],
                                                    max_workers=4)
            
            results_df = pd.DataFrame()
            for item in results: 
                results_df = pd.concat((results_df, pd.DataFrame(item)), axis=0, ignore_index=True)

            result =results_df.to_dict()

            
            length =len(result['origin_code']) # used to iterate dict 
            # result = "Hello World"



            return render(request, 'search/index.html', { 
                                                            'flight_results': result, #dict of results
                                                            'range': range(length)
                                                            })  # Redirect to a list view or success page
        
    else:
        form = FlightSearchForm()
    return render(request, 'search/index.html', {'form': form})"""
    

@csrf_exempt  # This is necessary if you are not using DRF's CSRF handling
@api_view(['POST'])
def search_api_view(request):
    if request.method == 'POST':
        try:
            # Assuming 'result' is the key in your payload
            result = request.data.get('result')
            if not result:
                return Response({'error': 'No result data provided'}, status=status.HTTP_400_BAD_REQUEST)

            # print("Payload: ", result)
            
            for i in range(len(result['origin_code'])): 
                search_result = FlightSearchCache(origin_code=result['origin_code'][i],
                                                  destination_code=result['destination_code'][i],
                                                  origin_depart_time=result['origin_depart_time'][i],
                                                  destination_arrival_time=result['destination_arrival_time'][i],
                                                  duration=result['duration'][i],
                                                  main_cabin_min=result['main_cabin_min'][i],
                                                  premium_cabin_min=result['premium_cabin_min'][i])
                with transaction.atomic():
                 search_result.save()


            # TODO ==== store contents in cache db ====



            return Response({'status': 'Result stored in session'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the exception for debugging
            print(f"Exception occurred: {e}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)




"""
class IndexView(generic.View): 
    template_name = "search/index.html"
    context_object_name = "searched_flights"

    def get_queryset(self):
        return Flight.objects.filter(departure_text="MIA")

        
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
"""

