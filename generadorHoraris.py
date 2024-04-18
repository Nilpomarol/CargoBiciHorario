import streamlit as st
import pandas as pd
import datetime 


#function to process the input data about routes
def process_routes(routes_table):
    
    data = []

    for line in routesTable.splitlines():
        if not line.strip():
            continue

        route = line.split()

        if len(route) != 14:  # Check for expected number of elements
            print(f"Warning: Unexpected line format: {line}")
            continue  # Skip lines with incorrect format
        #departure time in minutes
        departureTime = float(route[2].split(':')[0])*60 + float(route[2].split(':')[1])
        #arrival time in minutes
        arrivalTime = departureTime + int(route[5]) * int(route[11])
        #process an element of the data frame and uses the correct format
        route_data = [route[0], route[1], route[9], departureTime, int(route[5]), arrivalTime, int(route[11]), ""]
                    
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
        if workingHours > 6:
            workingHours *= (1 + extra6hours)
        elif workingHours > 4:
            workingHours *= (1 + extra4hours)
        else:
            workingHours *= (1 + extra0hours)
        
        worker_data = [worker[0], workingHours]

        data.append(worker_data)

        #sorts by higher amount of hours
        sorted_data = sorted(data, key=lambda x: x[1])
    
    #converts it into a dict
    return {i: element for i, element in enumerate(sorted_data)}




if __name__ == "__main__":

    st.set_page_config(layout="wide")


    columna = 1
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
    workerInformation = st.text_area("Informació hore de feina empleats ")
    
    #table with routes to order
    routesTable = st.text_area("taula amb les rutes")

    #columns
    col1, col2 = st.columns(2)

    if routesTable and workerInformation:
        
        #dict with the information of max working hours and names of the workers
        workerData = process_workers(workerInformation)
        #data frame with all the data about the jobs, its duration, start time, location, date...
        dfj_hub = pd.DataFrame(process_routes(routesTable), columns = ["Id", "Data", "Hub", "Hora Sortida", "Temps ruta", "Hora Arribada", "Num Entregues", "Assignació"])
        
        
        #divide the dataframe into smaller, each one pertaining to a different hub
        dfj_hub = dfj_hub.groupby("Hub")
        
        dfj_general = []

        for hub, dfj in dfj_hub:
            #sort by delivery exit time
            dfj = dfj.sort_values(by="Hora Sortida")
            #Total number of workers
            totalworkers = 0
            #List with info of entry and exit times, and total hours for each worker
            workerInfo = []
            #map with all the workers and their last route finish time
            workers = {}

            #sorts entries by Hub and Start Time
            

            

            for index, row in dfj.iterrows():
                #worker asigned to the route
                asignedTo = -1
                #expected initial time of the route
                expectedInitialTime = row["Hora Sortida"]
                #maximum late time to start the route
                maxDelayedInitialTime = expectedInitialTime + delayedDepartureTimeMargin
                #maximum early time to start the route
                maxEarlyInitialTime = expectedInitialTime - earlyDepartureTimeMargin
                #time to complete the route
                timeToCompleteRoute = row["Temps ruta"] + row["Num Entregues"] * timeForDelivery

                #end time of the route
                endTime = row["Hora Arribada"] + timeBetweenRoutes

                for t, value in workers.items(): #check if any worker is available

                    if value[0] < maxDelayedInitialTime and (workerInfo[value[1]][4] + timeToCompleteRoute) < workerData[t][1]:
                        #assign the job to worker t, and update the corresponding data structures
                        endTime = value[0] + timeToCompleteRoute + timeBetweenRoutes
                        workers[t] = endTime
                        workerInfo[value[1]][4] += timeToCompleteRoute #update the total hours worked
                        workerInfo[value[1]][3] = value[0] + timeToCompleteRoute + timeToEndShift #update the provisional end of the shift
                        asignedTo = t
                        break
                        
                        

                if asignedTo == -1: #No worker is available, then, add another worker

                    endTime = maxEarlyInitialTime + timeToCompleteRoute + timeBetweenRoutes

                    id = totalworkers #New worker assigned to this route
                    workers[id] = (endTime, len(workerInfo)) #add it to the dict with the active workers and their last route end time

                    startShift= maxEarlyInitialTime - timeToStartShift
                    #time it would end the shift if no more routes would be done
                    provisionalEndShift = maxEarlyInitialTime + row["Hora Arribada"]+timeToEndShift
                    provisionalShiftHours = provisionalEndShift - startShift

                    newWorker = [row["Hub"], id, startShift, provisionalEndShift, provisionalShiftHours]
                    workerInfo.append(newWorker) #add worker to the database

                    asignedTo = workerData[id][0]
                    totalworkers += 1


                dfj.at[index, "Assignacio"] = asignedTo

            #add the modified dataframe with the assignments to the list of dataframes
            dfj_general.append(dfj)

            #create the data frame from the info gathered in the list
            dft = pd.DataFrame(workerInfo, columns=['Hub', 'Treballador', 'Hora Entrada', 'Hora Sortida', 'Hores Totals'])

            for index, row in dft.iterrows():
                #convert the Hora Entrada from minutes to hours
                dft.at[index, 'Hora Entrada'] = str(row['Hora Entrada']//60)+':'+str(row['Hora Entrada']%60)
                #convert the Hora Sortida from minutes to hours
                dft.at[index, 'Hora Sortida'] = str(row['Hora Sortida']//60)+':'+str(row['Hora Sortida']%60)
                #convert the total hours from minutes to hours
                dft.at[index, 'Hores Totals'] = row["Hora Entrada"]/60

            #sort workers by id
            dft.sort_values(by='Hores Totals')

            if columna == 1:
                columna = 2
                with col1:
                    #print in columnt 1 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft)
            else:
                columna = 1
                with col2:
                    #print in columnt 2 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft)


        st.write("Taula amb la assignació de treballs")
        st.write(pd.concat(dfj_general))