import streamlit as st
from horariSumary import *
from generadorHoraris import * 

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title('Menu')
    app_mode = st.sidebar.selectbox('Choose the app mode', ['Generador Horaris', 'Horari Sumary'])
    if app_mode == 'Horari Sumary':
        executarResumHoraris()
    elif app_mode == 'Generador Horaris':
            executarGenerarHoraris()

if __name__ == "__main__":
    main()