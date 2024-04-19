import streamlit as st
import pandas as pd
import re
from funcions import *




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

    

    if routesTable and workersTable:
        
        #dict with the information of max working hours and names of the workers
        database_workers = process_workers(workersTable, extra6hours, extra4hours, extra0hours)
        #data frame with all the data about the jobs, its duration, start time, location, date...
        dfj_hub = pd.DataFrame(process_routes(routesTable, timeForDelivery), columns = ["Id", "Data", "Hub", "Hora Sortida", "Temps ruta", "Hora Arribada", "Num Entregues", "Assignacio", "order"])
        
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

                        routeStartTime = max(value[0], maxEarlyInitialTime)
                        
                        endTime = routeStartTime + timeToCompleteRoute + timeBetweenRoutes
                        workers[t] = (endTime, value[1], value[2])
                        
                        pre_dft[value[1]][3] = intToHora(routeStartTime + timeToCompleteRoute + timeToEndShift) #update the provisional end of the shift
                        pre_dft[value[1]][4] = round((horaToInt(pre_dft[value[1]][3]) - horaToInt(pre_dft[value[1]][2]))/60,1) #update the total hours worked
                        
                        timeline[asignedTo].append((row["Id"].split()[0],intToHora(routeStartTime), intToHora(endTime)))
                        
                        break
                        
                        

                if asignedTo == -1: #No worker is available, then, add another worker

                    endTime = maxEarlyInitialTime + timeToCompleteRoute + timeBetweenRoutes

                    id = totalworkers #New worker assigned to this route
                    workers[id] = (endTime, len(pre_dft), row['Hub']) #add it to the dict with the active workers and their last route end time

                    startShift= maxEarlyInitialTime - timeToStartShift
                    #time it would end the shift if no more routes would be done
                    provisionalEndShift = maxEarlyInitialTime + timeToCompleteRoute + timeToEndShift
                    provisionalShiftHours = round((provisionalEndShift - startShift)/60,1)

                    newWorker = [row["Hub"], id, intToHora(startShift), intToHora(provisionalEndShift), provisionalShiftHours]
                    
                    pre_dft.append(newWorker) #add worker to the database

                    timeline[id] = [(row["Id"].split()[0],intToHora(maxEarlyInitialTime), intToHora(endTime))]

                    asignedTo = id
                    totalworkers += 1



                dfj.at[index, "Assignacio"] = asignedTo
            #add the modified dataframe with the assignments to the list of dataframes
            dfj_general.append(dfj)



        #create the data frame from the info gathered in the list
        dft = pd.DataFrame(pre_dft, columns=['Hub', 'worker', 'Hora Entrada', 'Hora Sortida', 'Hores Totals'])
        dft = dft.sort_values(by='Hores Totals', ascending=False)
        
        idToWorker = {}
        i = 0


        #Assign workers to the shift the best fits their hours

        dft.insert(1, "Treballador", '')
        for index, row in dft.iterrows():
            idToWorker[row["worker"]] = database_workers[i][0]
            dft.at[index, "Treballador"] = idToWorker[row["worker"]]
            i += 1
        
        dft = dft.drop("worker", axis=1)

        #Add the names of the workers to the assignments

        dfj = pd.concat(dfj_general)
        dfj = dfj.drop("order", axis=1)
        i = 0

        for index, row in dfj.iterrows():
            dfj.at[index, "Assignació"] = idToWorker[row["Assignacio"]]
            if row["Assignacio"] in timeline:
                timeline[idToWorker[row["Assignacio"]]] = timeline.pop(row["Assignacio"])

        dfj = dfj.drop("Assignacio", axis=1)


    
        #Printing section of the code
        
        #columns
        col3, col4 = st.columns(2)

        #separete the different hubs
        dft = dft.groupby("Hub")
        for hub, dft_hub in dft:
            #sort workers by id
            dft_hub.sort_values(by='Hores Totals', ascending=False)

            
            
            
            if columna == 1:
                columna = 2
                with col3:
                    #print in columnt 1 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft_hub)
            else:
                columna = 1
                with col4:
                    #print in columnt 2 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft_hub)


        
        st.write("Taula amb la assignació de treballs")
        st.write(dfj)

        st.write(database_workers)

        printTimeline(timeline)