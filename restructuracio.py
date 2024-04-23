import streamlit as st
import pandas as pd
import openpyxl as opxl
import re

def intToHora(time):
    hours = time // 60
    minutes = time%60
    return f"{hours:02d}:{minutes:02d}"

def horaToInt(hora):
    return int(hora.split(':')[0])*60 + int(hora.split(':')[1])



def process_input():
    """
    Function to get user inputs for various parameters related to shift scheduling.

    Returns:
        input_variables: A dictionary containing information about all variables to show later on the Excel.
    """
        
    #columns
    col1, col2 = st.columns(2)

    input_variables = {} #Info about all variable to show later on the excel

    with col1:

        #time to start shift
        timeToStartShift = int(st.text_input("Temps abans de començar el torn", 12))
        input_variables["Temps Inici Torn"] = timeToStartShift
        #time to end Shift
        timeToEndShift = int(st.text_input("Temps després d'acabar el torn", 5))
        input_variables["Temps Fi Torn"] = timeToEndShift
        #time between deliveries
        timeForDelivery = int(st.text_input("Temps per entrega", 7))
        input_variables["Temps per Paquet"] = timeForDelivery
        #time between routes
        timeBetweenRoutes = int(st.text_input("Temps entre rutes", 10))
        input_variables["Temps entre rutes"] = timeBetweenRoutes
        #Represents the amount of time by which one departs earlier than the scheduled departure time
        earlyDepartureTimeMarginPriority = int(st.text_input("Marge de temps de sortida abans del previst - RUTES PRIORITARIES", 10))
        input_variables["Marge abans - W"] = earlyDepartureTimeMarginPriority
        #Represents the amount of time by which one departs later than the scheduled departure time
        delayedDepartureTimeMarginPriority = int(st.text_input("Marge de temps de sortida despres del previst - RUTES PRIORITARIES", 5))
        input_variables["Marge despres - W"] = delayedDepartureTimeMarginPriority
        #Represents the amount of time by which one departs earlier than the scheduled departure time
        earlyDepartureTimeMarginNoPriority= int(st.text_input("Marge de temps de sortida abans del previst - RUTES NO PRIORITARIES", 25))
        input_variables["Marge abans - No W"] = earlyDepartureTimeMarginNoPriority
        #Represents the amount of time by which one departs later than the scheduled departure time
        delayedDepartureTimeMarginNoPriority = int(st.text_input("Marge de temps de sortida despres del previst - RUTES NO PRIORITARIES", 15))
        input_variables["Marge despres - No W"] = delayedDepartureTimeMarginNoPriority

    with col2:

        #Maximum time before an worker gets assigned another route
        maxWaitTimeBetweenRoutes = int(st.text_input("Màxim temps d'espera entre rutes", 20))
        input_variables["Temps maxim espera"] = maxWaitTimeBetweenRoutes
        #max time to enter the first route early
        firstRouteMaxEarlyDepartureTime = int(st.text_input("Marge de temps de sortida abans del previst de la primera ruta del torn", 10))
        input_variables["Marge primera ruta torn"] = firstRouteMaxEarlyDepartureTime
        #Global maximum of working hours
        globalMaxhours = int(st.text_input("Maximes hores globals per treballador", 9))
        input_variables["Maxim Hores Global"] = globalMaxhours
        #extra hours
        extra6hours = int(st.text_input("flexibilitat horaria treballadors +6", 10))/100
        input_variables["Flexibilitat +6"] = extra6hours
        extra4hours = int(st.text_input("flexibilitat horaria treballadors +4", 20))/100
        input_variables["Flexibilitat +4"] = extra4hours
        extra0hours = int(st.text_input("flexibilitat horaria treballadors menys de 4 hores", 20))/100
        input_variables["Flexibilitat -4"] = extra0hours
    
    return input_variables

def process_routes(timeForDelivery):
    """
    Processes the input data about routes, 
    calculating arrival times and creating a list of processed routes.

    Args:
        delivery_time_multiplier: Multiplier for delivery time.

    Returns:
        List of processed routes, or None if there's an error.
    """

    #table with routes to order
    input_routes = st.text_area("taula amb les rutes")

    if input_routes:

        processed_routes = []

        for line in input_routes.splitlines():
            if not line.strip():
                continue

            route = re.split(r"\t", line)

            if len(route) != 15:  # Check for expected number of elements
                st.error(f"Warning: Unexpected line format: {line}")
                continue  # Skip lines with incorrect format
            #departure time in minutes
            departureTime = horaToInt(route[3])
            #arrival time in minutes
            arrivalTime = departureTime + int(route[6]) + int(route[12]) * timeForDelivery
            #process an element of the data frame and uses the correct format
            priority = ' w ' in route[0].lower()
            
            processed_route = [route[0],priority, route[2], route[10], route[3], '', intToHora(arrivalTime),'', int(route[6]), int(route[12]), '',"", departureTime, 0]
                        
            processed_routes.append(processed_route)
        
        return pd.DataFrame(processed_routes,
                        columns=["Id", "Prioritari", "Data", "Hub", "Hora Inici Ruta Plnif",
                                    "Hora Inici Ruta Real", "Hora Fi Ruta", "Inici Seguent Ruta",
                                    "Temps ruta", "Num Entregues","Assignació", "Assignacio", "order", "Plnif vs Real Min"])
            
    return None

