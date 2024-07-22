import streamlit as st
import pandas as pd
import openpyxl as opxl
from openpyxl.styles import NamedStyle
from datetime import datetime, timedelta
import locale
import json
import os
import re

def intToHora(minutes):
    """Convert minutes into a 'hh:mm' formatted string."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02}:{mins:02}"


def horaToInt(time_str):
    """Convert a 'hh:mm' formatted string into total minutes."""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except ValueError:
        raise ValueError("Input must be in 'hh:mm' format and contain valid integers.")
    except IndexError:
        raise ValueError("Input must be in 'hh:mm' format.")

def load_data(file_path, default_data=None):
    """Load data from a JSON file."""
    if default_data is None:
        default_data = {
            "Temps Entrada": 10,
            "Temps Sortida": 5,
        }
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Using default data.")
        return default_data

    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading file {file_path}: {e}. Using default data.")
        return default_data

def save_data(data, file_path):
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4) 
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving data to {file_path}: {e}.")
        return False

def process_User_Input():
    """Process user inputs."""
    file_path = 'variablesSumary.json'
    hipotesi = load_data(file_path)
    
    col1, col2 = st.columns([1, 1])
    
    for i, key in enumerate(hipotesi.keys()):
        with col1 if i % 2 == 0 else col2:
            hipotesi[key] = int(st.text_input(f"{key}:", hipotesi[key]))

    save_data(hipotesi, file_path)
    return hipotesi

def process_Week_Schedule(weekSchedule, hipotesi):
    
    processed_routes = []
    distinctdays = set()
    # Set the locale to Spanish
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

    for line in weekSchedule.splitlines():
        if not line.strip():
            continue
        
        route_elements = re.split(r"\t", line)

        try:
            date_str = route_elements[0] + " " + route_elements[1] 
            # Specify the year manually (current year)
            current_year = datetime.now().year

            # Parse the date string and add the year
            date_obj = datetime.strptime(f"{date_str} {current_year}", '%B %d %Y')

            if date_obj.strftime("%A") not in distinctdays:
                distinctdays.add(date_obj.strftime("%A"))
                if len(distinctdays) > 5:
                    break
            
            repartidor = route_elements[6]
            if repartidor == "":
                repartidor = "XXX"
            horaSortida = route_elements[7]
            horaArribada = route_elements[8]
            
            processed_route = [
                date_obj,
                repartidor,
                horaSortida,
                horaArribada                
            ]
            
            processed_routes.append(processed_route)
            
        except ValueError as e:
            print(f"Error processing line: {line} - {e}")
            continue
        
    processed_routes = pd.DataFrame(processed_routes, columns=["Data", "Repartidor", "Hora Sortida", "Hora Arribada"])
    return processed_routes



 
def generate_weekly_schedule(weekSchedule, hipotesi):
    workerSchedule = {}

    for index, row in weekSchedule.iterrows():
        dia = row["Data"].strftime("%A")
        repartidor = row["Repartidor"]
        
        def parse_time(time_str, formats):
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Time format for '{time_str}' not recognized")
        

        formats = ["%H:%M:%S", "%H:%M"]

        try:
            entrada = parse_time(row["Hora Sortida"], formats) - timedelta(minutes=hipotesi["Temps Entrada"])
            sortida = parse_time(row["Hora Arribada"], formats) + timedelta(minutes=hipotesi["Temps Sortida"])
        except ValueError as e:
            print(f"Error parsing time: {e}")
        
        
        if (dia, repartidor) not in workerSchedule:
            workerSchedule[(dia, repartidor)] = [entrada, sortida, round((sortida - entrada).total_seconds() / 3600, 1)]
        else:
            entrada = workerSchedule[(dia, repartidor)][0]
            workerSchedule[(dia, repartidor)][1] = sortida
            workerSchedule[(dia, repartidor)][2] = round((sortida - entrada).total_seconds() / 3600,1)
    
    return workerSchedule



def process_OldWeek_Schedule(OldWeekSchedule):
    """
    Processes worker data to extract and format relevant information based on the day of the week.

    Args:
        workers_table (str): String containing the worker data.
        week_day (int): Day of the week (0-6, where 0 is Monday).

    Returns:
        list: List of processed worker data.
    """

    # Initialize an empty list to store processed worker data
    processed_workers = {}



    # Process each line in the workers table
    for line in OldWeekSchedule.splitlines():
        if not line.strip():
            continue  # Skip empty lines

        worker = re.split(r"\t", line)

        try:
            treballador = worker[0].upper()
            # Convert hours worked from comma to period for float conversion
            for i in range(0, 5):
                worker[i+2] = worker[i+2].replace(",", ".")
            processed_workers[("lunes", treballador)] = [worker[1], worker[2], worker[3]]
            processed_workers[("martes", treballador)] = [worker[4], worker[5], worker[6]]
            processed_workers[("miÃ©rcoles", treballador)] = [worker[7], worker[8], worker[9]]
            processed_workers[("jueves", treballador)] = [worker[10], worker[11], worker[12]]
            processed_workers[("viernes", treballador)] = [worker[13], worker[14], worker[15]]
            

            # Append the processed worker data to the list

        except ValueError as e:
            print(f"Error processing line: {line} - {e}")
            continue

    # processed_workers = processed_workers.sort_values(by="Aux")
    # processed_workers = processed_workers.drop("Aux", axis=1)
    return processed_workers





def generate_Excel_File(oldWeekSchedule, newWeekSchedule):
    for index, row in newWeekSchedule.items():
        newWeekSchedule[index][0] = newWeekSchedule[index][0].strftime("%H:%M")
        newWeekSchedule[index][1] = newWeekSchedule[index][1].strftime("%H:%M")


    
    workers = set()
    for index, row in newWeekSchedule.items():
        if index[1] not in workers:
            workers.add(index[1])
   
    try:        
        wb = opxl.Workbook()
    except Exception as e:
        print(f"Error loading the Excel file: {e}")
        
    sheet = wb.active
    sheet.title = "Horari asdfsadf"
    
    row_number = 5
    sheet.cell(row=3, column=3).value = "Lunes"
    sheet.cell(row=3, column=6).value = "Martes"
    sheet.cell(row=3, column=9).value = "miÃ©rcoles"
    sheet.cell(row=3, column=12).value = "Jueves"
    sheet.cell(row=3, column=15).value = "Viernes"
    for i in range(0, 5):
        sheet.cell(row=4, column=3 + i * 3).value = "Entrada"
        sheet.cell(row=4, column=4 + i * 3).value = "Sortida"
        sheet.cell(row=4, column=5 + i * 3).value = "Hores"
    for worker in workers:
        sheet.cell(row=row_number, column=2).value = worker
        if ("lunes", worker) in newWeekSchedule:
            sheet.cell(row=row_number, column=3).value = newWeekSchedule[("lunes", worker)][0]
            sheet.cell(row=row_number, column=4).value = newWeekSchedule[("lunes", worker)][1]
            sheet.cell(row=row_number, column=5).value = newWeekSchedule[("lunes", worker)][2]
        if ("martes", worker) in newWeekSchedule:
            sheet.cell(row=row_number, column=6).value = newWeekSchedule[("martes", worker)][0]
            sheet.cell(row=row_number, column=7).value = newWeekSchedule[("martes", worker)][1]
            sheet.cell(row=row_number, column=8).value = newWeekSchedule[("martes", worker)][2]
        if ("miÃ©rcoles", worker) in newWeekSchedule:
            sheet.cell(row=row_number, column=9).value = newWeekSchedule[("miÃ©rcoles", worker)][0]
            sheet.cell(row=row_number, column=10).value = newWeekSchedule[("miÃ©rcoles", worker)][1]
            sheet.cell(row=row_number, column=11).value = newWeekSchedule[("miÃ©rcoles", worker)][2]
        if ("jueves", worker) in newWeekSchedule:
            sheet.cell(row=row_number, column=12).value = newWeekSchedule[("jueves", worker)][0]
            sheet.cell(row=row_number, column=13).value = newWeekSchedule[("jueves", worker)][1]
            sheet.cell(row=row_number, column=14).value = newWeekSchedule[("jueves", worker)][2]
        if ("viernes", worker) in newWeekSchedule:
            sheet.cell(row=row_number, column=15).value = newWeekSchedule[("viernes", worker)][0]
            sheet.cell(row=row_number, column=16).value = newWeekSchedule[("viernes", worker)][1]
            sheet.cell(row=row_number, column=17).value = newWeekSchedule[("viernes", worker)][2]
        row_number += 1

    row_number += 5
    if not isinstance(oldWeekSchedule, str):
        workersWritten = set()

        sheet.cell(row=row_number-2, column=3).value = "Lunes"
        sheet.cell(row=row_number-2, column=6).value = "Martes"
        sheet.cell(row=row_number-2, column=9).value = "miÃ©rcoles"
        sheet.cell(row=row_number-2, column=12).value = "Jueves"
        sheet.cell(row=row_number-2, column=15).value = "Viernes"
        for i in range(0, 5):
            sheet.cell(row=row_number-1, column=3 + i * 3).value = "Entrada"
            sheet.cell(row=row_number-1, column=4 + i * 3).value = "Sortida"
            sheet.cell(row=row_number-1, column=5 + i * 3).value = "Hores"
        for worker in workers:
            workersWritten.add(worker)
            sheet.cell(row=row_number, column=2).value = worker
            
            if ("lunes", worker) in oldWeekSchedule:
                sheet.cell(row=row_number, column=3).value = oldWeekSchedule[("lunes", worker)][0]
                sheet.cell(row=row_number, column=4).value = oldWeekSchedule[("lunes", worker)][1]
                sheet.cell(row=row_number, column=5).value = oldWeekSchedule[("lunes", worker)][2]
            if ("martes", worker) in oldWeekSchedule:
                sheet.cell(row=row_number, column=6).value = oldWeekSchedule[("martes", worker)][0]
                sheet.cell(row=row_number, column=7).value = oldWeekSchedule[("martes", worker)][1]
                sheet.cell(row=row_number, column=8).value = oldWeekSchedule[("martes", worker)][2]
            if ("miÃ©rcoles", worker) in oldWeekSchedule:
                sheet.cell(row=row_number, column=9).value = oldWeekSchedule[("miÃ©rcoles", worker)][0]
                sheet.cell(row=row_number, column=10).value = oldWeekSchedule[("miÃ©rcoles", worker)][1]
                sheet.cell(row=row_number, column=11).value = oldWeekSchedule[("miÃ©rcoles", worker)][2]
            if ("jueves", worker) in oldWeekSchedule:
                sheet.cell(row=row_number, column=12).value = oldWeekSchedule[("jueves", worker)][0]
                sheet.cell(row=row_number, column=13).value = oldWeekSchedule[("jueves", worker)][1]
                sheet.cell(row=row_number, column=14).value = oldWeekSchedule[("jueves", worker)][2]
            if ("viernes", worker) in oldWeekSchedule:
                sheet.cell(row=row_number, column=15).value = oldWeekSchedule[("viernes", worker)][0]
                sheet.cell(row=row_number, column=16).value = oldWeekSchedule[("viernes", worker)][1]
                sheet.cell(row=row_number, column=17).value = oldWeekSchedule[("viernes", worker)][2]
            row_number += 1
        
        for (day, worker), info in oldWeekSchedule.items():
            if worker not in workersWritten:
                workersWritten.add(worker)
                sheet.cell(row=row_number, column=2).value = worker
                if ("lunes", worker) in oldWeekSchedule:
                    sheet.cell(row=row_number, column=3).value = oldWeekSchedule[("lunes", worker)][0]
                    sheet.cell(row=row_number, column=4).value = oldWeekSchedule[("lunes", worker)][1]
                    sheet.cell(row=row_number, column=5).value = oldWeekSchedule[("lunes", worker)][2]
                if ("martes", worker) in oldWeekSchedule:
                    sheet.cell(row=row_number, column=6).value = oldWeekSchedule[("martes", worker)][0]
                    sheet.cell(row=row_number, column=7).value = oldWeekSchedule[("martes", worker)][1]
                    sheet.cell(row=row_number, column=8).value = oldWeekSchedule[("martes", worker)][2]
                if ("miÃ©rcoles", worker) in oldWeekSchedule:
                    sheet.cell(row=row_number, column=9).value = oldWeekSchedule[("miÃ©rcoles", worker)][0]
                    sheet.cell(row=row_number, column=10).value = oldWeekSchedule[("miÃ©rcoles", worker)][1]
                    sheet.cell(row=row_number, column=11).value = oldWeekSchedule[("miÃ©rcoles", worker)][2]
                if ("jueves", worker) in oldWeekSchedule:
                    sheet.cell(row=row_number, column=12).value = oldWeekSchedule[("jueves", worker)][0]
                    sheet.cell(row=row_number, column=13).value = oldWeekSchedule[("jueves", worker)][1]
                    sheet.cell(row=row_number, column=14).value = oldWeekSchedule[("jueves", worker)][2]
                if ("viernes", worker) in oldWeekSchedule:
                    sheet.cell(row=row_number, column=15).value = oldWeekSchedule[("viernes", worker)][0]
                    sheet.cell(row=row_number, column=16).value = oldWeekSchedule[("viernes", worker)][1]
                    sheet.cell(row=row_number, column=17).value = oldWeekSchedule[("viernes", worker)][2]
                row_number += 1
                
    wb.save("ResumHorari.xlsx")


def executarResumHoraris():
    
    st.header("Horari Sumary")
    hipotesi = process_User_Input()
    weekSchedule = st.text_area("Horari de la setmana")
    oldWeekSchedule = st.text_area("Horari de la setmana anterior")
    if weekSchedule != "":
        if oldWeekSchedule != "":
            oldWeekSchedule = process_OldWeek_Schedule(oldWeekSchedule)
        weekSchedule = process_Week_Schedule(weekSchedule, hipotesi)     
        newWeekSchedule = generate_weekly_schedule(weekSchedule, hipotesi)
        generate_Excel_File(oldWeekSchedule, newWeekSchedule)
        with open("ResumHorari.xlsx", "rb") as file:
                    st.download_button(
                        label='Descarregar Fitxer Excel',
                        data=file.read(),
                        file_name='ResumHorari.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
        print("Done")

if __name__ == "__main__":
    executarResumHoraris()
