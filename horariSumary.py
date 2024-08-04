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
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02}:{mins:02}"


def horaToInt(time_str):
    """Convert a 'hh:mm' or 'hh:mm:ss' formatted string into total minutes."""
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2:
            hours, minutes = parts
            seconds = 0
        elif len(parts) == 3:
            hours, minutes, seconds = parts
        else:
            raise ValueError
        
        total_minutes = hours * 60 + minutes + seconds / 60
        return total_minutes
    except ValueError:
        raise ValueError("Input must be in 'hh:mm' or 'hh:mm:ss' format and contain valid integers.")
    except IndexError:
        raise ValueError("Input must be in 'hh:mm' or 'hh:mm:ss' format.")


def save_data(data, file_path):
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data successfully saved to {file_path}.")
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving data to {file_path}: {e}.")
        return False
    
def load_data(file_path, default_data=None):
    """Load data from a JSON file."""
    if default_data is None:
        default_data = {
            "Temps Inici Torn": 12,
            "Temps Fi Torn": 5,
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

def process_user_inputs():
    """Process user inputs."""
    file_path = 'variablesSumary.json'
    hipotesi = load_data(file_path)
    keys = list(hipotesi.keys())
    print (keys)
    col1, col2 = st.columns(2)
    with col1:
        hipotesi["Temps Inici Torn"] = int(st.text_input("Temps Inici Torn", hipotesi["Temps Inici Torn"]))
    with col2:
        hipotesi["Temps Fi Torn"] = int(st.text_input("Temps Fi Torn", hipotesi["Temps Fi Torn"]))
    # Save data after collecting inputs
    save_data(hipotesi, file_path)
    return hipotesi

def process_rutes_reals(rutes_reals):
    """Process the real routes data."""
    # Initialize an empty list to store processed route data
    processed_routes = []

    # Process each line in the input data
    for line in rutes_reals.splitlines():
        if not line.strip():
            continue  # Skip empty lines

        route_elements = re.split(r"\t", line)

        meses = {
            'enero': 1,
            'febrero': 2,
            'marzo': 3,
            'abril': 4,
            'mayo': 5,
            'junio': 6,
            'julio': 7,
            'agosto': 8,
            'septiembre': 9,
            'octubre': 10,
            'noviembre': 11,
            'diciembre': 12 
        }

        dias_semana = {
            0: 'Lunes',
            1: 'Martes',
            2: 'Miercoles',
            3: 'Jueves',
            4: 'Viernes',
            5: 'Sábado',
            6: 'Domingo'
        }
        
        mes = meses.get(route_elements[0].lower())
        data = datetime(datetime.now().year, mes, int(route_elements[1]))
        dia_semana = dias_semana[data.weekday()]
        hora_sortida_ruta = route_elements[7]
        hora_sortida_ruta_aux = horaToInt(hora_sortida_ruta)
        hora_arribada_ruta = route_elements[8]
        repartidor = route_elements[6]
        processed_route = [
            data,
            dia_semana,
            repartidor,
            hora_sortida_ruta,
            hora_arribada_ruta,
            hora_sortida_ruta_aux
        ]
        processed_routes.append(processed_route)

    return processed_routes

def generarHoraris(rutes_reals_processades, hipotesi):
    """Generate the summary of the routes."""
    horaris = {}
    dia_setmana = rutes_reals_processades.loc[0, "Dia Semana"]
    for index, ruta in rutes_reals_processades.iterrows():
        if ruta["Repartidor"] not in horaris:
            print(horaToInt(ruta["Hora Sortida"]) + hipotesi["Temps Inici Torn"])
            print(intToHora(horaToInt(ruta["Hora Sortida"]) + hipotesi["Temps Inici Torn"]))
            horaris[ruta["Repartidor"]] = [intToHora(horaToInt(ruta["Hora Sortida"]) + hipotesi["Temps Inici Torn"]), intToHora(horaToInt(ruta["Hora Arribada"]) + hipotesi["Temps Fi Torn"])]
        else:
            horaris[ruta["Repartidor"]][1] = intToHora(horaToInt(ruta["Hora Arribada"]) + hipotesi["Temps Fi Torn"])

    st.write(horaris)
    return horaris, dia_setmana
       
def executarResumHoraris():
    st.header("Resumen de Horarios")
    hipotesi = process_user_inputs()
    rutes_reals = st.text_area("Matriu Reporte Hubs")
    rutes_reals_processades = process_rutes_reals(rutes_reals)
    #convertir rutes reals processades a un dataframe
    df = pd.DataFrame(rutes_reals_processades, columns=["Data", "Dia Semana", "Repartidor", "Hora Sortida", "Hora Arribada", "Hora Sortida Aux"])
    df = df.sort_values(by=["Repartidor", "Hora Sortida Aux"])
    df = df.reset_index(drop=True)
    df = df.drop(columns=["Hora Sortida Aux"])
    st.write(df)
    horaris = generarHoraris(df, hipotesi)
    df_horaris = pd.DataFrame(horaris[0]).T
    df_horaris["Dia Setmana"] = horaris[1]
    df_horaris = df_horaris.reset_index()
    df_horaris.columns = ["Repartidor", "Hora Inici", "Hora Fi", "Dia Setmana"]
    df_horaris = df_horaris.sort_values(by=["Dia Setmana", "Hora Inici"])
    st.write(df_horaris)
    






if __name__ == "__main__":
    executarResumHoraris()