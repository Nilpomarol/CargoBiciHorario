import streamlit as st
import pandas as pd
import openpyxl as opxl
from openpyxl.styles import NamedStyle
from datetime import datetime, timedelta
import locale
import json
import os
import re

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
    except ValueError as e:
        print(f"Error converting time string to minutes: {e}")
        return ""
    except IndexError as e:
        print(f"Error converting time string to minutes: {e}")
        return ""



def save_data(data, file_path):
    """Save data to a JSON file."""
    def default_converter(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, timedelta):
            return str(o)
        return o

    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, default=default_converter, indent=4)
        print(f"Data successfully saved to {file_path}.")
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving data to {file_path}: {e}.")
        return False
    
def load_data_variables(file_path, hores_contractades = None, default_data=None):
    """Load data from a JSON file."""
    if default_data is None:
        default_data = {
            "Temps Inici Torn": 12,
            "Temps Fi Torn": 5,
        }

    if hores_contractades is None:
        default_hores_contractades = {}

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Using default data.")
        return default_data, default_hores_contractades

    try:
        with open(file_path, 'r') as file:
            content = json.load(file)
            data = content.get("data", default_data)
            hores_contractades = content.get("hores_contractades", default_hores_contractades)
            return data, hores_contractades
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading file {file_path}: {e}. Using default data.")
        return default_data, default_hores_contractades

