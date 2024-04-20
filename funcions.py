import streamlit as st
import pandas as pd
import re


def intToHora(time):
    hours = time // 60
    minutes = time%60
    horaString = ''
    if hours < 10:
        horaString += "0" 
    horaString += str(hours) + ':'
    if minutes < 10:
        horaString += "0"
    horaString += str(minutes)
    return horaString

def horaToInt(hora):
    return int(hora.split(':')[0])*60 + int(hora.split(':')[1])

#function to process the input data about routes
def process_routes(routes_table, timeForDelivery):
    
    data = []

    for line in routes_table.splitlines():
        if not line.strip():
            continue

        route = re.split(r"\t", line)

        if len(route) != 15:  # Check for expected number of elements
            print(f"Warning: Unexpected line format: {line}")
            continue  # Skip lines with incorrect format
        #departure time in minutes
        departureTime = horaToInt(route[3])
        #arrival time in minutes
        arrivalTime = departureTime + int(route[6]) + int(route[12]) * timeForDelivery
        #process an element of the data frame and uses the correct format
        route_data = [route[0], route[2], route[10], route[3], '', intToHora(arrivalTime), int(route[6]), int(route[12]), "", departureTime]
                    
        data.append(route_data)
    
    return data


#function to process the input data about workers and their hours
def process_workers(workers_table, extra6hours, extra4hours, extra0hours):
    
    data = []

    for line in workers_table.splitlines():
        if not line.strip():
            continue
        
        worker = re.split(r"\t", line)
        
        if len(worker) != 2:  # Check for expected number of elements
            print(f"Warning: Unexpected line format: {line}")
            continue  # Skip lines with incorrect format

        if not worker[1].isdigit():
            continue #skip workers with no hours

        workingHours = (int(worker[1])/5) #convert into minutes

        #Apply the hour flexibility
        if workingHours > 6:
            workingHours *= (1 + extra6hours)
        elif workingHours > 4:
            workingHours *= (1 + extra4hours)
        else:
            workingHours *= (1 + extra0hours)
        
        worker_data = [worker[0], workingHours]

        data.append(worker_data)

        #sorts by higher amount of hours
        sorted_data = sorted(data, key=lambda x: x[1], reverse=True)
    
    #converts it into a dict
    return {i: element for i, element in enumerate(sorted_data)}


def printTimeline(timeline):
    col1, col2, col3= st.columns(3)
    c = 1
    for worker, value in timeline.items():
        if c == 1:
            with col1:
                st.write(str(worker) + ": ")
                for stop in value:
                    st.write("id: " + stop[0][8:] + " de " + str(stop[1]) + " a " + str(stop[2]))
                st.write("")
                st.write("")
            c = 2
        elif c == 2:
            with col2:
                st.write(str(worker) + ": ")
                for stop in value:
                    st.write("id: " + stop[0][8:] + " de " + str(stop[1]) + " a " + str(stop[2]))
                st.write("")
                st.write("")
            c = 3
        else:
            with col3:
                st.write(str(worker) + ": ")
                for stop in value:
                    st.write("id: " + stop[0][8:] + " de " + str(stop[1]) + " a " + str(stop[2]))
                st.write("")
                st.write("")
            c = 1
