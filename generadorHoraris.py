import streamlit as st
import pandas as pd
import re


def intToHora(hora):
    return str(hora//60)+':'+str(hora%60)

def horaToInt(hora):
    return int(hora.split(':')[0])*60 + int(hora.split(':')[1])

#function to process the input data about routes
def process_routes(routes_table):
    
    data = []

    for line in routesTable.splitlines():
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
        route_data = [route[0], route[2], route[10], route[3], int(route[6]), intToHora(arrivalTime), int(route[12]), "", departureTime]
                    
        data.append(route_data)
    
    return data


#function to process the input data about workers and their hours
def process_workers(workers_table):
    
    data = []

    for line in workers_table.splitlines():
        if not line.strip():
            continue
        
        worker = line.split()
        
        if len(worker) != 2:  # Check for expected number of elements
            print(f"Warning: Unexpected line format: {line}")
            continue  # Skip lines with incorrect format

        if worker[1] == "Out":
            continue #skip workers with no hours

        workingHours = (int(worker[1])/5)*60 #convert into minutes

        #Apply the hour flexibility
        if workingHours > 6*60:
            workingHours *= (1 + extra6hours)
        elif workingHours > 4*60:
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


if __name__ == "__main__":
    st.set_page_config(layout="wide")


    columna = 1
    #columns
    col1, col2 = st.columns(2)

    with col1:

        #time to start shift
        timeToStartShift = int(st.text_input("Temps abans de començar el torn", 12))
        #time to end Shift
        timeToEndShift = int(st.text_input("Temps després d'acabar el torn", 6))
        #time between deliveries
        timeForDelivery = int(st.text_input("Temps per entrega", 7))
        #time between routes
        timeBetweenRoutes = int(st.text_input("Temps entre rutes", 10))
        #Represents the amount of time by which one departs earlier than the scheduled departure time
        earlyDepartureTimeMargin = int(st.text_input("Marge de temps de sortida abans del previst", 20))
        #Represents the amount of time by which one departs later than the scheduled departure time
        delayedDepartureTimeMargin = int(st.text_input("Marge de temps de sortida despres del previst", 15))
    

    with col2:

        #Maximum time before an worker gets assigned another route
        maxWaitTimeBetweenRoutes = int(st.text_input("Màxim temps d'espera entre rutes", 20))

        #temps mobilitat entre hubs
    
        #Global maximum of working hours
        globalMaxhours = int(st.text_input("Maximes hores globals per treballador", 9))
        #extra hours
        extra6hours = int(st.text_input("flexibilitat horaria treballadors +6", 10))/100
        extra4hours = int(st.text_input("flexibilitat horaria treballadors +4", 20))/100
        extra0hours = int(st.text_input("flexibilitat horaria treballadors menys de 4 hores", 20))/100
    
    #maxim d'hores per treballador
    workersTable = st.text_area("Informació hore de feina empleats ")
    
    #table with routes to order
    routesTable = st.text_area("taula amb les rutes")

    #columns
    col3, col4 = st.columns(2)

    if routesTable and workersTable:
        
        #dict with the information of max working hours and names of the workers
        database_workers = process_workers(workersTable)
        #data frame with all the data about the jobs, its duration, start time, location, date...
        dfj_hub = pd.DataFrame(process_routes(routesTable), columns = ["Id", "Data", "Hub", "Hora Sortida", "Temps ruta", "Hora Arribada", "Num Entregues", "Assignacio", "order"])
        
        #divide the dataframe into smaller, each one pertaining to a different hub
        dfj_hub = dfj_hub.groupby("Hub")
        
        dfj_general = []

        for hub, dfj in dfj_hub:
            #sort by delivery exit time
            dfj = dfj.sort_values(by="order")
            #Total number of workers
            totalworkers = 0
            #List with info of entry and exit times, and total hours for each worker
            pre_dft = []
            #map with all the workers and their last route finish time
            workers = {}

            timeline = {}
            #sorts entries by Hub and Start Time
            

            

            for index, row in dfj.iterrows():
                #worker asigned to the route
                asignedTo = -1
                #expected initial time of the route
                expectedInitialTime = horaToInt(row["Hora Sortida"])
                #maximum late time to start the route
                maxDelayedInitialTime = expectedInitialTime + delayedDepartureTimeMargin
                #maximum early time to start the route
                maxEarlyInitialTime = expectedInitialTime - earlyDepartureTimeMargin
                #time to complete the route
                timeToCompleteRoute = row["Temps ruta"] + row["Num Entregues"] * timeForDelivery

                #end time of the route
                endTime = horaToInt(row["Hora Arribada"]) + timeBetweenRoutes

                for t, value in workers.items(): #check if any worker is available

                    if value[0] < maxDelayedInitialTime and (pre_dft[value[1]][4] + timeToCompleteRoute/60) < database_workers[t][1] and (maxEarlyInitialTime - value[0]) < maxWaitTimeBetweenRoutes:
                        
                        routeStartTime = max(value[0], maxEarlyInitialTime)
                        #assign the job to worker t, and update the corresponding data structures
                        endTime = routeStartTime + timeToCompleteRoute + timeBetweenRoutes
                        workers[t] = (endTime, value[1])
                        
                        pre_dft[value[1]][3] = intToHora(routeStartTime + timeToCompleteRoute + timeToEndShift) #update the provisional end of the shift
                        pre_dft[value[1]][4] = round((horaToInt(pre_dft[value[1]][3]) - horaToInt(pre_dft[value[1]][2]))/60,1) #update the total hours worked
                        asignedTo = t
                        timeline[database_workers[t][0]].append((row["Id"].split()[0],intToHora(routeStartTime), intToHora(endTime)))
                        break
                        
                        

                if asignedTo == -1: #No worker is available, then, add another worker

                    endTime = maxEarlyInitialTime + timeToCompleteRoute + timeBetweenRoutes

                    id = totalworkers #New worker assigned to this route
                    workers[id] = (endTime, len(pre_dft)) #add it to the dict with the active workers and their last route end time

                    startShift= maxEarlyInitialTime - timeToStartShift
                    #time it would end the shift if no more routes would be done
                    provisionalEndShift = maxEarlyInitialTime + timeToCompleteRoute + timeToEndShift
                    provisionalShiftHours = round((provisionalEndShift - startShift)/60,1)

                    if id in database_workers:
                        workerName = database_workers[id][0]
                    else:
                        workerName = "EXTRA"

                    newWorker = [row["Hub"], workerName, intToHora(startShift), intToHora(provisionalEndShift), provisionalShiftHours]
                    pre_dft.append(newWorker) #add worker to the database

                    timeline[workerName] = [(row["Id"].split()[0],intToHora(maxEarlyInitialTime), intToHora(endTime))]

                    asignedTo = id
                    totalworkers += 1

                if asignedTo in database_workers:
                    workerName = database_workers[asignedTo][0]
                else:
                    workerName = "EXTRA"

                dfj.at[index, "Assignacio"] = workerName
            #add the modified dataframe with the assignments to the list of dataframes
            dfj_general.append(dfj)

            #create the data frame from the info gathered in the list
            dft = pd.DataFrame(pre_dft, columns=['Hub', 'Treballador', 'Hora Entrada', 'Hora Sortida', 'Hores Totals'])

            #sort workers by id
            dft.sort_values(by='Hores Totals')

            if columna == 1:
                columna = 2
                with col3:
                    #print in columnt 1 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft)
            else:
                columna = 1
                with col4:
                    #print in columnt 2 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft)


        dfj = pd.concat(dfj_general)
        dfj = dfj.drop("order", axis=1)
        st.write("Taula amb la assignació de treballs")
        st.write(dfj)

        printTimeline(timeline)