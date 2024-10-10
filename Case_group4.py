

df1 = pd.read_csv('schedule_airport.csv')
df2 = pd.read_csv('airports-extended-clean.csv', delimiter=';')
df3 = df2[df2['Type']=='station']

# Merge de datasets
df_merged = df1.merge(df2, left_on='Org/Des', right_on='ICAO', how='left')

df_merged['ATA_ATD_ltc'] = pd.to_timedelta(df_merged['ATA_ATD_ltc'])
df_merged['STA_STD_ltc'] = pd.to_timedelta(df_merged['STA_STD_ltc'])

df_merged['STD2'] = pd.to_datetime(df_merged['STD'], dayfirst=True, errors='coerce')
df_merged['month'] = df_merged['STD2'].dt.month
df_merged['year'] = df_merged['STD2'].dt.year
df_merged['weekday'] = df_merged['STD2'].dt.weekday

# Bereken het verschil tussen de twee kolommen
df_merged['verschil'] = df_merged['ATA_ATD_ltc'] - df_merged['STA_STD_ltc']
df_merged['verschil_in_minuten'] = df_merged['verschil'].dt.total_seconds() / 60

# Filter de data voor de jaren 2019 en 2020
df_merged_2019 = df_merged.loc[df_merged['STD'].str.contains('2019')]
df_merged_2020 = df_merged.loc[df_merged['STD'].str.contains('2020')]

# Create tabs to separate sections
st.title("Visualisatie van Luchthavens en Vluchten")
tab1, tab2, tab3, tab4 = st.tabs(["Kaarten", "Vertraging", "Vluchten van AMS-BCN", "Vluchten hoogte Visualisatie"])




#-----Kaart drukte------------------------------------------------------------------------------------------------

# Groepeer op luchthavens en tel het aantal vluchten
df_drukte_beide = df_merged[['Name', 'Longitude', 'Latitude']].groupby('Name').agg(
    Latitude=('Latitude', 'first'),
    Longitude=('Longitude', 'first'),
    Count=('Name', 'count')
).reset_index()

df_drukte_2019 = df_merged_2019[['Name', 'Longitude', 'Latitude']].groupby('Name').agg(
    Latitude=('Latitude', 'first'),
    Longitude=('Longitude', 'first'),
    Count=('Name', 'count')
).reset_index()

df_drukte_2020 = df_merged_2020[['Name', 'Longitude', 'Latitude']].groupby('Name').agg(
    Latitude=('Latitude', 'first'),
    Longitude=('Longitude', 'first'),
    Count=('Name', 'count')
).reset_index()

# Omzetten van coördinaten
df_drukte_2019['Latitude'] = df_drukte_2019['Latitude'].astype(str).str.replace(',', '.').astype(float)
df_drukte_2019['Longitude'] = df_drukte_2019['Longitude'].astype(str).str.replace(',', '.').astype(float)
df_drukte_2020['Latitude'] = df_drukte_2020['Latitude'].astype(str).str.replace(',', '.').astype(float)
df_drukte_2020['Longitude'] = df_drukte_2020['Longitude'].astype(str).str.replace(',', '.').astype(float)
df_drukte_beide['Latitude'] = df_drukte_beide['Latitude'].astype(str).str.replace(',', '.').astype(float)
df_drukte_beide['Longitude'] = df_drukte_beide['Longitude'].astype(str).str.replace(',', '.').astype(float)

# Stel het midden van de kaart in
midpoint = (df_drukte_beide['Latitude'].mean(), df_drukte_beide['Longitude'].mean())


