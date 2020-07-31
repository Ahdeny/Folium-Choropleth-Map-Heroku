from flask import Flask

import folium
import pandas as pd
import geopandas as gpd
import requests

app = Flask(__name__)

@app.route("/")
def index():
    response = requests.get("https://ng-covid-19-api.herokuapp.com/")
    data_json = response.json()
    
    states = data_json["states"].keys()
    dataframe = pd.DataFrame(states, columns = ["States"])

    def get_stats(df, data):
        if data == "confirmed":
            case = data_json["states"][df][0]["confirmed"]
            return int(case.replace(",", ""))
        elif data == "discharged":
            discharge = data_json["states"][df][0]["discharged"]
            return int(discharge.replace(",", ""))
        elif data == "death":
            death = data_json["states"][df][0]["deaths"]
            return int(death.replace(",", ""))
    
    dataframe["Confirmed"] = dataframe["States"].apply(get_stats, data = "confirmed")
    dataframe["Discharged"] = dataframe["States"].apply(get_stats, data = "discharged")
    dataframe["Death"] = dataframe["States"].apply(get_stats, data = "death")

    def fix_states(df):
        if df == "AkwaIbom":
            return "Akwa Ibom"
        elif df == "FCT":
            return "Federal Capital Territory"
        elif df == "CrossRiver":
            return "Cross River"
        else:
            return df

    dataframe["States"] = dataframe["States"].apply(fix_states)

    df = gpd.read_file("The_Naija_Poly.geojson")

    def get_cases_recover_death (df, data):
        api_data = dataframe["States"]
        if df in list(api_data):
            i = list(api_data).index(df)
            if data == "cases":
                case = dataframe.loc[i, "Confirmed"]
                return case
            elif data == "recover":
                recover = dataframe.loc[i, "Discharged"]
                return recover
            elif data == "death":
                death = dataframe.loc[i, "Death"]
                return death
        else:
            return 0

    df["Confirmed Cases"] = df["Name"].apply(get_cases_recover_death, data = "cases")
    df["Discharged"] = df["Name"].apply(get_cases_recover_death, data = "recover")
    df["Death"] = df["Name"].apply(get_cases_recover_death, data = "death")

    total = df["Confirmed Cases"].max()

    folium_map = folium.Map(location = [9.0820, 8.6753],tiles = "Mapbox Control Room", zoom_start = 6, min_zoom = 6, max_zoom = 7,
                    max_lat =16 , max_lon =15 , min_lat = 2 , min_lon =1, max_bounds = True )

    chloro = folium.Choropleth(
    geo_data= df,
    name='choropleth',
    data=df,
    columns=['Name', 'Confirmed Cases'],
    key_on='properties.Name',
    fill_color= "YlOrRd",
    #bins = [0, 100, 400, 700, 900, 1000, 1200, 1500, total+1],
    bins = [0, 0.015*total, 0.15*total, 0.3*total, 0.7*total,total+1],
    fill_opacity=1,
    line_opacity=1,
    legend_name='Confirmed Cases',
    highlight = True,
    
    ).add_to(folium_map)

    for i in range(0, len(df["Name"])):
        
        temp = df.iloc[i]["Name"]
        if temp == "Federal Capital Territory":
            temp = "FCT"
            
        folium.Marker([df.iloc[i]["lon"], df.iloc[i]["lat"]], icon = folium.DivIcon(html = f"""<div style = "font-family: fantasy
                        ; color: black; font-size: smaller; font-weight: boldest"> 
                        {"{}".format(temp) }</div>  """)).add_to(folium_map) 

    chloro.geojson.add_child(folium.features.GeoJsonTooltip(["Name", "Confirmed Cases", "Discharged", "Death"]))



    folium.LayerControl().add_to(folium_map)

    return folium_map._repr_html_()

    if __name__ == "__main__":
        app.run()