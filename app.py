import streamlit as st
import pandas as pd
import requests
import re
from io import BytesIO
import pydeck as pdk
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from geopy.geocoders import Nominatim

# --- CONFIG ---
API_KEY = "AIzaSyCH953FeL7QjuaU7H1QyPqd2yWvrYYh_TE"
st.set_page_config(page_title="Branchen-Finder Pro", layout="wide")

# --- FUNCTIONS ---
def get_coordinates(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
    response = requests.get(url).json()
    if response["status"] != "OK" or not response["results"]:
        st.error("❌ Adresse nicht gefunden. Bitte gib z. B. '26603 Aurich' ein.")
        st.stop()
    location = response["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]

def search_places(lat, lng, radius, keyword):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": API_KEY
    }
    results = []
    while True:
        res = requests.get(url, params=params).json()
        results.extend(res.get("results", []))
        next_token = res.get("next_page_token")
        if not next_token:
            break
        import time
        time.sleep(2)
        params["pagetoken"] = next_token
    return results

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,geometry",
        "key": API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})

def extract_email_from_website(url):
    try:
        res = requests.get(url, timeout=5)
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", res.text)
        return emails[0] if emails else ""
    except:
        return ""

def extract_keywords_from_website(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text(separator=' ')
        words = re.findall(r'\b[a-zA-Z]{6,}\b', text.lower())
        keywords = pd.Series(words).value_counts().head(5).index.tolist()
        return ", ".join(keywords)
    except:
        return ""

# --- UI ---
st.title("🔍 Branchen-Finder Pro")

plz = st.text_input("📍 Postleitzahl + Ort", "26603 Aurich")
branche = st.text_input("🏢 Branche (z. B. Architekt, Zahnarzt)", "Architekt")
umkreis = st.slider("📏 Umkreis (in km)", 1, 100, 30)

if st.button("🔎 Suche starten"):
    with st.spinner("🔄 Suche läuft... bitte warten"):
        lat, lng = get_coordinates(plz)
        radius = umkreis * 1000
        places = search_places(lat, lng, radius, branche)

        daten = []
        for ort in places:
            details = get_place_details(ort["place_id"])
            location = details.get("geometry", {}).get("location", {})
            website = details.get("website")
            email = extract_email_from_website(website) if website else ""
            keywords = extract_keywords_from_website(website) if website else ""

            daten.append({
                "Name": details.get("name"),
                "Adresse": details.get("formatted_address"),
                "Telefon": details.get("formatted_phone_number"),
                "Webseite": website,
                "E-Mail": email,
                "Keywords (von Website)": keywords,
                "Latitude": location.get("lat"),
                "Longitude": location.get("lng")
            })

        df = pd.DataFrame(daten)
        st.success(f"✅ {len(df)} Einträge gefunden.")

        st.dataframe(df.drop(columns=["Latitude", "Longitude"]))

        if not df.empty:
            output = BytesIO()
            df.drop(columns=["Latitude", "Longitude"]).to_excel(output, index=False)
            st.download_button(
                label="📥 Excel herunterladen",
                data=output.getvalue(),
                file_name="branchen_suchergebnis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.subheader("🗺️ Standortkarte")
            df_map = df.dropna(subset=["Latitude", "Longitude"])
            st.pydeck_chart(pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=lat,
                    longitude=lng,
                    zoom=9,
                    pitch=0
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data=df_map,
                        get_position='[Longitude, Latitude]',
                        get_radius=200,
                        get_fill_color='[255, 100, 100, 160]',
                        pickable=True
                    )
                ]
            ))