def save_data_variables(file_path, data, hores_contractades):
    """
    Save data and hores_contractades into a JSON file.

    Parameters:
    file_path (str): The path to the JSON file to save.
    data (dict): The first dictionary to save.
    hores_contractades (dict): The second dictionary to save.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump({
                "data": data,
                "hores_contractades": hores_contractades
            }, file, indent=4)
        print(f"Data successfully saved to {file_path}.")
    except IOError as e:
        print(f"Error saving file {file_path}: {e}")
    

def load_horari(file_path, default_data=None):
    """Load data from a JSON file."""
    if default_data is None:
        default_data = {}
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Using default data.")
        return default_data

    def date_parser(dct):
        for k, v in dct.items():
            if isinstance(v, str):
                try:
                    dct[k] = datetime.fromisoformat(v)
                except ValueError:
                    pass
        return dct

    try:
        with open(file_path, 'r') as file:
            return json.load(file, object_hook=date_parser)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading file {file_path}: {e}. Using default data.")
        return default_data

def process_hores(hores_contractades, hores_contractades_temp):
    """Process the hours data."""
    processed_hores = hores_contractades_temp
    for line in hores_contractades.splitlines():

        if not line.strip():
            continue

        elements = re.split(r"[\t ]+", line)
        if len(elements) != 2:

            continue


        repartidor = elements[0]
        hores = elements[1]
        processed_hores[repartidor] = hores
    
    return processed_hores 

def process_user_inputs():
    """Process user inputs."""
    file_path = 'variablesSumary.json'
    hipotesi, hores_contractades_temp = load_data_variables(file_path)

    keys = list(hipotesi.keys())
    col1, col2 = st.columns(2)
    with col1:
        hipotesi["Temps Inici Torn"] = int(st.text_input("Temps Inici Torn", hipotesi["Temps Inici Torn"]))
    with col2:
        hipotesi["Temps Fi Torn"] = int(st.text_input("Temps Fi Torn", hipotesi["Temps Fi Torn"]))
    col1, col2, col3 = st.columns(3)

    with col2:
        hores_contractades = st.text_area("Hores Contractades")
    
    
    hores_contractades = process_hores(hores_contractades, hores_contractades_temp)

    with col3:
        df_hores_contractades = pd.DataFrame(hores_contractades, index=[0]).T
        df_hores_contractades.columns = ["Hores Contractades"] 
        st.write(df_hores_contractades)
    # Save data after collecting inputs
    save_data_variables(file_path, hipotesi, hores_contractades)
    return col1, hipotesi, hores_contractades

def process_rutes_reals(rutes_reals):
    """Process the real routes data."""
    # Initialize an empty list to store processed route data
    processed_routes = []
    errors= []

    # Process each line in the input data
    for line in rutes_reals.splitlines():
        if not line.strip():
            continue  # Skip empty lines

        route_elements = re.split(r"\t", line)

        mes = meses.get(route_elements[0].lower())
        data = datetime(datetime.now().year, mes, int(route_elements[1]))
        dia_semana = dias_semana[data.weekday()]
        hora_sortida_ruta = route_elements[7]
        hora_sortida_ruta_aux = horaToInt(hora_sortida_ruta)
        hora_arribada_ruta = route_elements[8]
        repartidor = route_elements[6]
        if repartidor == "":
            repartidor = "XXX"
        if data == "" or dia_semana == "" or hora_sortida_ruta == "" or hora_arribada_ruta == "" or hora_sortida_ruta_aux == "":
            errors.append(f"Error en la entrada de datos. Revisa la línea: {line}")
            continue

        print(f"hora sortida: {hora_sortida_ruta}")
        processed_route = [
            data,
            dia_semana,
            repartidor,
            hora_sortida_ruta,
            hora_arribada_ruta,
            hora_sortida_ruta_aux
        ]
        processed_routes.append(processed_route)

    df = pd.DataFrame(processed_routes, columns=["Data", "Dia Semana", "Repartidor", "Hora Sortida", "Hora Arribada", "Hora Sortida Aux"])
    df = df.sort_values(by=["Data", "Repartidor", "Hora Sortida Aux"])
    df = df.reset_index(drop=True)
    df = df.drop(columns=["Hora Sortida Aux"])
    if errors:
        with st.expander("Errores en la entrada de datos"):
            for error in errors:
                st.error(error)
    return df

def generarHorarisDia(rutes_reals_processades, hipotesi):
    """Generate the summary of the routes."""
    horaris = {}
    for index, ruta in rutes_reals_processades.iterrows():
        if ruta["Repartidor"] not in horaris:
            print(ruta["Hora Sortida"])
            hora_sortida = horaToInt(ruta["Hora Sortida"]) - hipotesi["Temps Inici Torn"]
            hora_arribada = horaToInt(ruta["Hora Arribada"]) + hipotesi["Temps Fi Torn"]
            horaris[ruta["Repartidor"]] = [intToHora(hora_sortida), intToHora(hora_arribada), round((hora_arribada-hora_sortida)/60,1) ,ruta["Data"].date()]
        else:
            horaris[ruta["Repartidor"]][1] = intToHora(horaToInt(ruta["Hora Arribada"]) + hipotesi["Temps Fi Torn"])
            horaris[ruta["Repartidor"]][2] = round((horaToInt(ruta["Hora Arribada"]) + hipotesi["Temps Fi Torn"] - horaToInt(horaris[ruta["Repartidor"]][0]))/60, 1)

    return horaris
       
def generarHorarisTotals(rutes_reals_processades, hipotesi, horaris_totals, col1, col2):
    rutes_reals_processades_per_dia = rutes_reals_processades.groupby(["Data"])
    for dia in rutes_reals_processades_per_dia:
        horaris = generarHorarisDia(dia[1], hipotesi)
        horaris_serializable = {k: [v[0], v[1], v[2], v[3].isoformat()] for k, v in horaris.items()}
        horaris_totals[dia[0][0].date().isoformat()] = horaris_serializable


    cols = [col1, col2]
    num_cols = len(cols)

    # Alternar entre columnas para cada DataFrame
    for i, (dia, horaris) in enumerate(horaris_totals.items()):
        horaris_dataframe = pd.DataFrame(horaris).T
        horaris_dataframe.columns = ["Hora Inici", "Hora Fi", "Hores", "Data"]
        horaris_dataframe = horaris_dataframe.reset_index()
        horaris_dataframe.columns = ["Treballador", "Hora Inici", "Hora Fi", "Hores", "Data"]
        horaris_dataframe = horaris_dataframe[["Data", "Treballador", "Hora Inici", "Hora Fi", "Hores"]]

        # Seleccionar la columna adecuada
        col = cols[i % num_cols]
        with col:
            st.write(f"{dia}: {dias_semana[datetime.fromisoformat(dia).weekday()]}")
            st.write(horaris_dataframe)
    return horaris_totals


def calcular_saldo(horaris_totals, hores_contractades):
    """Calculate the balance of hours for each worker."""
    saldo = {}
    for dia, horaris in horaris_totals.items():
        for treballador, hores in horaris.items():
            if treballador not in hores_contractades:
                hores_contractades_treballador = 0
            else:
                hores_contractades_treballador = hores_contractades.get(treballador, 0)
            if treballador not in saldo:
                saldo[treballador] = 0
            saldo[treballador] += hores[2] - int(hores_contractades_treballador)/5
    return saldo

def executarResumHoraris():
    st.header("Resumen de Horarios")
    col1, hipotesi, hores_contractades = process_user_inputs()
    with col1:
        rutes_reals = st.text_area("Matriu Reporte Hubs")
    
    if not rutes_reals:
        st.stop()
    col1, col2 = st.columns(2)
    rutes_reals_processades = process_rutes_reals(rutes_reals)
    col4,col5,col6 = st.columns(3)
    horaris_totals = load_horari("horaris_processats.json")
    horaris_totals = generarHorarisTotals(rutes_reals_processades, hipotesi, horaris_totals, col4, col5)


    save_data(horaris_totals, "horaris_processats.json")
    saldo = calcular_saldo(horaris_totals, hores_contractades)
    saldo_dataframe = pd.DataFrame(saldo.items(), columns=["Treballador", "Saldo"])
    saldo_dataframe = saldo_dataframe.sort_values(by="Saldo")
    saldo_dataframe = saldo_dataframe.reset_index(drop=True)
    with col6:
        st.write("Saldo de horas")
        st.write(saldo_dataframe)
    #two buttons one for resseting the data in horaris_processats.json and the other for resseting the data in variablesSumary.json
    with col1:
        if st.button("Reset Horaris Processats"):
            horaris_totals = {}
            save_data(horaris_totals, "horaris_processats.json")
            st.write("Horaris Processats reseteados")
    with col2:
        if st.button("Reset Variables"):
            hipotesi = {
                "Temps Inici Torn": 12,
                "Temps Fi Torn": 5,
            }
            hores_contractades = {}
            save_data_variables("variablesSumary.json", hipotesi, hores_contractades)
            st.write("Variables reseteadas")


if __name__ == "__main__":
    executarResumHoraris()