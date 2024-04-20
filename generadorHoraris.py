import streamlit as st
import pandas as pd
import openpyxl as opxl
import sys

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
        timeToEndShift = int(st.text_input("Temps després d'acabar el torn", 5))
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

        #max time to enter the first route early
        firstRouteMaxEarlyDepartureTime = int(st.text_input("Marge de temps de sortida abans del previst de la primera ruta del torn", 10))
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

    colButton, colaux = st.columns(2)
    

    if routesTable:
        
        database_workers = {}
        if workersTable:
            #dict with the information of max working hours and names of the workers
            database_workers = process_workers(workersTable, extra6hours, extra4hours, extra0hours)
        #data frame with all the data about the jobs, its duration, start time, location, date...
        dfj_hub = pd.DataFrame(process_routes(routesTable, timeForDelivery), columns = ["Id", "Data", "Hub", "Hora Inici Ruta Plnif", "Hora Inici Ruta Real", "Hora Fi Ruta", "Temps ruta", "Num Entregues", "Assignacio", "order"])
        
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
                #maximum late time to start the route
                maxDelayedInitialTime = expectedInitialTime + delayedDepartureTimeMargin
                #maximum early time to start the route
                maxEarlyInitialTime = expectedInitialTime - earlyDepartureTimeMargin
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

                        workers[t] = (endTime, value[1], value[2])
                        
                        pre_dft[value[1]][3] = intToHora(routeStartTime + timeToCompleteRoute + timeToEndShift) #update the provisional end of the shift
                        pre_dft[value[1]][4] = round((horaToInt(pre_dft[value[1]][3]) - horaToInt(pre_dft[value[1]][2]))/60,1) #update the total hours worked
                        
                        timeline[asignedTo][-1] = (timeline[asignedTo][-1][0], timeline[asignedTo][-1][1], intToHora(horaToInt(timeline[asignedTo][-1][2])+10))
                        timeline[asignedTo].append((row["Id"].split()[0],intToHora(routeStartTime), intToHora(routeStartTime + timeToCompleteRoute)))
                        
                        break
                        
                        

                if asignedTo == -1: #No worker is available, then, add another worker
                    
                    maxEarlyInitialTime = expectedInitialTime - firstRouteMaxEarlyDepartureTime #Start time of the route

                    dfj.at[index, "Hora Inici Ruta Real"] = intToHora(maxEarlyInitialTime) #update the table with the actual start time of the route

                    endTime = maxEarlyInitialTime + timeToCompleteRoute + timeBetweenRoutes #time when the worker can start the next route
                    
                    dfj.at[index, "Hora Fi Ruta"] = intToHora(maxEarlyInitialTime + timeToCompleteRoute)

                    id = totalworkers #New worker assigned to this route
                    workers[id] = (endTime, len(pre_dft), row['Hub']) #add it to the dict with the active workers and their last route end time

                    startShift= maxEarlyInitialTime - timeToStartShift
                    #time it would end the shift if no more routes would be done
                    provisionalEndShift = maxEarlyInitialTime + timeToCompleteRoute + timeToEndShift
                    provisionalShiftHours = round((provisionalEndShift - startShift)/60,1)

                    newWorker = [row["Hub"], id, intToHora(startShift), intToHora(provisionalEndShift), provisionalShiftHours]
                    
                    pre_dft.append(newWorker) #add worker to the database

                    timeline[id] = [(row["Id"].split()[0],intToHora(maxEarlyInitialTime), intToHora(maxEarlyInitialTime + timeToCompleteRoute))]

                    asignedTo = id
                    totalworkers += 1



                dfj.at[index, "Assignacio"] = asignedTo
            #add the modified dataframe with the assignments to the list of dataframes
            dfj_general.append(dfj)



        #create the data frame from the info gathered in the list
        dft = pd.DataFrame(pre_dft, columns=['Hub', 'worker', 'Hora Entrada', 'Hora Inici Ruta Plnif', 'Hores Totals'])
        dft = dft.sort_values(by='Hores Totals', ascending=False)
        
        idToWorker = {}
        i = 0


        #Assign workers to the shift the best fits their hours

        dft.insert(1, "Treballador", '')
        extraWorkers = 65

        for index, row in dft.iterrows():
            if i in database_workers:
                idToWorker[row["worker"]] = database_workers[i][0]
            else:
                idToWorker[row["worker"]] = chr(extraWorkers)
                extraWorkers += 1
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

        additionalInfoList = []

        for hub, dft_hub in dft:
            #sort workers by id
            dft_hub.sort_values(by='Hores Totals', ascending=False)

            totalHoursHub = round(dft_hub["Hores Totals"].sum(),1)

            workersInHub = len(dft_hub)

            numberDeliveriesHub = len(dfj[dfj["Hub"] == hub])

            additionalInfoList.append((hub, len(dft_hub), totalHoursHub, workersInHub, numberDeliveriesHub))
            
            
            
            if columna == 1:
                columna = 2
                with col3:
                    st.write("Informació per al Hub: " + hub)
                    col5, col6, col7 = st.columns(3)
                    with col5:
                        st.write("Hores Totals: " + str(totalHoursHub))
                    with col6:
                        st.write("Numero de traballadors: " + str(workersInHub))
                    with col7:
                        st.write("Numero de rutes: " + str(numberDeliveriesHub))

                    #print in columnt 1 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft_hub)
            else:
                columna = 1
                with col4:
                    st.write("Informació per al Hub: " + hub)
                    col5, col6, col7 = st.columns(3)
                    with col5:
                        st.write("Hores Totals al Hub: " + str(totalHoursHub))
                    with col6:
                        st.write("Numero de traballadors: " + str(workersInHub))
                    with col7:
                        st.write("Numero de rutes: " + str(numberDeliveriesHub))
                    #print in columnt 2 worker information for the actual hub
                    st.write("Taula amb les hores del empleats per al Hub: " + hub)
                    st.write(dft_hub)


        
        st.write("Taula amb la assignació de treballs")
        st.write(dfj)

        printTimeline(timeline)

        #Code section that generates an excel file with the results of the code
        with pd.ExcelWriter('output.xlsx') as writer:
            dfj.to_excel(writer, sheet_name='Taula General', startcol= 1, startrow= 1)

            workerList = {}
            

            for hub, dft_hub in dft:
                dft_hub.to_excel(writer, sheet_name=hub, startcol= 1, startrow= 1)

                workerListAux = []

                rowToWrite = len(dft_hub) + 8
                colToWrite = 1

                for index, row in dft_hub.iterrows():
                    workerTimeline = timeline[row["Treballador"]]
                    df_workerTimeline = []
                    for i in workerTimeline:
                        newElement = [i[0], i[1], i[2]]
                        df_workerTimeline.append(newElement)
                    df_workerTimeline = pd.DataFrame(df_workerTimeline, columns=['ID', 'Inici Ruta', 'Fi Ruta'])
                    df_workerTimeline.to_excel(writer, sheet_name=hub, startcol=colToWrite, startrow=rowToWrite)
                    workerListAux.append((row["Treballador"], rowToWrite))
                    
                    colToWrite += 7

                    if colToWrite == 22:
                        colToWrite = 1
                        rowToWrite += len(df_workerTimeline) + 8

                workerList[hub] = workerListAux

        try:
            # Load the workbook
            wb = opxl.load_workbook('output.xlsx')
            print(additionalInfoList)
            # Loop through the data list
            for data in additionalInfoList:
                # Get the sheet by name
                sheet = wb[data[0]]


                row_number = data[1]+2  # Assuming you want to sum from row 3 onwards
                column_letter = 'G'  # Assuming you want to sum column G
                formula = f"=SUM({column_letter}3:{column_letter}{row_number})"  # Construct the SUM formula
                row_number +=1
                row_number +=1
                sheet.cell(row=row_number, column=6).value = "Total Hores"
                sheet.cell(row=row_number, column=7).value = formula
                row_number +=1
                sheet.cell(row=row_number, column=6).value = "Num treballadors"
                sheet.cell(row=row_number, column=7).value = data[3]
                row_number +=1
                sheet.cell(row=row_number, column=6).value = "Num Rutes"
                sheet.cell(row=row_number, column=7).value = data[4]


                colToWrite = 1
 
                for tuple in workerList[data[0]]:
                    
                    row_number = tuple[1]
                    sheet.cell(row=row_number+1, column=colToWrite+1).value = tuple[0]
                    
                    colToWrite += 7
                    if colToWrite == 22:
                        colToWrite = 1


            # Save the workbook once after all data is written
            wb.save('output.xlsx')

            with colButton:
                # Add a download button for the Excel file
                if st.button('Download Excel File'):
                    with open("output.xlsx", "rb") as file:
                        file_content = file.read()
                    st.download_button(label='Download Excel', data=file_content, file_name='output.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


        except Exception as e:
            print(f"Error writing to Excel file: {e}")

        


