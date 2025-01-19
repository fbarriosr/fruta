import ast
import numpy as np
import pandas as pd
k_b = '0.5'
a_b = '3.4'
Tc = '4'
variables_b_form_Tc = { 'k_b': float(k_b),'a_b': float(a_b), 'mT': Tc }
variables_b_form_Tc = {
    'k_b': float(k_b),
    'a_b': float(a_b),
    'mT': float(Tc),  # Convertir 'mT' a float para evitar errores de tipo
    'np': np          # Agregar numpy al entorno
}

b_form ='k_b * np.log(mT) + a_b'

eval(b_form, {"__builtins__": None}, variables_b_form_Tc)