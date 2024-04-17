import streamlit as st
import pandas as pd
import datetime 


#time to start shift
timeToStartShift = int(st.text_input("Temps abans de començar el torn", 12))
#time to end Shift
timeToEndShift = int(st.text_input("Temps després d'acabar el torn", 6))
#time between deliveries
timeForDelivery = int(st.text_input("Temps per entrega", 7))
#time between routes
timeBetweenRoutes = int(st.text_input("Temps entre rutes", 10))
#table with jobs to order
jobsTable = st.text_area("taula amb les rutes")

if jobsTable:
    lines = jobsTable.split('\n')
    data = [line.split() for line in lines if line.strip()]
    #data frame with all the data about the jobs, its duration, start time, location, date...
    dfj = pd.DataFrame(data, columns = ["Mes", "Dia", "Hub", "Sortida","Sortida2", "Temps ruta total", "Num Entregues", "Acaba Ruta"])
    dfj['Assignacio'] = ''
    #Total number of employees
    totalEmployees = 0
    #List with info of entry and exit times, and total hours for each employee
    employeeInfo = []
    #map with all the workers and their last route finish time
    employees = {}

    #sorts entries by Hub and Start Time
    dfj = dfj.sort_values(by=["Hub", "Sortida"])



    for index, row in dfj.iterrows():
        #employee asigned to the route
        asignedTo = -1
        #initial time of the route
        initialTime = datetime.time.fromisoformat(str(row["Sortida"])+":00")
        #end time of the route
        endTimeAux = datetime.datetime(100,1,1,initialTime.hour, initialTime.minute,0) + datetime.timedelta(minutes = int(row["Num Entregues"]) * timeForDelivery + float(row["Temps ruta total"]) + timeBetweenRoutes)
        endTime = datetime.time(endTimeAux.hour, endTimeAux.minute)

        for t in employees: #check if any employee is available

            if employees[t] < initialTime:
                #assign the job to employee t, and update the corresponding data structures
                
                employees[t] = endTime
                asignedTo = t
                break
                
                 

        if asignedTo == -1: #No employee is available, the add another employee
            
            totalEmployees += 1
            employees[totalEmployees] = endTime
            startshift= datetime.datetime(100,1,1,initialTime.hour, initialTime.minute,0) - datetime.timedelta(minutes=timeToStartShift)
            newEmployee = [row["Hub"], totalEmployees, str(startshift.hour) + ":" + str(startshift.minute), "00:00", 0]
            employeeInfo.append(newEmployee) #add employee to the database
            asignedTo = totalEmployees

        dfj.at[index, "Assignacio"] = asignedTo

    #create the data frame from the info gathered in the list
    dft = pd.DataFrame(employeeInfo, columns=['Hub', 'Treballador', 'Hora Entrada', 'Hora Sortida', 'Hores Totals'])

    for index, row in dft.iterrows():
        #determine the end Shift time
        endShift = datetime.datetime(100,1,1,employees[row['Treballador']].hour, employees[row['Treballador']].minute, 0) + datetime.timedelta(minutes=timeToEndShift)
        dft.at[index,'Hora Sortida'] = str(endShift.hour) + ":" + str(endShift.minute)
        #determine the total hours worked by each employee
        hours, minutes = map(int, row["Hora Entrada"].split(':'))
        startshift = datetime.datetime(100,1,1, hours, minutes,0)
        dft.at[index, 'Hores Totals'] = round((endShift - startshift).total_seconds() / 3600,1)

    dft.sort_values(by=['Hub','Treballador'])

    st.write("Taula amb la assignació de treballs")
    st.write(dfj)

    st.write("Taula amb les hores del empleats")
    st.write(dft)