#function to process the input data about workers and their hours
def process_workers(extra6hours, extra4hours, extra0hours):
    """
    Processes the input data about workers and their hours, 
    applying flexibility based on working hours and returning a dictionary.

    Args:
        workers_table: String containing the workers data.
        extra_6hours: Flexibility multiplier for workers with more than 6 hours.
        extra_4hours: Flexibility multiplier for workers with 4 to 6 hours.
        extra_0hours: Flexibility multiplier for workers with less than 4 hours.

    Returns:
        Dictionary mapping worker names to their working hours with flexibility applied.
    """

    input_workers = st.text_area("Informació hore de feina empleats ")
    
    if input_workers: 
        
        processed_workers = []

        for line in input_workers.splitlines():
            if not line.strip():
                continue
            
            worker = re.split(r"\t", line)
            
            if len(worker) != 2:  # Check for expected number of elements
                st.error(f"Warning: Unexpected line format: {line}")
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
            
            processed_worker = [worker[0], workingHours]

            processed_workers.append(processed_worker)

        #sorts by higher amount of hours
        sorted_workers = sorted(processed_workers, key=lambda x: x[1], reverse=True)
        
        #converts it into a dict
        return {i: element for i, element in enumerate(sorted_workers)}
    
    return {}


def assign_routes_to_workers(processed_Routes_DF, workers_Schedule, iVAr):
    #divide the dataframe into smaller, each one pertaining to a different hub
    dfj_hub = dfj_hub.groupby("Hub")
    
    dfj_general = []

    #List with info of entry and exit times, and total hours for each worker
    pre_dft = []
    #map with all the workers and their last route finish time
    workers = {}
    #timeline for each worker
    timeline = {}
    
    #Total number of workers
    totalworkers = 0
    
    for hub, dfj in dfj_hub:
        #sort by delivery exit time
        dfj = dfj.sort_values(by="order")
        

        #sorts entries by Hub and Start Time

        for index, row in dfj.iterrows():
            #worker asigned to the route
            asignedTo = -1
            #expected initial time of the route
            expectedInitialTime = horaToInt(row["Hora Inici Ruta Plnif"])
            
            if row["Prioritari"]:
                maxDelayedInitialTime = expectedInitialTime + delayedDepartureTimeMarginPriority #maximum late time to start the route
                maxEarlyInitialTime = expectedInitialTime - earlyDepartureTimeMarginPriority #maximum early time to start the route
            else:
                maxDelayedInitialTime = expectedInitialTime + delayedDepartureTimeMarginNoPriority  #maximum late time to start the route with added non-priority margin
                maxEarlyInitialTime = expectedInitialTime - earlyDepartureTimeMarginNoPriority #maximum early time to start the route with added non-priority margin
                
            #time to complete the route
            timeToCompleteRoute = row["Temps ruta"] + row["Num Entregues"] * timeForDelivery

            #end time of the route
            endTime = horaToInt(row["Hora Fi Ruta"]) + timeBetweenRoutes

            for t, value in workers.items(): #check if any worker is available
                
                

                available = value[0] < maxDelayedInitialTime #check if worker has ended route before max delayed time
                
                if t in database_workers:
                    hoursLeftShift = (pre_dft[value[1]][4] + timeToCompleteRoute/60) <= min(database_workers[t][1], globalMaxhours) #Hours left to the shift
                else: 
                    hoursLeftShift = (pre_dft[value[1]][4] + timeToCompleteRoute/60) <= globalMaxhours

                exceededMaxWaitTime = (maxEarlyInitialTime - value[0]) < maxWaitTimeBetweenRoutes #worker waiting without a route

                correctHub = workers[t][2] == row['Hub']

                if available and hoursLeftShift and exceededMaxWaitTime and correctHub:

                    #assign the job to worker t, and update the corresponding data structures
                    asignedTo = t

                    routeStartTime = max(value[0], maxEarlyInitialTime) #Start time of the route

                    dfj.at[index, "Hora Inici Ruta Real"] = intToHora(routeStartTime) #update the table with the actual start time of the route
                    
                    endTime = routeStartTime + timeToCompleteRoute + timeBetweenRoutes #time when the worker can start the next route

                    dfj.at[index, "Hora Fi Ruta"] = intToHora(routeStartTime + timeToCompleteRoute) #update the table with the actual end time of the route
                    dfj.at[index, "Plnif vs Real Min"] = -(horaToInt(row["Hora Inici Ruta Plnif"]) - routeStartTime) #difference of starting time between plan and actual
                    dfj.at[index, "Inici Seguent Ruta"] = intToHora(endTime) #time at which the worker that did this route is available for the next one

                    workers[t] = (endTime, value[1], value[2])
                    
                    pre_dft[value[1]][3] = intToHora(routeStartTime + timeToCompleteRoute + timeToEndShift) #update the provisional end of the shift
                    pre_dft[value[1]][4] = round((horaToInt(pre_dft[value[1]][3]) - horaToInt(pre_dft[value[1]][2]))/60,1) #update the total hours worked
                    
                    waitingTime = routeStartTime-(horaToInt(timeline[asignedTo][-1][2])+10)
                    timeline[asignedTo][-1] = (timeline[asignedTo][-1][0], timeline[asignedTo][-1][1], intToHora(horaToInt(timeline[asignedTo][-1][2])+10), timeline[asignedTo][-1][3])
                    timeline[asignedTo].append((row["Id"].split()[0],intToHora(routeStartTime), intToHora(routeStartTime + timeToCompleteRoute), waitingTime))
                    
                    break
                    
                    

            if asignedTo == -1: #No worker is available, then, add another worker
                
                maxEarlyInitialTime = expectedInitialTime - firstRouteMaxEarlyDepartureTime #Start time of the route

                dfj.at[index, "Hora Inici Ruta Real"] = intToHora(maxEarlyInitialTime) #update the table with the actual start time of the route

                endTime = maxEarlyInitialTime + timeToCompleteRoute + timeBetweenRoutes #time when the worker can start the next route
                
                dfj.at[index, "Hora Fi Ruta"] = intToHora(maxEarlyInitialTime + timeToCompleteRoute)
                dfj.at[index, "Plnif vs Real Min"] = -(horaToInt(row["Hora Inici Ruta Plnif"]) - maxEarlyInitialTime) #difference of starting time between plan and actual
                dfj.at[index, "Inici Seguent Ruta"] = intToHora(endTime) #time at which the worker that did this route is available for the next one

                id = totalworkers #New worker assigned to this route
                workers[id] = (endTime, len(pre_dft), row['Hub']) #add it to the dict with the active workers and their last route end time

                startShift= maxEarlyInitialTime - timeToStartShift
                #time it would end the shift if no more routes would be done
                provisionalEndShift = maxEarlyInitialTime + timeToCompleteRoute + timeToEndShift
                provisionalShiftHours = round((provisionalEndShift - startShift)/60,1)

                newWorker = [row["Hub"], id, intToHora(startShift), intToHora(provisionalEndShift), provisionalShiftHours]
                
                pre_dft.append(newWorker) #add worker to the database

                timeline[id] = [(row["Id"].split()[0],intToHora(maxEarlyInitialTime), intToHora(maxEarlyInitialTime + timeToCompleteRoute), "")]

                asignedTo = id
                totalworkers += 1



            dfj.at[index, "Assignacio"] = asignedTo
        
        #add the modified dataframe with the assignments to the list of dataframes
        dfj_general.append(dfj)

    processed_Routes_DF = pd.concat(dfj_general)

    return processed_Routes_DF, pre_dft, timeline

