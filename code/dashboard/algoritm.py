class AnalysisViewSensor(DetailView):
    model = Sensor
    template_name = "web/views/analysis.html"
    context_object_name = 'sensor'

    cifra = 5  # Definir la cantidad de cifras significativas

    def generate_plotly_graph(self, t, LPA, RPI, mRPI, T):
        import plotly.graph_objects as go
        from io import BytesIO
        import base64

        # Definir trazos y colores
        traces = [
            {"name": "LPA", "y": LPA, "color": "green", "dash": "solid", "yaxis": "y1"},
            {"name": "RPI", "y": RPI, "color": "red", "dash": "solid", "yaxis": "y1"},
            {"name": "mRPI", "y": mRPI, "color": "orange", "dash": "dot", "yaxis": "y1"},
            {"name": "Temperature", "y": T, "color": "blue", "dash": "solid", "yaxis": "y2"}
        ]

        # Crear figura y agregar trazos
        fig = go.Figure()
        for trace in traces:
            fig.add_trace(go.Scatter(
                x=t, y=trace["y"],
                mode="lines",
                name=trace["name"],
                line=dict(color=trace["color"], dash=trace["dash"]),
                yaxis=trace["yaxis"]
            ))

        # Configuración del diseño
        layout = dict(
            title=dict(
                text="LPA, RPI, mRPI, and Temperature Analysis",
                font=dict(size=28)
            ),
            xaxis=dict(
                title="Time (h)",
                range=[0, 30],
                dtick=5,
                showgrid=True,
                zeroline=False,
                titlefont=dict(size=28),
                tickfont=dict(size=24)
            ),
            yaxis=dict(
                title="RPI and LPA",
                range=[0, 3],
                dtick=0.5,
                titlefont=dict(color="green", size=28),
                tickfont=dict(size=24, color="green"),
                showgrid=True,
                zeroline=False,
                side="left"
            ),
            yaxis2=dict(
                title="Temperature (°C)",
                range=[0, 12],
                dtick=2,
                titlefont=dict(color="blue", size=28),
                tickfont=dict(size=24, color="blue"),
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=False
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=24)
            ),
            template="plotly_white",
            width=1280,
            height=720
        )
        fig.update_layout(layout)

        # Generar imagen base64 con alta resolución
        buffer = BytesIO()
        fig.write_image(buffer, format="png", width=1920, height=1080, scale=2)
        buffer.seek(0)
        encoded_image = base64.b64encode(buffer.read()).decode("utf-8")
        buffer.close()

        return encoded_image

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = self.object.records.order_by('time')

        if records.exists():
            # Calcular estadísticas básicas
            stats = records.aggregate(
                min_temp=Min('temperature'),
                max_temp=Max('temperature'),
                total_records=Count('id'),
                min_date=Min('time'),
                max_date=Max('time'),
            )
            min_temp = stats['min_temp']
            max_temp = stats['max_temp']
            total_records = stats['total_records']
            min_date = stats['min_date']
            max_date = stats['max_date']

            # Calcular diferencia de tiempo
            time_difference = max_date - min_date
            decimal_days = np.round(time_difference.days + time_difference.seconds / 86400, self.cifra)
            decimal_hours = np.round(time_difference.total_seconds() / 3600, self.cifra)

            # Crear DataFrame desde los registros
            values = records.values_list('number', 'time', 'temperature')
            df = pd.DataFrame(list(values), columns=['number', 'time', 'temperature'])

            # Calcular columnas vectorizadas
            df["t_h"] = (pd.to_datetime(df["time"]) - min_date).dt.total_seconds() / 3600
            df["t"] = df["t_h"] / 24
            df["dt"] = df["t"].diff().fillna(0)
            df["mT"] = (df["temperature"] + df["temperature"].shift(1)) / 2

            # Constantes
            k, a, =  1.30, -0.14

            # Calcular LPD y LPA
            df['LPD'] = np.round(k * (df['mT'] ** a), self.cifra).where(df['mT'].notna(), np.nan)
            df['LPA'] = (df['dt'] / df['LPD']).cumsum()

            # calculos de LPA >=1 
            # Constantes para calculos LPA >=1
            k_b, a_b, k_n, a_n = 0.5757, 3.0481, 0.1226, 0.0517
            dtu = 1 / (24 * 60 * 60)
            Tc = 4
            bc = k_b * np.log(Tc) + a_b
            nc = k_n * (Tc ** a_n)

            # Crear máscara
            mask = df.index[df['LPA'] >= 1]
            
            if len(mask) > 1:
                i = mask[1]
                mT_2 = df.at[i, 'mT']
                dt_2 = df.at[i, 'dt']
                if pd.notna(mT_2) and pd.notna(dt_2):
                    b_2 = round(k_b * np.log(mT_2) + a_b, self.cifra)
                    n_2 = round(k_n * (mT_2 ** a_n), self.cifra)
                    df.at[i, 'b'] = b_2
                    df.at[i, 'n'] = n_2

                    # Modelo original
                    logN_2 = round(b_2 * (dt_2 ** n_2), self.cifra)
                    df.at[i, 'logN'] = logN_2

                    # Modelo compuesto
                    logNc_2 = round(bc * (dt_2 ** nc), self.cifra)
                    df.at[i, 'logNc'] = logNc_2

                    # RPI
                    RPI_2 = round(logN_2 / logNc_2, self.cifra) if logNc_2 > 0 else pd.NA
                    df.at[i, 'RPI'] = RPI_2
                    max_temp = str(RPI_2)+'-'+str(i)+'-'+str(logN_2)+'-'+str(logNc_2)
            # Procesar posiciones 3 en adelante  
            if len(mask) > 2:
                indices = mask[2:]
                for i in indices:
                    mT = df['mT'].iloc[i]
                    dt = df['dt'].iloc[i]
                    b = round(k_b * np.log(mT) + a_b, self.cifra)
                    n = round(k_n * (mT ** a_n), self.cifra)
                    df.at[i, 'b'] = b
                    df.at[i, 'n'] = n

                    # Modelo original
                    prev_logN = df['logN'].iloc[i - 1] 
                    
                    tx = round((prev_logN / b) ** (1 / n) , self.cifra)
                    Na = round(b * ((tx + dtu) ** n) , self.cifra)
                    Nb = round(b * ((tx - dtu) ** n) , self.cifra)
                    mu = round((Na - Nb) / dtu, self.cifra)
                    df.at[i, 'tx'] = tx
                    df.at[i, 'Na'] = Na
                    df.at[i, 'Nb'] = Nb
                    df.at[i, 'mu'] = mu

                    logN = round(mu * dt  + prev_logN , self.cifra)
                    df.at[i, 'logN'] = logN

                    # Modelo compuesto
                    prev_logNc = df['logNc'].iloc[i - 1] 
                    
                    txc = round((prev_logNc / bc) ** (1 / nc) , self.cifra)
                    Nac = round(bc * ((txc + dtu) ** nc) , self.cifra)
                    Nbc = round(bc * ((txc - dtu) ** nc) , self.cifra)
                    muc = round((Nac - Nbc) / dtu, self.cifra)
                    df.at[i, 'txc'] = txc
                    df.at[i, 'Nac'] = Nac
                    df.at[i, 'Nbc'] = Nbc
                    df.at[i, 'muc'] = muc

                    logNc = round(muc * dt  + prev_logNc , self.cifra)
                    df.at[i, 'logNc'] = logNc

                    # RPI y mRPI  
                    RPI = round(logN / logNc, self.cifra) if logNc > 0 else pd.NA
                    df.at[i, 'RPI'] = RPI
                    
                    # Calcular mRPI si existen suficientes registros
                    if pd.notna(logN) and pd.notna(df['logN'].iloc[i - 120]) and pd.notna(logNc) and pd.notna(df['logNc'].iloc[i - 120]):
                        mRPI = round((logN - df['logN'].iloc[i - 120]) / (logNc - df['logNc'].iloc[i - 120]), self.cifra)
                    else:
                        mRPI = pd.NA

                    df.at[i, 'mRPI'] = mRPI
           
            # Convertir valores de LPA > 1 a pd.NA
            df.loc[df['LPA'] > 1, 'LPA'] = pd.NA


            # Actualizar contexto
            context.update({
                "min_temp": min_temp,
                "max_temp": max_temp,
                "total_records": total_records,
                "min_date": min_date,
                "max_date": max_date,
                "decimal_days": decimal_days,
                "decimal_hours": decimal_hours,
                "lpa_data": df['LPA'].fillna(0).tolist(),
                "rpi_data": df['RPI'].fillna(0).tolist(),
                "mrpi_data": df['mRPI'].fillna(0).tolist(),
            })

        else:
            context.update({
                "min_temp": None,
                "max_temp": None,
                "total_records": 0,
                "min_date": None,
                "max_date": None,
                "decimal_days": 0,
                "decimal_hours": 0,
                "lpa_data": [],
                "rpi_data": [],
                "mrpi_data": [],
            })

        # Generar gráfico de Plotly
        if records.exists():
            context['plotly_image'] = self.generate_plotly_graph(
                df['t_h'], 
                df['LPA'].tolist(), 
                df['RPI'].tolist(), 
                df['mRPI'].tolist(), 
                df['temperature']
            )

        return context