with tab1:
    st.markdown("### Kaart met de drukte per luchthaven voor 2019 en 2020")
    st.write("De onderstaande kaart geeft de drukte per luchthaven weer. Dit geeft dus aan hoeveel vluchten er\
                van of naar Zurich gaan vanuit de bepaalde luchthavens. Er kan gefilterd worden op de jaren 2019 en 2020.\
             Als beide jaren worden gekozen dan laat de kaart de totale drukte van beide jaren zien")
    
    # Maak een Streamlit-kolomindeling voor checkboxen en legenda
    col1, col2 = st.columns([1, 1])  # Twee gelijke kolommen

    with col1:
        show_2019 = st.checkbox("Toon 2019", value=True)
        show_2020 = st.checkbox("Toon 2020", value=True)

    with col2:
        st.markdown(
            """
            <div style="background-color:white; padding:10px; border-radius:5px; box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);">
                <b>Legenda:</b><br>
                <span style="background-color:rgba(0, 0, 255, 0.78); border-radius:2px; padding:5px; color:white">2019: Blauw</span><br>
                <span style="background-color:rgba(191, 235, 255, 0.78); border-radius:2px; padding:5px; color:black">2020: Lichtblauw</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Maak een lijst van layers op basis van de geselecteerde checkboxen
    layers = []

    if show_2019:
        layer_2019 = pdk.Layer(
            'ColumnLayer',
            data=df_drukte_2019,
            get_position='[Longitude, Latitude]',
            get_elevation='Count',
            elevation_scale=100,
            radius=20000,
            get_fill_color='[0, 0, 255, 200]',  # Blauw voor 2019
            pickable=True,
            auto_highlight=True
        )
        layers.append(layer_2019)

    if show_2020:
        layer_2020 = pdk.Layer(
            'ColumnLayer',
            data=df_drukte_2020,
            get_position='[Longitude, Latitude]',
            get_elevation='Count',
            elevation_scale=100,
            radius=20000,
            get_fill_color='[191, 235, 255, 200]',  # Lichtblauw voor 2020
            pickable=True,
            auto_highlight=True
        )
        layers.append(layer_2020)

    # Pydeck view instellen (kaartview)
    view_state = pdk.ViewState(
        latitude=midpoint[0],
        longitude=midpoint[1],
        zoom=3,
        pitch=50,  # 3D hoek
    )

    # Verbeterde tooltip
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip={"html": "<b>{Name}</b><br>Count: {Count}", "style": {"color": "white"}},  # Tooltip voor hover
        map_style='road',  # Gebruik de juiste mapstijl
    )

    # Laat de kaart onder de kolommen zien
    st.pydeck_chart(r)

#-----Kaart met treinen, vliegtuigen-------------------------------------------------------------------------------

m = folium.Map(location=(30, 10), zoom_start=3, tiles="cartodb positron")
print(df_merged[['Latitude', 'Longitude']].isnull().sum())
df_merged = df_merged.dropna(subset=['Latitude', 'Longitude'])
print(df_merged[['Latitude', 'Longitude']].isnull().sum())

df_merged['Latitude'] = df_merged['Latitude'].astype(str).str.replace(',', '.').astype(float)
df_merged['Longitude'] = df_merged['Longitude'].astype(str).str.replace(',', '.').astype(float)
df_merged_airports= df_merged.drop_duplicates(subset=['Org/Des'],keep='first').reset_index(drop=True)
df3['Latitude'] = df3['Latitude'].astype(str).str.replace(',', '.').astype(float)
df3['Longitude'] = df3['Longitude'].astype(str).str.replace(',', '.').astype(float)

location_nl = [52.3784, 4.9009]

m = folium.Map(location=location_nl, zoom_start=5, tiles='cartodb positron')

# Voeg luchthavens toe aan de kaart
for i in range(len(df_merged_airports)):
    html_marker = f"""
    <div style="font-size: 12px; color: black;">
        <i class="fa fa-plane" aria-hidden="true"></i>
    </div>
    """
    folium.Marker(
        location=[df_merged_airports.iloc[i]['Latitude'], df_merged_airports.iloc[i]['Longitude']],
        popup=df_merged_airports.iloc[i]['Name'],
        icon=folium.DivIcon(html=html_marker)
    ).add_to(m)

# Voeg treinen toe aan de kaart
for i in range(len(df3)):
    html_marker = f"""
    <div style="font-size: 6px; color: gray;">
        <i class="fa fa-train" aria-hidden="true"></i>
    </div>
    """
    folium.Marker(
        location=[df3.iloc[i]['Latitude'], df3.iloc[i]['Longitude']],
        popup=df3.iloc[i]['Name'],
        icon=folium.DivIcon(html=html_marker)
    ).add_to(m)

# Toon de Folium kaart in de Streamlit-app
with tab1:
    st.markdown("### Kaart van alle luchthavens en stations")
    st.write("Deze kaart is een overzicht van alle luchthavens en stations. De luchthavens zijn met een vliegtuigicoontje\
             weergegeven en de stations met een treinicoontje")
    st_folium = st.components.v1.html(m._repr_html_(), height=500, scrolling=True)

#-----Vertraging kaart----------------------------------------------------------------------------------------

df_merged.groupby(['Org/Des'])['verschil_in_minuten'].mean().apply(lambda x: x)

df_avg = df_merged.groupby(['Org/Des', 'Latitude', 'Longitude'])['verschil_in_minuten'].median().reset_index()

def get_color(value):
    if value < 0:
        return '#32cd32'  # Optijd (te vroeg)
    else:
        return '#ff3030'  # Te laat
#66c266

# Maak de tweede kaart aan met dezelfde stijl als de eerste kaart
  # Gebruik standaard OpenStreetMap stijl
m3 = folium.Map(tiles="cartodb positron")

# Add CircleMarkers to the map
for index, row in df_avg.iterrows():
    folium.CircleMarker(
        location=(row['Latitude'], row['Longitude']),
        radius=2,  # Smallest radius to serve as a dot
        color=get_color(row['verschil_in_minuten']),
        fill=True,
        fill_color=get_color(row['verschil_in_minuten']),
        fill_opacity=1  # Fully filled to appear as a colored dot
    ).add_to(m3)

# Display the map in Streamlit
with tab1:
    st.markdown("### Vertraagd of op tijd per luchthaven")
    st.write("Deze onderstaande kaart laat zien per luchthaven of er gemiddeld vertraging is, of dat de vliegtuigen \
             op tijd aankomen/vertrekken. Met groen wordt aangegeven welke luchthavens geen vertraging hebben en met \
             rood wordt aangegeven welke luchthavens wel vertraging hebben. Dit is een overzicht voor 2019 en 2020")
    st_folium2 = st.components.v1.html(m3._repr_html_(), height=500, scrolling=True)

#-----Vertraging per jaar kaart------------------------------------------------------------------------------------

df_map = df_merged.groupby('Country')['verschil_in_minuten'].mean().reset_index()

with open("countries.geojson", "r") as f:
    geojson_data = json.load(f)

geojson_landnamen = [feature['properties']['ADMIN'] for feature in geojson_data['features']]

# Maak een automatische mapping van de landnamen
mapping = {}
for Country in df_map['Country']:
    # Zoek de beste overeenkomende naam in de GeoJSON
    close_matches = get_close_matches(Country, geojson_landnamen, n=1, cutoff=0.6)
    if close_matches:  # Als er een overeenkomende naam is gevonden
        mapping[Country] = close_matches[0]
    else:
        mapping[Country] = None  # Geen overeenkomst gevonden


# Vervang de landnamen in de DataFrame op basis van de mapping
df_map['GeoJSON_Land'] = df_map['Country'].map(mapping)

# Filter de DataFrame om alleen landen met een overeenkomende GeoJSON naam te behouden
df_map = df_map.dropna(subset=['GeoJSON_Land'])

m = folium.Map(location=[52.3676, 4.9041], zoom_start=2)

max_delay = df_map['verschil_in_minuten'].max()
min_delay = df_map['verschil_in_minuten'].min()

# Stel de threshold_scale in, inclusief de min en max vertraging
threshold_scale = [min_delay, 10, 20, 30, 40, 50, max_delay]

landen_met_data = df_map['GeoJSON_Land'].unique()
gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
landen_zonder_data = gdf[~gdf['ADMIN'].isin(landen_met_data)]

# Voeg een Choropleth toe voor het kleuren van de landen
folium.Choropleth(
    geo_data=geojson_data,  # GeoJSON met landen
    name='choropleth',
    data=df_map,
    columns=['GeoJSON_Land', 'verschil_in_minuten'],  # Kolommen voor matching en kleuren
    key_on='feature.properties.ADMIN',
    fill_color='YlOrRd',  # Kleurenschaal: Geel-Oranje-Rood
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Vertraging in minuten',
    threshold_scale=threshold_scale,  # Dynamisch gegenereerde schaal
).add_to(m)

folium.GeoJson(
    data=landen_zonder_data.__geo_interface__,
    style_function=lambda feature: {
        'fillColor': 'lightgray',
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7
    },
    name='Landen zonder data'
).add_to(m)

m_html = m._repr_html_()

# Gebruik Streamlit om de kaart weer te geven
with tab2:
    st.markdown("### Vertraging per land")
    st.write('Per land is hier te zien hoe groot de gemiddelde vertraging over 2019 en 2020 is. De landen waar de vertraging\
             niet van bekend is zijn grijs gekleurd.')
    st.components.v1.html(m_html, height=600)

#-----Vertraging per maand-----------------------------------------------------------------------------------------

grouped_df_2019_month = df_merged_2019.groupby('month')['verschil_in_minuten'].mean().reset_index() #gem vertraging per maand
grouped_df_2020_month = df_merged_2020.groupby('month')['verschil_in_minuten'].mean().reset_index() #gem vertraging per maand

line_fig = go.Figure()

line_fig.add_trace(go.Bar(
    x=grouped_df_2019_month['month'],
    y=grouped_df_2019_month['verschil_in_minuten'],
    name='Gemiddelde vertraging 2019',
))
line_fig.add_trace(go.Bar(
    x=grouped_df_2020_month['month'],
    y=grouped_df_2020_month['verschil_in_minuten'],
    name='Gemiddelde vertraging 2020'
))
line_fig.add_trace(go.Scatter(
    x=grouped_df_2019_month['month']-0.2,
    y=grouped_df_2019_month['verschil_in_minuten'],
    mode='lines+markers',
    name='Verloop 2019',
    line=dict(color='blue', width=2),  # Pas de kleur aan naar wens
    marker=dict(size=5),
))
line_fig.add_trace(go.Scatter(
    x=grouped_df_2020_month['month']+0.2,
    y=grouped_df_2020_month['verschil_in_minuten'],
    mode='lines+markers',
    name='Verloop 2020',
    line=dict(color='lightblue', width=2),  # Pas de kleur aan naar wens
    marker=dict(size=5),
))
line_fig.update_layout(
    title='Gemiddelde vertraging per maand',
    xaxis_title='Maand',
    yaxis_title='Gemiddelde vertraging in minuten',
    xaxis=dict(
        tickmode='array',
        tickvals=grouped_df_2019_month['month'].tolist(),
        ticktext=[
            'Januari', 'Februari', 'Maart', 'April', 'Mei', 
            'Juni', 'Juli', 'Augustus', 'September', 'Oktober', 
            'November', 'December'
        ],
    ),
    autosize=False,
    margin=dict(l=80, r=80, b=100, t=50),
)

# Vertraging per weekdag:
grouped_df_2019_weekday = df_merged_2019.groupby('weekday')['verschil_in_minuten'].mean().reset_index() #gem vertraging per maand
grouped_df_2020_weekday = df_merged_2020.groupby('weekday')['verschil_in_minuten'].mean().reset_index() #gem vertraging per maand

line_fig2 = go.Figure()

line_fig2.add_trace(go.Bar(
    x=grouped_df_2019_weekday['weekday'],
    y=grouped_df_2019_weekday['verschil_in_minuten'],
    name='Gemiddelde vertraging per dag in 2019',
))
line_fig2.add_trace(go.Bar(
    x=grouped_df_2020_weekday['weekday'],
    y=grouped_df_2020_weekday['verschil_in_minuten'],
    name='Gemiddelde vertraging per dag in 2020'
))
line_fig2.add_trace(go.Scatter(
    x=grouped_df_2019_weekday['weekday']-0.2,
    y=grouped_df_2019_weekday['verschil_in_minuten'],
    mode='lines+markers',
    name='Verloop 2019',
    line=dict(color='blue', width=2),  # Pas de kleur aan naar wens
    marker=dict(size=5),
))
line_fig2.add_trace(go.Scatter(
    x=grouped_df_2020_weekday['weekday']+0.2,
    y=grouped_df_2020_weekday['verschil_in_minuten'],
    mode='lines+markers',
    name='Verloop 2020',
    line=dict(color='lightblue', width=2),  # Pas de kleur aan naar wens
    marker=dict(size=5),
))
line_fig2.update_layout(
    title='Gemiddelde vertraging per dag',
    xaxis_title='Dag',
    yaxis_title='Gemiddelde vertraging in minuten',
    xaxis=dict(
        tickmode='array',
        tickvals=grouped_df_2019_weekday['weekday'].tolist(),  # Voeg hier de weekdagwaarden toe
        ticktext=['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'],
    ),
    autosize=False,
    margin=dict(l=80, r=80, b=100, t=50),
)
with tab2:
    st.markdown("### Gemiddelde Vertraging per Maand en Dag")
    st.write("Deze grafieken geven de gemiddelde vertraging per maand en per weekdag aan. Om de grafieken goed te zien\
             kan je naar instellingen gaan en 'wide mode' aanzetten. De grafieken geven de vertraging aan voor 2019 en 2020\
             en de negatieve waarden geven aan dat er geen vertraging was, maar dat de vliegtuigen juist eerder dan \
             gepland zijn geland of vertrokken.")
    
    col1, col2 = st.columns(2)  # Maak 2 kolommen aan

    with col1:
        st.plotly_chart(line_fig)

    with col2:
        st.plotly_chart(line_fig2)

#-----Grafiek die veranderd met dropdown--------------------------------------------------------------------------

df_merged['Airline'] = df_merged['FLT'].str.extract(r'([A-Z]{1,3})', expand=False)

airline_mapping = {
    'A': 'Aloha Airlines',
    'AA': 'American Airlines',
    'AF': 'Air France',
    'AT': 'Royal Air Maroc',
    'AY': 'Finnair',
    'AZ': 'Alitalia',
    'BA': 'British Airways',
    'BT': 'airBaltic',
    'CJ': 'Classic Jet',
    'CX': 'Cathay Pacific',
    'DL': 'Delta Air Lines',
    'EI': 'Aer Lingus',
    'EK': 'Emirates',
    'EW': 'Eurowings',
    'EY': 'Etihad Airways',
    'EZY': 'easyJet',
    'GM': 'Germania',
    'IB': 'Iberia',
    'JP': 'Adria Airways',
    'JU': 'Air Serbia',
    'KL': 'KLM Royal Dutch Airlines',
    'KM': 'Air Malta',
    'LH': 'Lufthansa',
    'LO': 'LOT Polish Airlines',
    'LX': 'Swiss International Air Lines',
    'LY': 'El Al Israel Airlines',
    'OS': 'Austrian Airlines',
    'OU': 'Croatia Airlines',
    'PC': 'Pegasus Airlines',
    'PS': 'Ukraine International Airlines',
    'QR': 'Qatar Airways',
    'SK': 'SAS Scandinavian Airlines',
    'SQ': 'Singapore Airlines',
    'SU': 'Aeroflot',
    'TG': 'Thai Airways',
    'TK': 'Turkish Airlines',
    'TP': 'TAP Air Portugal',
    'TU': 'Tunisair',
    'U': 'Transavia Airlines',
    'UA': 'United Airlines',
    'UX': 'Air Europa',
    'VY': 'Vueling',
    'WK': 'Helvetic Airways',
    'WY': 'Oman Air',
    'AC': 'Air Canada',
    'FI': 'Icelandair',
    'HU': 'Hainan Airlines',
    'KE': 'Korean Air',
    'RJ': 'Royal Jordanian',
    'T': 'TUI Airlines',
    'XQ': 'SunExpress',
    'YM': 'Montenegro Airlines',
    'ELB': 'Air Transat',
    'FB': 'Bulgaria Air',
    'TOM': 'Thomas Cook Airlines',
    'L': 'Lauda Air',
    'KK': 'InterSky',
    'SM': 'Smartwings',
    'W': 'Air Zimbabwe',
    'UZB': 'Uzbekistan Airways',
    'QS': 'SmartWings',
    'X': 'Xinjiang Airlines',
    'AP': 'Air Punjab',
    'TDR': 'Tropic Air',
    'AXE': 'Axe Airlines',
    'Y': 'Yeti Airlines',
    'FEG': 'Far Eastern Air Transport',
    'ARN': 'Aran Air',
    'GX': 'Go Air',
    'KF': 'Blue1',
    'VIP': 'VIP Air',
    'XXP': 'China United Airlines',
    'Q': 'Qantas',
    'EUP': 'Europcar',
    'ZT': 'Airstar Airlines',
    'KLJ': 'Air Koryo',
    'TWI': 'Twin Jet',
    'YW': 'CityJet',
    'WDL': 'WDL Aviation',
    'EJU': 'Eurowings Discover',
    'CA': 'Air China',
    'GNJ': 'Guna Air',
    'SR': 'Surinam Airways',
    'HV': 'Transavia',
    'MS': 'EgyptAir',
    'CY': 'Cyprus Airways',
    'ENT': 'Enter Air',
    'CAI': 'Cairo Air',
    'OTF': 'Oasis Hong Kong Airlines',
    'LMU': 'Air Luxor',
    'NMA': 'NMA Airlines',
    'BE': 'Flybe',
    'WF': 'Wideroe',
    'LG': 'Lignes Aeriennes Congolaises',
    'PE': 'Peruvian Airlines',
    'PAV': 'Pan Am',
    'MHV': 'MHV Airlines',
    'AEH': 'Aeronex',
    'YDY': 'Yeti Airlines',
    'TB': 'TUI fly',
    'TF': 'Air Greenland',
    'SRN': 'Sprint Air',
    'BGH': 'Buraq Air',
    'ENZ': 'Enzo Airlines',
    'XM': 'Xiamen Airlines',
    'FHY': 'Flynas',
    'SV': 'Saudi Arabian Airlines',
    'EZS': 'EasyJet Switzerland',
    'FV': 'Rossiya Airlines',
    'DRU': 'Druk Air',
    'AXY': 'Axon Airlines',
    'CXI': 'Cargolux',
    'ATV': 'Atlantic Airways',
    'FPO': 'FPO Airlines',
    'SZ': 'Shenzhen Airlines',
    'S': 'Siberia Airlines',
    'LLM': 'LLM Airlines',
    'KRP': 'KRP Airlines',
    'SQP': 'SAP Airlines',
    'PVG': 'Puente Verde Airlines',
    'ET': 'Ethiopian Airlines',
    'NYX': 'Nykobing Airlines',
    'VKA': 'Valtour Airlines',
    'FTL': 'Forteleza Airlines',
    'MTL': 'Matanuska Airlines',
    'PQ': 'Pacific Air',
    'ZB': 'Zambezi Airlines',
    'AHY': 'African Airlines',
    'XC': 'XC Airlines',
    'IMX': 'Indian Mountain Airlines',
    'MMO': 'Madhu Airlines',
    'HRB': 'Hrb Air',
    'ED': 'Egyptair',
}

df_merged['Airline'] = df_merged['Airline'].map(airline_mapping)

column_mapping = {
    'ACT': 'Vliegtuigtype',
    'Name': 'Luchthaven',
    'Airline': 'Luchtvaartmaatschappij',
    'City': 'Stad',
    'Country': 'Land'
}

options = list(column_mapping.values())

# Checkbox om te kiezen tussen gemiddelde of totale vertraging
with tab2:
    st.markdown('### Top 10 meest vertraagde met bijbehorende drukte')
    st.write('Hieronder kan een gegeven worden geselecteerd waarvan de grafiek de bijbehorende gegevens laat zien.\
              De grafiek laat de top 10 meest vertraagde in de gekozen categorie zien, en hij laat op de rechter y-as\
             de drukte/frequentie van vluchten zien. Als de optie voor gemiddelde vertraging wordt uitgezet bij de checkbox\
              dan laat de grafiek de totale vertraging zien.')
    selected_option = st.selectbox('Selecteer een gegeven', options)
    is_gemiddelde = st.checkbox('Toon Gemiddelde Vertraging', value=True)

# Tel de frequentie van elke waarde in de geselecteerde kolom
selected_column = [key for key, value in column_mapping.items() if value == selected_option][0]

# Tel de frequentie van elke waarde in de geselecteerde kolom
frequentie = df_merged[selected_column].value_counts()

# Filter op frequentie >= 10
frequentie_gefilterd = frequentie[frequentie >= 35]

# Bereken de gemiddelde of totale vertraging voor de gefilterde waarden
if is_gemiddelde:
    # Gemiddelde vertraging
    top10_sums = df_merged[df_merged[selected_column].isin(frequentie_gefilterd.index)] \
        .groupby(selected_column)['verschil_in_minuten'].mean().nlargest(10).reset_index()
else:
    # Totale vertraging
    top10_sums = df_merged[df_merged[selected_column].isin(frequentie_gefilterd.index)] \
        .groupby(selected_column)['verschil_in_minuten'].sum().nlargest(10).reset_index()

# Haal de top 10 waarden op basis van de hoogste vertraging (gemiddeld of totaal)
top10 = top10_sums[selected_column].tolist()

# Frequentie tellen van de top 10 waarden
drukte = df_merged[selected_column].value_counts().reindex(top10).fillna(0)

# Maak een lege figuur aan voor de grafiek
line_fig = go.Figure()

# Staafdiagram voor de top 10 som van 'verschil_in_minuten'
line_fig.add_trace(go.Bar(
    x=top10_sums[selected_column],  # Top 10 waarden van de geselecteerde kolom
    y=top10_sums['verschil_in_minuten'],  # Som van 'verschil_in_minuten'
    name='Vertraging in minuten',
    yaxis='y1'
))

# Lijnplot voor de frequentie van de top 10 waarden
line_fig.add_trace(go.Scatter(
    x=top10_sums[selected_column],  # Top 10 waarden van de geselecteerde kolom
    y=drukte.values,  # Frequentie telling van de top 10
    mode='lines+markers',
    name='Aantal vluchten',
    line=dict(color='lightblue', width=2),  # Kleur en breedte van de lijn
    yaxis='y2'  # Tweede y-as
))

# Werk de layout van de grafiek bij
line_fig.update_layout(
    title=f'Top 10 {selected_column} op Basis van {"Gemiddelde" if is_gemiddelde else "Totale"} Vertraging en Frequentie',  # Dynamische titel
    xaxis_title=selected_option,  # Dynamische x-as titel op basis van selectie
    yaxis_title='Vertraging in minuten',
    yaxis2=dict(
        title='Frequentie',
        overlaying='y',
        side='right',  # Plaats aan de rechterkant
        showgrid=False  # Verberg de gridlijnen voor de tweede y-as
    ),
    margin=dict(l=80, r=80, b=100, t=50),
)

# Toon de grafiek met Streamlit
with tab2:
    st.plotly_chart(line_fig)


#-----7 vluchten------------------------------------------------------------------------------------------------

import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math
from branca.element import MacroElement
import plotly.graph_objects as go  # Import Plotly


# Function to load and clean flight data
def load_and_clean_flight_data(file_names):
    dataframes = []
    for file in file_names:
        df = pd.read_excel(file)
        df.dropna(axis=0, inplace=True)  # Clean data by removing NA values
        dataframes.append(df)
    return dataframes

# Haversine function to calculate distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon1_rad - lon2_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c  # Distance in kilometers

# List of flight files for 30 flight data
flight_files_30 = [f"30Flight {i}.xlsx" for i in range(1, 8)]

# Load and clean the data
flights_30 = load_and_clean_flight_data(flight_files_30)

# List of DataFrames with their corresponding colors and renamed flight names
flight_data = [
    (flights_30[i], f"vlucht{i+1}", color) for i, color in enumerate(['blue', 'green', 'red', 'orange', 'purple', 'black', 'cyan'])
]



@st.cache_data
def filter_flights(flight_data,selected_flights):
    return [flight for flight in flight_data if flight[1] in selected_flights]

# Tab 1: Map display with multi-select to choose flights
with tab3:
    st.subheader("Vluchten van Schiphol Airport naar El Prat Airport")
    
    # Get a list of flight names for the multi-select
    flight_names = [flight[1] for flight in flight_data]
    
    # Multi-select widget for flight selection, defaulting to the first flight
    selected_flights = st.multiselect('Selecteer Vluchten', flight_names, default=flight_names[0:2])

    # Filter the flight data based on selected flights
    filtered_flights = filter_flights(flight_data,selected_flights)
    #filtered_flights = [flight for flight in flight_data if flight[1] in selected_flights]

    # If no flight is selected, show a warning
    if not filtered_flights:
        st.warning("Selecteer alstublieft ten minste één vlucht om de kaart weer te geven.")
    else:
        # Create a Folium map centered on a specific coordinate
        mymap = folium.Map(location=[48.8575, 2.3514], zoom_start=5.47)

        # Add markers for Schiphol and Barcelona airports
        popup_c = 'Amsterdam, Schiphol Airport'
        popupS = folium.Popup(popup_c, max_width=300)  
        folium.Marker(
            location=[52.3105, 4.7683],  # Schiphol airport coordinates
            popup=popupS,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(mymap)

        popup_c1 = 'Barcelona, El Prat Airport'
        popupB = folium.Popup(popup_c1, max_width=300)  
        folium.Marker(
            location=[41.2974, 2.0833],  # Barcelona airport coordinates
            popup=popupB,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(mymap)

        # HTML code for the custom legend
        legend_html = '''
            <div style="
            position: fixed;
            top: 10px;
            right: 10px;
            width: 250px;
            height: auto;
            background-color: white;
            border:2px solid grey;
            z-index:9999;
            font-size:14px;
            ">&nbsp;<b>Totale Afstand per Vlucht:</b><br>
        '''

        # Iterate through filtered flight data
        for df, flight_name, color in filtered_flights:
            # Create a list to store latitude/longitude pairs
            coordinates = []
            total_distance = 0.0  # Initialize total distance for each flight

            # Loop through the DataFrame to get lat/lon pairs
            prev_lat, prev_lon = None, None
            for _, row in df.iterrows():
                lat = row["[3d Latitude]"]
                lon = row["[3d Longitude]"]
                coordinates.append((lat, lon))
                
                # Calculate distance if we have previous coordinates
                if prev_lat is not None and prev_lon is not None:
                    distance = haversine(prev_lat, prev_lon, lat, lon)
                    total_distance += distance
                
                # Update previous coordinates
                prev_lat, prev_lon = lat, lon

            # Add total distance to the legend
            legend_html += f'&nbsp;<i style="color:{color};">⬤</i> {flight_name}: {total_distance:.2f} km<br>'

            # Check if the coordinates list is not empty
            if coordinates:
                # Add a line connecting the points with the selected color
                folium.PolyLine(locations=coordinates, color=color, weight=5).add_to(mymap)
                
                # Add rectangles at coordinates with popups
                for _, row in df.iterrows():
                    lat = row["[3d Latitude]"]
                    lon = row["[3d Longitude]"]

                    # Define the size of the rectangle
                    width = 0.001  # Adjust the width
                    height = 0.001  # Adjust the height
                    
                    # Create the southwest and northeast corners of the rectangle
                    southwest = (lat - height / 2, lon - width / 2)
                    northeast = (lat + height / 2, lon + width / 2)

                    # Prepare the popup content
                    time_remaining = (df['Time (secs)'].max() - row['Time (secs)']) / 60  # Remaining time in minutes
                    altitude_ft = row["[3d Altitude Ft]"]
                    true_airspeed = row["TRUE AIRSPEED (derived)"]

                    popup_content = f'Resterende tijd: {time_remaining:.2f} min<br>Hoogte: {altitude_ft} ft<br>Snelheid: {true_airspeed} knopen'

                    # Create and add the rectangle with a popup
                    folium.Rectangle(bounds=[southwest, northeast], color=color, fill=True, fill_opacity=0.4,
                                     popup=folium.Popup(popup_content, max_width=250)).add_to(mymap)

        # Close the HTML div tag for the legend
        legend_html += '</div>'

        # Create a DivIcon for the legend
        legend = folium.map.Marker(
            location=[48.8575, 2.3514],
            icon=folium.DivIcon(html=legend_html)
        )
        
        # Add the legend to the map
        mymap.add_child(legend)

        # Write an explanation about the map and distance calculation
        col1, col2 = st.columns([1, 2])  # Create two columns
        with col1:
            st.write("""\
            **Uitleg van de kaart:**
            Deze kaart toont de vluchtpaden van Amsterdam Schiphol naar Barcelona El Prat Airport. 
            U kunt vluchten selecteren om hun routes en afstanden te bekijken.

            **Hoe de afstand wordt berekend:**
            De afstand tussen twee punten op de aarde wordt berekend met de Haversine-formule. 
            Deze formule houdt rekening met de kromming van de aarde en gebruikt de breedte- en lengtegraad van de luchthavens om de afstand in kilometers te berekenen.
                     
            **Conclusies die uit deze kaart kunnen worden getrokken:**
            - Door de geselecteerde routes te vergelijken, kunt u zien welke route de kortste afstand heeft en dus waarschijnlijk de snelste is.
            - Vluchten die dichter bij de rechte lijn tussen de luchthavens liggen, kunnen minder tijd in beslag nemen en minder brandstof verbruiken.
            - Als er veel verschillende routes zijn voor dezelfde vlucht, kunt u patronen opmerken in de luchtvaartoperaties, zoals voorkeur voor bepaalde luchtcorridors of routes die vaak worden gebruikt.         
            """)
        with col2:
            st_folium(mymap, width=725)

        # Plot altitude over time for all flights
        st.markdown("---")
        st.subheader("Hoogteverloop Over Tijd")
        fig_altitude = go.Figure()
        
        for df, flight_name, _ in flight_data:  # Loop through all flight data
            fig_altitude.add_trace(go.Scatter(
                x=df["Time (secs)"]/60,  # X-axis: Time in minutes
                y=df["[3d Altitude Ft]"],  # Y-axis: Altitude in feet
                mode='lines+markers',  # Display as lines with markers
                name=flight_name,  # Legend label
                line=dict(width=2),  # Line width
                marker=dict(size=8)  # Marker size
            ))

        # Update layout for altitude plot
        fig_altitude.update_layout(
            title='Grafiek Hoogteverloop over tijd',  # Plot title
            xaxis_title='Tijd in minuten',  # X-axis label
            yaxis_title='Hoogte in (Ft)',  # Y-axis label
            showlegend=True,  # Show legend
            xaxis=dict(
                tickmode='linear',
                tick0=0,
                dtick=10, 
                tickangle= -45)
        )
        col3, col4 = st.columns([1, 2])
        with col3:
            st.markdown("""
            **Uitleg van de Hoogteverloop Plot:**
                        
            Deze plot toont de hoogte van de geselecteerde vluchten in voet (Ft) over de tijd in seconden. De X-as geeft de tijd aan vanaf het begin van de vlucht, terwijl de Y-as de hoogte van het vliegtuig weergeeft.
        
            In deze grafiek kunt u de volgende aspecten waarnemen:
        
            - **Hoogtevariatie:** U kunt de stijging en daling van de hoogte tijdens de vlucht volgen. Meestal begint een vlucht met een stijging tot de kruishoogte en daalt het vliegtuig weer tijdens de landing.
            - **Vergelijking van Vluchten:** Door de lijnen van verschillende vluchten te vergelijken, kunt u patronen en verschillen in het hoogteverloop identificeren. Dit helpt te begrijpen hoe luchtvaartmaatschappijen vluchtprofielen beheren en hoe factoren zoals weer en vliegroute invloed hebben.
            - **Consistentie:** Het kan ook helpen om te kijken naar de consistentie van de hoogte over tijd. Vluchten met een constante kruishoogte verbruiken vaak efficiënter brandstof.
            """)

        # Display the altitude plot
        with col4:
            st.plotly_chart(fig_altitude)  # Show the Plotly chart
#__________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________

with tab4:
    import streamlit as st
    import pandas as pd
    import folium
    from streamlit_folium import st_folium
    import plotly.express as px
    df1 = pd.read_excel("30Flight 1.xlsx")
    df2 = pd.read_excel("30Flight 2.xlsx")
    df3 = pd.read_excel("30Flight 3.xlsx")
    df4 = pd.read_excel("30Flight 4.xlsx")
    df5 = pd.read_excel("30Flight 5.xlsx")
    df6 = pd.read_excel("30Flight 6.xlsx")
    df7 = pd.read_excel("30Flight 7.xlsx")
    # Dataframes: df1, df2, df3, df4, df5, df6, df7
    dfs = [df1, df2, df3, df4, df5, df6, df7]

    # Voeg labels voor de dropdown toe
    flight_labels = [f'Flight {i + 1}' for i in range(len(dfs))]

    # Drop-down menu voor het selecteren van vluchten
    selected_flights = st.multiselect(
        'Selecteer vluchten om weer te geven',
        flight_labels,
        default=flight_labels  # Standaard worden alle vluchten weergegeven
    )

    # Functie om kleuren te bepalen op basis van hoogte met meer categorieën
    def altitude_color(altitude):
        if altitude < 2000:
            return 'blue'
        elif altitude < 5000:
            return 'cyan'
        elif altitude < 8000:
            return 'green'
        elif altitude < 11000:
            return 'yellow'
        elif altitude < 14000:
            return 'orange'
        else:
            return 'red'

    # Maak een Folium kaart aan gecentreerd op de route tussen Barcelona en Amsterdam
    m = folium.Map(location=[48.8575, 2.3514], zoom_start=5)

    # Doorloop de geselecteerde vluchten
    for i, df in enumerate(dfs):
        if flight_labels[i] in selected_flights:
            # Haal Latitude, Longitude en Altitude op, en verwijder rijen met NaN-waarden
            df_clean = df.dropna(subset=['[3d Latitude]', '[3d Longitude]', '[3d Altitude M]'])
            latitudes = df_clean['[3d Latitude]'].values
            longitudes = df_clean['[3d Longitude]'].values
            altitudes = df_clean['[3d Altitude M]'].values

            # Maak een polyline voor de route en kleur de punten op basis van hoogte
            for j in range(1, len(latitudes)):
                folium.PolyLine(
                    locations=[[latitudes[j - 1], longitudes[j - 1]], [latitudes[j], longitudes[j]]],
                    color=altitude_color(altitudes[j]),
                    weight=2.5
                ).add_to(m)

    # Toon de Folium kaart in Streamlit
    

    

    # Functie om de taxi-tijd te berekenen voor een vlucht
    def calculate_taxi_time(df):
        # Filter het gedeelte waar de hoogte negatief of nul is (taxi fase)
        taxi_phase = df[df['[3d Altitude M]'] <= 0]
        
        if not taxi_phase.empty:
            # Bereken de tijdsduur van het taxien (in minuten)
            start_time = taxi_phase['Time (secs)'].min()
            end_time = taxi_phase['Time (secs)'].max()
            taxi_duration_secs = end_time - start_time
            taxi_duration_minutes = taxi_duration_secs / 60
            return taxi_duration_minutes
        else:
            return 0  # Geen taxi-tijd gevonden

    # Functie om de totale vluchtduur te berekenen voor een vlucht
    def calculate_flight_duration(df):
        start_time = df['Time (secs)'].min()
        end_time = df['Time (secs)'].max()
        duration_secs = end_time - start_time
        duration_minutes = duration_secs / 60
        return duration_minutes

    # Lijst om de taxi-tijden en vluchtduur van elke vlucht op te slaan
    flight_data = []

    # Doorloop elke vlucht en bereken de taxi-tijd en totale vluchtduur
    for i, df in enumerate(dfs):
        taxi_time = calculate_taxi_time(df)
        flight_duration = calculate_flight_duration(df)
        non_taxi_flight_duration = flight_duration - taxi_time  # vluchtduur zonder taxi-tijd
        flight_data.append({
            'Vlucht': f'Vlucht {i + 1}', 
            'Taxi-tijd (min)': taxi_time, 
            'Vluchtduur zonder taxi-tijd (min)': non_taxi_flight_duration
        })

    # Maak een Pandas DataFrame van de vluchtgegevens
    flight_df = pd.DataFrame(flight_data)

    # Maak een gestapelde staafdiagram met Plotly Express
    fig = px.bar(flight_df, 
                 x='Vlucht', 
                 y=['Taxi-tijd (min)', 'Vluchtduur zonder taxi-tijd (min)'], 
                 title="Taxi-tijd en totale vluchtduur per vlucht",
                 labels={'value': 'Tijd (in minuten)', 'Vlucht': 'Vlucht'},
                 color_discrete_map={'Taxi-tijd (min)': 'red', 'Vluchtduur zonder taxi-tijd (min)': 'blue'})

    # Zet de balken als gestapeld (stacked)
    fig.update_layout(barmode='stack', width=850, height=600)
    
    col5,col6 = st.columns([1,2])
    with col6:
        st_folium(m, width=850, height=500)

    with col5:
        st.subheader("**Kleurencode voor Hoogte:**")
        st.write("""
                    
                    - **Blauw:** Vluchten onder 2000 voet. Deze hoogte is meestal tijdens de start en de landing.
                    - **Cyaan:** Vluchten tussen 2000 en 5000 voet. Dit zijn vaak lage kruishoogtes of delen van de klimfase.
                    - **Groen:** Vluchten tussen 5000 en 8000 voet. Dit kan een tussentijdse kruishoogte zijn of de beginfase van de kruising.
                    - **Geel:** Vluchten tussen 8000 en 11000 voet. Dit is een gemiddelde kruishoogte voor sommige korte vluchten.
                    - **Oranje:** Vluchten tussen 11000 en 14000 voet. Deze hoogte wordt vaak bereikt tijdens langere regionale vluchten.
                    - **Rood:** Vluchten boven 14000 voet. Dit zijn meestal langeafstandsvluchten die hogere kruishoogtes bereiken voor optimale efficiëntie.
                    """)
    st.markdown("----")
    # Visualiseer de gestapelde staafdiagram in Streamlit
    col7, col8 = st.columns([1, 2])
    with col7:
        # Explanation of the chart
        st.subheader("**Uitleg Grafiek**")
        st.write(""" 
        Deze grafiek toont taxi-tijden en totale vluchtduur van verschillende vluchten, waardoor u de operationele efficiëntie van de routes kunt vergelijken.
        """)

        # How the flight duration is calculated
        st.write("**Hoe de vluchtduur wordt berekend**")
        st.write(""" 
        De totale vluchtduur is het tijdsverschil tussen de minimum en maximum tijdstempels. Taxi-tijden zijn de tijd die vliegtuigen op de grond doorbrengen, en de vluchtduur zonder taxi-tijd is de totale vluchtduur min de taxi-tijd.
        """)
        # Conclusions from the chart
        st.write("**Conclusies die uit deze grafiek kunnen worden getrokken**")
        st.write(""" 
        - Vergelijk taxi-tijden en non-taxi vluchtduur om de operationele efficiëntie te analyseren.
        - Langere taxi-tijden kunnen wijzen op luchthavencongestie of vertragingen, wat de totale reistijd beïnvloedt.
        - Deze inzichten kunnen luchtvaartmaatschappijen helpen de prestaties te verbeteren en taxi-tijden te verkorten, wat leidt tot snellere vluchten en lager brandstofverbruik.
        """)  
    with col8:
        st.plotly_chart(fig)

#-----Dynamische grafiek vertraging per fabrikant-----------------------------------------------------------------

mapping_vliegtuig = {
    'A': 'Airbus',
    'B': 'Boeing',
    'C': 'Cessna',
    'D': 'Dassault',
    'E': 'Embraer',
    'F': 'Fokker',
    'S': 'Sukhoi',
    'M': 'McDonnell Douglas',
    'R': 'Bombardier'
}

df_merged['ACT2'] = df_merged['ACT'].astype(str).str[0]
df_merged['Fabrikant'] = df_merged['ACT2'].map(mapping_vliegtuig)

with tab2:
    st.markdown('### Verdeling vertraging en vliegtuigfabrikanten')
    st.write('De onderstaande grafiek laat een verdeling van de vertraging en vliegtuigfabrikanten zien. \
             Hiervoor zijn een aantal keuzes mogelijk. Zo kan er worden gekozen om de data van 2019 of 2020 weer te geven.\
             Daarnaast kan ervoor worden gekozen om de data per jaar, per maand te zien. Hieruit kan worden gehaald welke\
             vliegtuigen van verschillende vliegtuigfabrikanten die maanden vliegen en welke vertraging hebben.')
    # Dropdown voor kiezen tussen 'Alle Data 2019', 'Alle Data 2020', 'Specifieke Maand 2019' of 'Specifieke Maand 2020'
    data_keuze = st.selectbox('Kies de data weergave', options=[
        'Alle Data 2019', 
        'Alle Data 2020', 
        'Specifieke Maand 2019', 
        'Specifieke Maand 2020'
    ])

    # Slider voor het kiezen van de maand (alleen als 'Specifieke Maand' is gekozen)
    if 'Specifieke Maand' in data_keuze:
        # Extraheer het jaar uit de keuze
        jaar = data_keuze.split()[-1]  # '2019' of '2020'
        
        # Slider voor het kiezen van de maand
        maand = st.slider('Kies de maand', min_value=1, max_value=12, value=1, step=1, 
                          format="%d")  # Gebruik maandnummers in de slider
    else:
        maand = None  # Geen specifieke maand geselecteerd

    # Filter de DataFrame
    if data_keuze == 'Alle Data 2019':
        df_filtered = df_merged.loc[df_merged['STD'].str.contains('2019')]
    elif data_keuze == 'Alle Data 2020':
        df_filtered = df_merged.loc[df_merged['STD'].str.contains('2020')]
    else:
        # Filter op jaar en maand
        df_filtered = df_merged.loc[
            (df_merged['STD'].str.contains(jaar)) &  # Filter op het geselecteerde jaar
            (pd.to_datetime(df_merged['STD'], format='%d/%m/%Y').dt.month == maand)  # Filter op maand
        ]

    # Filter om waarden onder -500 uit te sluiten
    df_filtered = df_filtered[df_filtered['verschil_in_minuten'] >= -500]

    # Maak een nieuwe kolom voor de datetime
    df_filtered['Datum'] = pd.to_datetime(df_filtered['STD'], format='%d/%m/%Y')

    # Maak de scatterplot
    fig = px.scatter(
        df_filtered, 
        x='Datum',  # Gebruik de nieuwe kolom met datums
        y='verschil_in_minuten',  # De kolom met vertraging per vlucht
        color='Fabrikant',  # Gebruik de nieuwe 'Fabrikant' kolom voor kleuren
        labels={
            'Datum': 'Dagen',
            'verschil_in_minuten': 'Vertraging (in minuten)',
            'Fabrikant': 'Vliegtuig'
        },
        title='',  # Leeg voor nu, we vullen het later
    )

    # Voeg de layout aan de grafiek toe
    fig.update_layout(
        xaxis_title='Dag',
        yaxis_title='Vertraging (in minuten)',
        xaxis=dict(
            tickmode='array',  # Dit zorgt ervoor dat je de ticks zelf kunt instellen
            tickvals=[],  # We vullen deze ook met de maandlabels
            ticktext=[],  # We vullen deze ook met de maandlabels
        ),
        autosize=True,
        margin=dict(l=40, r=40, b=50, t=50),
    )

    # Verkrijg de unieke maanden en hun bijbehorende dagen
    df_filtered['Maand'] = df_filtered['Datum'].dt.month_name()

    # Maandlabels en hun eerste datum
    month_labels = df_filtered.groupby('Maand')['Datum'].min().reset_index()

    # Voeg de maandlabels toe aan de ticks
    fig.update_xaxes(
        tickvals=month_labels['Datum'],  # Gebruik de eerste datum van elke maand als tickvals
        ticktext=[month[:3] for month in month_labels['Maand']],  # Afkortingen van de maanden
    )

    # Dynamische grafiektitel instellen
    if data_keuze == 'Alle Data 2019':
        fig.update_layout(title='Vertraging per vlucht in 2019')
    elif data_keuze == 'Alle Data 2020':
        fig.update_layout(title='Vertraging per vlucht in 2020')
    elif data_keuze.startswith('Specifieke Maand'):
        maand_naam = pd.to_datetime(f'2021-{maand}-01').strftime('%B')  # Verkrijg de maandnaam
        fig.update_layout(title=f'Vertraging per vlucht in {maand_naam} {jaar}')

    # Toon de grafiek in Streamlit
    st.plotly_chart(fig)