def printTimeline(timeline):
    col1, col2, col3= st.columns(3)
    c = 1
    for worker, value in timeline.items():
        if c == 1:
            with col1:
                st.write(str(worker) + ": ")
                for stop in value:
                    st.write("id: " + stop[0][8:] + " de " + str(stop[1]) + " a " + str(stop[2]) + " Temps d'espera (min): " + str(stop[3]))
                st.write("")
                st.write("")
            c = 2
        elif c == 2:
            with col2:
                st.write(str(worker) + ": ")
                for stop in value:
                    st.write("id: " + stop[0][8:] + " de " + str(stop[1]) + " a " + str(stop[2]) + " Temps d'espera (min): " + str(stop[3]))
                st.write("")
                st.write("")
            c = 3
        else:
            with col3:
                st.write(str(worker) + ": ")
                for stop in value:
                    st.write("id: " + stop[0][8:] + " de " + str(stop[1]) + " a " + str(stop[2]) + " Temps d'espera (min): " + str(stop[3]))
                st.write("")
                st.write("")
            c = 1

if __name__ == "__main__":
    st.set_page_config(layout="wide")

    iVar = process_input() #Input variables

    processed_Routes_DF = process_routes(iVar["Temps per Paquet"]) # Routes processed and in dataframe format

    if(processed_Routes_DF is None):
        pass
    else:
        workers_Schedule = process_workers(iVar["Flexibilitat +6"], iVar["Flexibilitat +4"], iVar["Flexibilitat -4"])

        assign_routes_to_workers(processed_Routes_DF, workers_Schedule, iVar)