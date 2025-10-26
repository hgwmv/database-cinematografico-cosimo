import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import os
import time
from typing import Optional
try:
    import requests
except Exception:
    requests = None

# =====================================
# PAGE CONFIG (no emojis)
# =====================================
st.set_page_config(
    page_title="Database Cinematografico Cosimo",
    page_icon=None,
    layout="wide"
)

# =====================================
# THEMES (original vs early web)
# =====================================
def apply_theme(style_key: str):
    # Early Web 1.0 (default)
    early_web = """
    <style>
      :root {
        --bg: #e5e8ec;
        --text: #111;
        --muted: #333;
        --card: #ffffff;
        --border: #6b6b6b;
        --accent: #0000EE; /* link blue */
        --accent-2: #ff0088;
        --sans: "Arial", "Verdana", sans-serif;
      }
      html, body, .stApp { font-family: var(--sans); background: var(--bg); color: var(--text); }
      .block-container { padding-top: 1.2rem; }
      .main-header {
        font-size: 3rem;
        color: var(--text);
        text-align: center;
        margin-bottom: 1.25rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-shadow: 1px 1px #fff;
      }
      .stats-card, .film-card {
        background-color: var(--card);
        color: var(--text);
        padding: 0.9rem;
        border-radius: 2px;
        border: 1px solid var(--border);
        box-shadow: 2px 2px 0 #b8bcc1;
      }
      .stats-card { border-left: 5px solid var(--accent); }
      .film-card { margin-bottom: 0.5rem; }
      a { color: var(--accent); text-decoration: underline; }
    </style>
    """
    # Original look (your previous style)
    original_style = """
    <style>
      :root {
        --accent: #FF6B6B;
        --text: #222;
        --bg: #ffffff;
      }
      html, body, .stApp { background: var(--bg); color: var(--text); }
      .main-header {
        font-size: 3rem;
        color: var(--accent);
        text-align: center;
        margin-bottom: 2rem;
      }
      .stats-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid var(--accent);
      }
      .film-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
      }
    </style>
    """
    st.markdown(early_web if style_key == "early_web" else original_style, unsafe_allow_html=True)

def _get_query_params():
    # Robust to both old/new Streamlit versions
    try:
        return dict(st.query_params)
    except Exception:
        try:
            return st.experimental_get_query_params()
        except Exception:
            return {}

# NEW: safe secret accessor to avoid StreamlitSecretNotFoundError
def _get_secret(key: str, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

def resolve_style() -> str:
    # Priority: secret STYLE -> env MOVIEDB_STYLE -> (optional) URL ?style=...&token=...
    style = _get_secret("STYLE", None)
    if not style:
        style = os.environ.get("MOVIEDB_STYLE", None)
    if not style:
        qp = _get_query_params()
        style_q = (qp.get("style") if isinstance(qp.get("style"), str) else (qp.get("style", [None])[0])) if qp else None
        token_q = (qp.get("token") if isinstance(qp.get("token"), str) else (qp.get("token", [None])[0])) if qp else None
        # Allow query switch if STYLE_TOKEN is not set; if set, require a matching token
        token_secret = _get_secret("STYLE_TOKEN", None)
        token_ok = (token_secret is None) or (token_secret == token_q)
        if style_q in ("early_web", "original") and token_ok:
            style = style_q
    return style if style in ("early_web", "original") else "early_web"

# =====================================
# DATA LOAD
# =====================================
@st.cache_data
def load_database():
    """Carica il database con caching"""
    try:
        df = pd.read_csv('cosimo-film-visti-excel.csv', sep=';', encoding='cp1252')
        
        # Pulizia dati
        df['Rating_Clean'] = pd.to_numeric(df['Rating 10'].str.replace(',', '.'), errors='coerce')
        df['Year_Clean'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Duration_Clean'] = pd.to_numeric(df['Duration'], errors='coerce')
        df['Watch_Date'] = pd.to_datetime(df['Watched Date'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return pd.DataFrame()

# =====================================
# RENDER HELPERS (no emojis)
# =====================================
def render_film_card(index=None, title="", director=None, year=None, rating=None, duration=None, date=None, highlight=False):
    year_txt = f" ({int(year)})" if pd.notna(year) else ""
    parts = []
    if director:
        parts.append(f"Regia: {director}")
    if rating is not None and pd.notna(rating):
        parts.append(f"Rating: {rating}/10")
    if duration is not None and pd.notna(duration):
        parts.append(f"Durata: {int(duration)} min")
    if date:
        parts.append(f"Data: {date}")
    prefix = f"{index}. " if index is not None else ""
    style = "font-weight:600; color: var(--accent);" if highlight else ""
    st.markdown(f"""
    <div class="film-card">
        <span style="{style}">{prefix}{title}</span>{year_txt}<br>
        <small>{' | '.join(parts)}</small>
    </div>
    """, unsafe_allow_html=True)

# =====================================
# MAIN
# =====================================
def main():
    # Apply theme at runtime (safer than at import time)
    apply_theme(resolve_style())
    # Header (no emojis)
    st.markdown('<h1 class="main-header">Database Cinematografico Cosimo</h1>', unsafe_allow_html=True)
    st.caption("App pronta")
    # REMOVE visible theme selector - keep hidden switch only

    # Carica dati
    df = load_database()

    if df.empty:
        st.error("Impossibile caricare il database. Assicurati che il file CSV sia presente.")
        return

    # Sidebar per navigazione
    st.sidebar.title("Menu Principale")

    menu = st.sidebar.selectbox(
        "Scegli una sezione:",
        [
            "Dashboard Generale",
            "Ricerca Film",
            "Top Film",
            "Analisi Registi",
            "Film in Compagnia",
            "Grafici e Statistiche",
            "Analisi Temporale",
            "Aggiungi Film",  # NEW
            "Metadati TMDb"  # existing
        ]
    )

    # Sezioni principali
    if menu == "Dashboard Generale":
        show_dashboard(df)
    elif menu == "Ricerca Film":
        show_search(df)
    elif menu == "Top Film":
        show_top_films(df)
    elif menu == "Analisi Registi":
        show_directors_analysis(df)
    elif menu == "Film in Compagnia":
        show_companions_analysis(df)
    elif menu == "Grafici e Statistiche":
        show_charts(df)
    elif menu == "Analisi Temporale":
        show_temporal_analysis(df)
    elif menu == "Aggiungi Film":
        show_add_film()
    elif menu == "Metadati TMDb":
        show_tmdb_metadata(df)

# =====================================
# DASHBOARD (remove emojis + use helper)
# =====================================
def show_dashboard(df):
    """Dashboard principale con statistiche generali"""
    st.header("Dashboard Generale")
    
    # Statistiche principali in colonne
    col1, col2, col3, col4 = st.columns(4)
    
    df_valid = df[df['Rating_Clean'].notna()]
    df_features = df[df['Duration_Clean'] >= 40]
    df_shorts = df[df['Duration_Clean'] < 40]
    
    with col1:
        st.markdown("""
        <div class="stats-card">
            <h3>Film Totali</h3>
            <h2>{:,} film</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        avg_rating = df_valid['Rating_Clean'].mean() if len(df_valid) > 0 else 0
        st.markdown("""
        <div class="stats-card">
            <h3>Rating Medio</h3>
            <h2>{:.2f}/10</h2>
        </div>
        """.format(avg_rating), unsafe_allow_html=True)
    
    with col3:
        great_movies = len(df_valid[df_valid['Rating_Clean'] >= 7.5])
        st.markdown("""
        <div class="stats-card">
            <h3>Great Movies</h3>
            <h2>{} film</h2>
        </div>
        """.format(great_movies), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stats-card">
            <h3>Lungometraggi</h3>
            <h2>{:,}</h2>
        </div>
        """.format(len(df_features)), unsafe_allow_html=True)
    
    # Ultimi film aggiunti
    st.subheader("Ultimi Film Aggiunti")
    if len(df[df['Watch_Date'].notna()]) > 0:
        recent_films = df[df['Watch_Date'].notna()].nlargest(10, 'Watch_Date')
        
        # Replace per-film rendering:
        # for _, film in recent_films.iterrows():
        #     ...
        #     render_film_card(...)
        # ...existing code...
        for _, film in recent_films.iterrows():
            rating = film['Rating_Clean'] if pd.notna(film['Rating_Clean']) else None
            watch_date = film['Watch_Date'].strftime('%d/%m/%Y') if pd.notna(film['Watch_Date']) else None
            render_film_card(
                title=film['Name'] if pd.notna(film['Name']) else "Titolo sconosciuto",
                director=film['Director'] if pd.notna(film['Director']) else "Sconosciuto",
                year=film['Year_Clean'],
                rating=rating,
                date=watch_date
            )

# =====================================
# SEARCH (remove emojis + use helper)
# =====================================
def show_search(df):
    """Sezione ricerca film"""
    st.header("Ricerca Film")
    
    # Filtri di ricerca
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("Cerca per titolo:", "")
        search_director = st.text_input("Cerca per regista:", "")
    
    with col2:
        # Sostituisce number_input value=None con selectbox sicuro
        years_list = sorted([int(y) for y in df['Year_Clean'].dropna().unique()], reverse=True)
        year_options = ["Tutti"] + years_list
        selected_year = st.selectbox("Anno (uscita):", year_options, index=0)
        min_rating = st.slider("Rating minimo:", 0.0, 10.0, 0.0, 0.5)
    
    # Applica filtri
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(search_term, case=False, na=False)]
    
    if search_director:
        filtered_df = filtered_df[filtered_df['Director'].str.contains(search_director, case=False, na=False)]
    
    if selected_year != "Tutti":
        filtered_df = filtered_df[filtered_df['Year_Clean'] == int(selected_year)]
    
    if min_rating > 0:
        filtered_df = filtered_df[filtered_df['Rating_Clean'] >= min_rating]
    
    # Risultati
    st.subheader(f"Risultati ({len(filtered_df)} film)")
    
    if len(filtered_df) > 0:
        # Ordina per rating (compatibile con tutte le versioni pandas)
        if 'Rating_Clean' in filtered_df.columns and not filtered_df['Rating_Clean'].isna().all():
            filtered_df = filtered_df.sort_values('Rating_Clean', ascending=False, na_position='last')
        else:
            filtered_df = filtered_df.sort_values('Name', na_position='last')
        
        for i, (_, film) in enumerate(filtered_df.head(50).iterrows(), 1):
            rating = film['Rating_Clean'] if pd.notna(film['Rating_Clean']) else None
            highlight = (rating is not None and float(rating) >= 7.5)
            render_film_card(
                index=i,
                title=film['Name'] if pd.notna(film['Name']) else "Titolo sconosciuto",
                director=film['Director'] if pd.notna(film['Director']) else "Sconosciuto",
                year=film['Year_Clean'],
                rating=rating,
                duration=film['Duration_Clean'],
                highlight=highlight
            )
        if len(filtered_df) > 50:
            st.info(f"Mostrati i primi 50 risultati di {len(filtered_df)}")

# =====================================
# TOP FILMS (remove emojis + use helper)
# =====================================
def show_top_films(df):
    """Top film per anno/decade"""
    st.header("Top Film")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Per Anno", "Per Decennio", "Film 10/10", "Great Movies"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            years_list = sorted([int(year) for year in df['Year_Clean'].dropna().unique()], reverse=True)
            selected_year = st.selectbox("Scegli anno:", years_list)
        with col2:
            top_n = st.slider("Numero film:", 5, 100, 10)
        
        if selected_year:
            year_films = df[df['Year_Clean'] == selected_year]
            year_films_rated = year_films[year_films['Rating_Clean'].notna()]
            
            if len(year_films_rated) > 0:
                top_films = year_films_rated.nlargest(top_n, 'Rating_Clean')
                
                st.subheader(f"Top {top_n} Film del {int(selected_year)}")
                
                for i, (_, film) in enumerate(top_films.iterrows(), 1):
                    render_film_card(
                        index=i,
                        title=film['Name'],
                        director=film['Director'],
                        year=film['Year_Clean'],
                        rating=film['Rating_Clean']
                    )
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            decades = list(range(1920, 2030, 10))
            selected_decade = st.selectbox("Scegli decennio:", decades, index=len(decades)-3)
        with col2:
            top_n_decade = st.slider("Numero film:", 5, 100, 15, key="decade_slider")
        
        decade_films = df[(df['Year_Clean'] >= selected_decade) & (df['Year_Clean'] < selected_decade + 10)]
        decade_films_rated = decade_films[decade_films['Rating_Clean'].notna()]
        
        if len(decade_films_rated) > 0:
            top_decade = decade_films_rated.nlargest(top_n_decade, 'Rating_Clean')
            
            st.subheader(f"Top {top_n_decade} Film anni {selected_decade}s")
            
            for i, (_, film) in enumerate(top_decade.iterrows(), 1):
                render_film_card(
                    index=i,
                    title=film['Name'],
                    director=film['Director'],
                    year=film['Year_Clean'],
                    rating=film['Rating_Clean']
                )
    
    with tab3:
        # Film con voto 10/10
        df_rated = df[df['Rating_Clean'].notna()]
        perfect_films = df_rated[df_rated['Rating_Clean'] == 10.0]
        
        if len(perfect_films) > 0:
            # Ordina per anno (cronologico)
            perfect_films_sorted = perfect_films.sort_values('Year_Clean', ascending=True)
            
            st.subheader(f"I Miei Film 10/10 ({len(perfect_films)} film)")
            
            for i, (_, film) in enumerate(perfect_films_sorted.iterrows(), 1):
                render_film_card(
                    index=i,
                    title=film['Name'],
                    director=film['Director'],
                    year=film['Year_Clean'],
                    rating=film['Rating_Clean']
                )
        else:
            st.info("Nessun film con voto 10/10 trovato nel database")
    
    with tab4:
        # Great Movies (7.5+)
        df_rated = df[df['Rating_Clean'].notna()]
        great_films = df_rated[df_rated['Rating_Clean'] >= 7.5]
        
        if len(great_films) > 0:
            # Ordina per anno (cronologico)
            great_films_sorted = great_films.sort_values('Year_Clean', ascending=True)
            
            st.subheader(f"Great Movies - 7.5+ ({len(great_films)} film)")
            
            # Mostra con paginazione ogni 50 film
            films_per_page = 50
            total_pages = (len(great_films_sorted) + films_per_page - 1) // films_per_page
            
            if total_pages > 1:
                page = st.selectbox("Pagina:", range(1, total_pages + 1))
                start_idx = (page - 1) * films_per_page
                end_idx = start_idx + films_per_page
                films_to_show = great_films_sorted.iloc[start_idx:end_idx]
            else:
                films_to_show = great_films_sorted
            
            for _, film in films_to_show.iterrows():
                render_film_card(
                    title=film['Name'],
                    director=film['Director'],
                    year=film['Year_Clean'],
                    rating=film['Rating_Clean']
                )
            
            if total_pages > 1:
                st.info(f"Pagina {page} di {total_pages} - {len(great_films)} great movies totali")
        else:
            st.info("Nessun Great Movie (7.5+) trovato nel database")

# =====================================
# DIRECTORS (remove remaining emoji in rating line)
# =====================================
def show_directors_analysis(df):
    """Analisi registi"""
    st.header("Analisi Registi")
    
    # Normalizzazione registi (come nel codice originale)
    def normalize_director_name(director):
        if pd.isna(director) or director == '':
            return 'Sconosciuto'
        
        director = str(director).strip()
        
        collaborations = {
            'joel coen': 'Joel & Ethan Coen',
            'ethan coen': 'Joel & Ethan Coen',
            'joel & ethan coen': 'Joel & Ethan Coen',
            'ethan & joel coen': 'Joel & Ethan Coen',
            'coen brothers': 'Joel & Ethan Coen',
            'fratelli coen': 'Joel & Ethan Coen',
        }
        
        director_lower = director.lower()
        for key, value in collaborations.items():
            if key in director_lower:
                return value
        
        return director
    
    df['Director_Normalized'] = df['Director'].apply(normalize_director_name)
    df_features = df[df['Duration_Clean'] >= 40]
    
    tab1, tab2 = st.tabs(["Classifiche Registi", "Dettagli Regista"])
    
    with tab1:
        # Top registi per numero film
        director_counts = df_features['Director_Normalized'].value_counts()
        director_counts = director_counts[director_counts.index != 'Sconosciuto'].head(20)
        
        st.subheader("Top 20 Registi per Numero Film")
        
        for i, (director, count) in enumerate(director_counts.items(), 1):
            director_films = df_features[df_features['Director_Normalized'] == director]
            director_films_rated = director_films[director_films['Rating_Clean'].notna()]
            avg_rating = director_films_rated['Rating_Clean'].mean() if len(director_films_rated) > 0 else 0
            great_movies = len(director_films_rated[director_films_rated['Rating_Clean'] >= 7.5])
            st.markdown(f"""
            <div class="film-card">
                <strong>{i}. {director}</strong><br>
                <small>Film: {count} | Rating medio: {avg_rating:.2f}/10 | Great: {great_movies}</small>
            </div>""", unsafe_allow_html=True)
    
    with tab2:
        # Selezione regista
        directors_list = sorted([d for d in df['Director_Normalized'].unique() if d != 'Sconosciuto'])
        selected_director = st.selectbox("Scegli un regista:", directors_list)
        
        if selected_director:
            director_films = df[df['Director_Normalized'] == selected_director]
            director_films_rated = director_films[director_films['Rating_Clean'].notna()]
            
            # Statistiche regista
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Film Totali", len(director_films))
            with col2:
                avg_rating = director_films_rated['Rating_Clean'].mean() if len(director_films_rated) > 0 else 0
                st.metric("Rating Medio", f"{avg_rating:.2f}/10")
            with col3:
                great_movies = len(director_films_rated[director_films_rated['Rating_Clean'] >= 7.5])
                st.metric("Great Movies", great_movies)
            
            # Filmografia
            st.subheader(f"Filmografia di {selected_director}")
            
            if len(director_films_rated) > 0:
                chronological_films = director_films_rated.sort_values('Year_Clean', ascending=True)
                
                for _, film in chronological_films.iterrows():
                    rating = film['Rating_Clean']
                    year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                    duration = f" - {int(film['Duration_Clean'])}min" if pd.notna(film['Duration_Clean']) else ""
                    title_style = "font-weight: bold; color: var(--accent);" if rating >= 7.5 else ""
                    st.markdown(f"""
                    <div class="film-card">
                        <span style="{title_style}">{film['Name']}</span>{year}{duration}<br>
                        <small>Rating: {rating}/10</small>
                    </div>
                    """, unsafe_allow_html=True)

# =====================================
# COMPANIONS (remove emojis in metrics)
# =====================================
def show_companions_analysis(df):
    """Analisi film visti in compagnia"""
    st.header("Film in Compagnia")
    
    # Controlla se esiste la colonna tag diario
    tag_column = None
    possible_columns = ['Tag Diario', 'tag diario', 'Tag_Diario', 'tag_diario', 'Diario Tag', 'diario_tag']
    
    for col in df.columns:
        if any(tag_col.lower() in col.lower() for tag_col in possible_columns):
            tag_column = col
            break
    
    if not tag_column:
        st.error("Colonna 'Tag Diario' non trovata nel database")
        st.info("Colonne disponibili nel CSV:")
        st.write(list(df.columns))
        return
    
    st.info(f"📊 Analizzando la colonna: '{tag_column}'")
    
    # Dizionario dei compagni
    companions = {
        'c:c': 'Claudia (mamma)',
        'c:a': 'Ale (babbo)', 
        'c:p': 'Priamo',
        'c:r': 'Rebecca',
        'c:k': 'Kenta',
        'd:m': 'Marco Grifò',
        'c:mo': 'Monica',
        'd:p': 'Priamo',
        'c:av': 'Alessandro Valenti',
        'd:r': 'Rebecca',
        'd:k': 'Kenta', 
        'c:m': 'Marco Grifò',
        'd:l': 'Leonardo Romagnoli',
        'c:l': 'Leonardo Romagnoli',
        'c:d': 'Dario',
        'd:sm': 'Simone Malaspina',
        'c:sm': 'Simone Malaspina',
        'd:av': 'Alessandro Valenti',
        'd:d': 'Dario'
    }
    
    # Trova film con tag di compagnia
    companion_films = {}
    
    for tag, name in companions.items():
        # Cerca film che contengono questo tag
        mask = df[tag_column].astype(str).str.contains(tag, case=False, na=False)
        films = df[mask].copy()
        
        if len(films) > 0:
            if name not in companion_films:
                companion_films[name] = pd.DataFrame()
            
            # Unisci i film senza duplicati
            companion_films[name] = pd.concat([companion_films[name], films]).drop_duplicates()
    
    if not companion_films:
        st.warning("Nessun film trovato con tag di compagnia")
        st.info("Tags cercati: c:c, c:a, c:p, c:r, d:m, etc.")
        
        # Mostra esempi di contenuti nella colonna tag
        sample_tags = df[tag_column].dropna().head(10)
        if len(sample_tags) > 0:
            st.info("Esempi di contenuti nella colonna tag:")
            for tag in sample_tags:
                st.write(f"- '{tag}'")
        return
    
    # Calcola statistiche
    all_companion_film_indices = set()
    for films in companion_films.values():
        all_companion_film_indices.update(films.index)
    
    total_companion_films = len(all_companion_film_indices)
    total_films = len(df)
    companion_percentage = (total_companion_films / total_films) * 100
    
    # Statistiche generali
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Film Totali", f"{total_films:,}")
    with col2:
        st.metric("Film in Compagnia", f"{total_companion_films:,}")
    with col3:
        st.metric("Percentuale", f"{companion_percentage:.1f}%")
    
    # Top compagni
    companion_counts = [(name, len(films)) for name, films in companion_films.items()]
    companion_counts.sort(key=lambda x: x[1], reverse=True)
    
    st.subheader("Classifica Compagni di Visione")
    
    for i, (name, count) in enumerate(companion_counts, 1):
        films = companion_films[name]
        films_with_rating = films[films['Rating_Clean'].notna()]
        
        if len(films_with_rating) > 0:
            avg_rating = films_with_rating['Rating_Clean'].mean()
            great_movies = len(films_with_rating[films_with_rating['Rating_Clean'] >= 7.5])
            rating_info = f" | Rating medio: {avg_rating:.2f}/10 | Great: {great_movies}"
        else:
            rating_info = " | Rating medio: N/A"
        
        percentage = (count / total_companion_films) * 100
        st.markdown(f"""
        <div class="film-card">
            <strong>{i}. {name}</strong><br>
            <small>Film: {count} ({percentage:.1f}%) {rating_info}</small>
        </div>""", unsafe_allow_html=True)
    
    # Dettagli per compagno selezionato
    st.subheader("Dettagli Compagno")
    selected_companion = st.selectbox("Scegli un compagno:", list(companion_films.keys()))
    
    if selected_companion:
        films = companion_films[selected_companion]
        films_with_rating = films[films['Rating_Clean'].notna()]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Film Insieme", len(films))
        with col2:
            if len(films_with_rating) > 0:
                avg_rating = films_with_rating['Rating_Clean'].mean()
                st.metric("Rating Medio", f"{avg_rating:.2f}/10")
            else:
                st.metric("Rating Medio", "N/A")
        with col3:
            great_movies = len(films_with_rating[films_with_rating['Rating_Clean'] >= 7.5])
            st.metric("Great Movies", great_movies)
        
        # Lista film con questo compagno
        if len(films_with_rating) > 0:
            st.subheader(f"Film visti con {selected_companion}")
            
            # Ordina per rating decrescente
            top_films = films_with_rating.sort_values('Rating_Clean', ascending=False)
            
            for i, (_, film) in enumerate(top_films.head(20).iterrows(), 1):
                render_film_card(
                    index=i,
                    title=film['Name'],
                    director=film['Director'] if pd.notna(film['Director']) else "Sconosciuto",
                    year=film['Year_Clean'],
                    rating=film['Rating_Clean']
                )
            
            if len(top_films) > 20:
                st.info(f"Mostrati i primi 20 di {len(top_films)} film con rating")

# =====================================
# CHARTS & TEMPORAL (remove emojis in headings/info)
# =====================================
def show_charts(df):
    """Grafici e visualizzazioni"""
    st.header("Grafici e Statistiche")
    
    tab1, tab2 = st.tabs(["Distribuzione Rating", "Attività nel Tempo"])
    
    with tab1:
        df_valid = df[df['Rating_Clean'].notna()]
        
        if len(df_valid) > 0:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Arrotondo per difetto i rating (come nel codice originale)
            df_simplified = df_valid.copy()
            df_simplified['Rating_Simplified'] = df_valid['Rating_Clean'].apply(lambda x: int(x))
            
            # Creo bins per voti interi da 2 a 10 (incluso)
            bins = list(range(2, 11)) + [11]  # Da 2 a 11, così il bin 10 include i voti 10.0
            
            ax.hist(df_simplified['Rating_Simplified'], bins=bins, alpha=0.7, color='lightblue', 
                    edgecolor='black', width=0.8, align='left')
            
            # Statistiche sui voti semplificati
            mean_rating = df_simplified['Rating_Simplified'].mean()
            median_rating = df_simplified['Rating_Simplified'].median()
            
            # Linee statistiche
            ax.axvline(mean_rating, color='red', linestyle='--', linewidth=2, label=f'Media: {mean_rating:.1f}')
            ax.axvline(median_rating, color='green', linestyle='--', linewidth=2, label=f'Mediana: {median_rating:.0f}')
            
            ax.set_xlabel('Rating (voti interi)')
            ax.set_ylabel('Numero di Film')
            ax.set_title('Distribuzione Rating Film')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Imposta i tick per voti interi da 2 a 10
            ax.set_xticks(range(2, 11))
            ax.set_xlim(1.5, 10.5)  # Limiti per centrare le barre
            
            st.pyplot(fig)
            
            # Statistiche
            st.subheader("Statistiche Rating")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Media", f"{mean_rating:.1f}")
            with col2:
                st.metric("Mediana", f"{median_rating:.0f}")
            with col3:
                st.metric("Max", f"{df_simplified['Rating_Simplified'].max()}")
            with col4:
                st.metric("Min", f"{df_simplified['Rating_Simplified'].min()}")
            
            # Statistiche aggiuntive
            great_movies = len(df_valid[df_valid['Rating_Clean'] >= 7.5])
            great_percentage = (great_movies / len(df_valid)) * 100
            
            st.markdown(f"""
            <div class="stats-card">
                <h4>Great Movies (7.5+)</h4>
                <h3>{great_movies} film ({great_percentage:.1f}%)</h3>
                <p>Film totali con rating: {len(df_valid)}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        df_timeline = df[df['Watch_Date'].notna()]
        
        if len(df_timeline) > 0:
            # Attività mensile
            df_timeline['Year_Month'] = df_timeline['Watch_Date'].dt.to_period('M')
            monthly_activity = df_timeline.groupby('Year_Month').size()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            monthly_activity.plot(kind='line', ax=ax, color='steelblue', marker='o')
            ax.set_title('Attività Cinematografica nel Tempo')
            ax.set_xlabel('Mese')
            ax.set_ylabel('Film Visti')
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            # Statistiche temporali
            st.subheader("Statistiche Temporali")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Primo Film", df_timeline['Watch_Date'].min().strftime('%d/%m/%Y'))
            with col2:
                st.metric("Ultimo Film", df_timeline['Watch_Date'].max().strftime('%d/%m/%Y'))
            with col3:
                days_span = (df_timeline['Watch_Date'].max() - df_timeline['Watch_Date'].min()).days
                st.metric("Giorni di Attività", f"{days_span:,}")

def show_temporal_analysis(df):
    """Analisi temporale basata sulle date di visione (Watch_Date)"""
    st.header("Analisi Temporale (per anno di visione)")

    # Filtra solo film con data di visione
    df_watched = df[df['Watch_Date'].notna()].copy()

    if df_watched.empty:
        st.info("Nessuna 'Watched Date' disponibile nel database.")
        return

    df_watched['Watch_Year'] = df_watched['Watch_Date'].dt.year
    df_watched['Watch_Month'] = df_watched['Watch_Date'].dt.month

    # Usa solo lungometraggi per i conteggi per anno
    df_watched_features = df_watched[df_watched['Duration_Clean'] >= 40]

    tab1, tab2 = st.tabs(["Per Anno di Visione", "Tendenze (anni di visione)"])

    with tab1:
        years_available = sorted(df_watched['Watch_Year'].unique(), reverse=True)
        selected_year = st.selectbox("Scegli anno di visione:", years_available)

        year_films = df_watched[df_watched['Watch_Year'] == selected_year]
        year_films_rated = year_films[year_films['Rating_Clean'].notna()]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Film visti", len(year_films))
        with col2:
            avg_rating = year_films_rated['Rating_Clean'].mean() if len(year_films_rated) > 0 else 0
            st.metric("Rating medio", f"{avg_rating:.2f}")
        with col3:
            great_movies = len(year_films_rated[year_films_rated['Rating_Clean'] >= 7.5])
            st.metric("Great Movies", great_movies)
        with col4:
            if len(year_films_rated) > 0:
                best_film = year_films_rated.loc[year_films_rated['Rating_Clean'].idxmax()]
                st.metric("Miglior Film", f"{best_film['Rating_Clean']:.1f}/10")
            else:
                st.metric("Miglior Film", "N/A")

        # Distribuzione mensile
        st.subheader(f"Distribuzione mensile {selected_year}")
        monthly_counts = year_films.groupby('Watch_Month').size()
        if not monthly_counts.empty:
            months_labels = {1:"Gen",2:"Feb",3:"Mar",4:"Apr",5:"Mag",6:"Giu",7:"Lug",8:"Ago",9:"Set",10:"Ott",11:"Nov",12:"Dic"}
            fig, ax = plt.subplots(figsize=(10,4))
            monthly_counts.reindex(range(1,13), fill_value=0).plot(kind='bar', color='#FF6B6B', ax=ax)
            ax.set_xticks(range(0,12))
            ax.set_xticklabels([months_labels[m] for m in range(1,13)], rotation=0)
            ax.set_ylabel("Film")
            ax.set_xlabel("Mese")  # ← cambiato (rimosso 'Watch_Month')
            ax.set_title(f"Film visti per mese - {selected_year}")
            st.pyplot(fig)

            peak_month = monthly_counts.idxmax()
            st.info(f"Mese più attivo: {months_labels[peak_month]} ({monthly_counts[peak_month]} film)")

        # Top film per rating (solo con rating)
        st.subheader(f"Migliori film visti nel {selected_year} (max 30)")
        year_films_rated_sorted = year_films_rated.sort_values(
            ['Rating_Clean', 'Watch_Date'], ascending=[False, True]
        ).head(30)
        if len(year_films_rated_sorted) == 0:
            st.info("Nessun film con rating per questo anno di visione.")
        else:
            for i, (_, film) in enumerate(year_films_rated_sorted.iterrows(), 1):
                rating = film['Rating_Clean']
                watch_date = film['Watch_Date'].strftime('%d/%m/%Y')
                year_out = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                style = "font-weight:bold;color: var(--accent);" if rating >= 7.5 else ""
                st.markdown(f"""
                <div class="film-card">
                    <span style="{style}">{i}. {film['Name']}</span>{year_out}<br>
                    <small>Regia: {film.get('Director', 'Sconosciuto')} | Rating: {rating:.1f}/10 | Data: {watch_date}</small>
                </div>""", unsafe_allow_html=True)
            if len(year_films_rated) > 30:
                st.info(f"Mostrati 30 di {len(year_films_rated)} film con rating.")

    with tab2:
        st.subheader("Tendenze annuali (anni di visione)")
        # Aggregazioni per anno di visione (solo lungometraggi)
        yearly_stats = df_watched_features.groupby('Watch_Year').agg(
            film=('Name','count'),
            rated=('Rating_Clean', lambda s: s.notna().sum()),
            avg_rating=('Rating_Clean','mean'),
            great=('Rating_Clean', lambda s: (s >= 7.5).sum())
        ).sort_index()

        colA, colB = st.columns(2)
        with colA:
            fig1, ax1 = plt.subplots(figsize=(6,4))
            ax1.plot(yearly_stats.index, yearly_stats['film'], marker='o', color='#1d4ed8')
            ax1.set_title("Film visti per anno (visione) – solo lungometraggi")
            ax1.set_xlabel("Anno")
            ax1.set_ylabel("Film")
            ax1.grid(alpha=0.3)
            st.pyplot(fig1)
        with colB:
            fig2, ax2 = plt.subplots(figsize=(6,4))
            ax2.plot(yearly_stats.index, yearly_stats['avg_rating'], marker='o', color='#dc2626')
            ax2.set_title("Rating medio per anno di visione – solo lungometraggi")
            ax2.set_xlabel("Anno")
            ax2.set_ylabel("Rating medio")
            ax2.set_ylim(0,10)
            ax2.grid(alpha=0.3)
            st.pyplot(fig2)

        # Cards annuali (solo lungometraggi)
        for year in yearly_stats.index[::-1]:
            row = yearly_stats.loc[year]
            great_pct = (row['great']/row['rated']*100) if row['rated'] else 0
            st.markdown(f"""
            <div class="film-card">
                <strong>{int(year)}</strong><br>
                <small>Film: {int(row['film'])} | Rating medio: {row['avg_rating']:.2f}/10 | Great: {int(row['great'])} ({great_pct:.1f}%)</small>
            </div>
            """, unsafe_allow_html=True)

# --- TMDb helpers (safe key, cached calls) ---
def _get_secret(key: str, default=None):
    try:
        return st.secrets[key]
    except Exception:
        return default

def get_tmdb_api_key():
    # NEW: prefer a session override set from the UI form
    override = st.session_state.get("TMDB_API_KEY_OVERRIDE")
    if override:
        return override
    return _get_secret("TMDB_API_KEY", os.environ.get("TMDB_API_KEY"))

@st.cache_data(ttl=60*60*24)
def tmdb_search_movie(api_key: str, title: str, year: Optional[int]):
    if not requests:
        return None, "missing_requests"
    try:
        def _call(params: dict):
            return requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=10)

        def _best_match(results: list):
            if not results:
                return None
            # score by year match and title similarity
            best = None
            best_score = -1
            norm_title = (title or "").strip().lower()
            for it in results:
                score = 0
                rd = (it.get("release_date") or "")
                try:
                    rd_year = int(rd[:4]) if len(rd) >= 4 else None
                except Exception:
                    rd_year = None
                if year and rd_year and int(year) == rd_year:
                    score += 5
                t1 = (it.get("title") or "").strip().lower()
                t2 = (it.get("original_title") or "").strip().lower()
                if t1 == norm_title or t2 == norm_title:
                    score += 4
                if norm_title and (norm_title in t1 or norm_title in t2):
                    score += 2
                if it.get("popularity"):
                    score += float(it.get("popularity")) * 0.01
                if score > best_score:
                    best_score = score
                    best = it
            return best

        # try IT with year
        params = {"api_key": api_key, "query": title, "include_adult": False, "language": "it-IT"}
        if pd.notna(year):
            params["year"] = int(year)
        r = _call(params)
        if r.status_code == 200:
            data = r.json(); res = data.get("results", [])
            hit = _best_match(res)
            if hit:
                return hit, None
        # try IT without year
        params.pop("year", None)
        r = _call(params)
        if r.status_code == 200:
            data = r.json(); res = data.get("results", [])
            hit = _best_match(res)
            if hit:
                return hit, None
        # try EN with year
        params_en = {"api_key": api_key, "query": title, "include_adult": False, "language": "en-US"}
        if pd.notna(year):
            params_en["year"] = int(year)
        r = _call(params_en)
        if r.status_code == 200:
            data = r.json(); res = data.get("results", [])
            hit = _best_match(res)
            if hit:
                return hit, None
        # try EN without year
        params_en.pop("year", None)
        r = _call(params_en)
        if r.status_code == 200:
            data = r.json(); res = data.get("results", [])
            hit = _best_match(res)
            if hit:
                return hit, None
        return None, f"http_{r.status_code}" if r.status_code != 200 else None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=60*60*24)
def tmdb_movie_details(api_key: str, tmdb_id: int):
    if not requests:
        return None, "missing_requests"
    try:
        # request only needed data; use en-US so genre names are in English
        params = {"api_key": api_key, "language": "en-US", "append_to_response": "external_ids,alternative_titles"}
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}", params=params, timeout=10)
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        return r.json(), None
    except Exception as e:
        return None, str(e)

def _enrich_row_with_tmdb(api_key: str, row: pd.Series):
    title = str(row.get("Name", "")).strip()
    year = row.get("Year_Clean", None)
    if not title:
        return {}
    hit, err = tmdb_search_movie(api_key, title, year if pd.notna(year) else None)
    if err or not hit:
        return {}
    details, derr = tmdb_movie_details(api_key, hit.get("id"))
    if derr or not details:
        return {}

    # Genres (English names via en-US)
    genres = ", ".join([g.get("name", "") for g in details.get("genres", []) if g.get("name")])

    # Countries (English names)
    countries = ", ".join([c.get("name", "") for c in details.get("production_countries", []) if c.get("name")])

    # Spoken languages (prefer English name)
    def _lang_name(l):
        return l.get("english_name") or l.get("name") or l.get("iso_639_1") or ""
    languages = ", ".join([_lang_name(l) for l in details.get("spoken_languages", []) if _lang_name(l)])

    tmdb_id = details.get("id")
    tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None

    # Alternative titles (Title (CC)) limited to first 10
    alt_raw = (details.get("alternative_titles") or {}).get("titles", [])
    alt_list = []
    for t in alt_raw:
        tt = t.get("title")
        cc = t.get("iso_3166_1")
        if tt:
            alt_list.append(f"{tt} ({cc})" if cc else tt)
    alternative_titles = ", ".join(alt_list[:10]) if alt_list else None

    return {
        "TMDB_ID": tmdb_id,
        "TMDB_URL": tmdb_url,
        "TMDB_Genres": genres,
        "TMDB_Production_Countries": countries,
        "TMDB_Spoken_Languages": languages,
        "TMDB_Alternative_Titles": alternative_titles,
    }

TMDB_ENRICH_COLS = [
    "TMDB_ID",
    "TMDB_URL",
    "TMDB_Genres",
    "TMDB_Production_Countries",
    "TMDB_Spoken_Languages",
    "TMDB_Alternative_Titles",
]

def load_detailed_database(path: str = "cosimo-film-visti-detailed.csv") -> pd.DataFrame:
    if os.path.exists(path):
        try:
            return pd.read_csv(path, sep=";", encoding="utf-8")
        except Exception:
            try:
                return pd.read_csv(path)
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()

def save_detailed_database(df: pd.DataFrame, path: str = "cosimo-film-visti-detailed.csv"):
    # write with ; to match original style, utf-8 for extended chars
    df.to_csv(path, index=False, sep=";", encoding="utf-8")

# =====================================
# TMDb METADATA (new section)
# =====================================
def show_tmdb_metadata(df: pd.DataFrame):
    st.header("Metadati TMDb")
    api_key = get_tmdb_api_key()
    if not api_key:
        st.error("TMDb API key non configurata.")
        st.info("Imposta una chiave in .streamlit/secrets.toml (TMDB_API_KEY = \"...\") oppure come variabile d'ambiente TMDB_API_KEY.")
        if not requests:
            st.warning("Manca la libreria 'requests'. Installa con: pip install requests")

        # NEW: inline form to use a key only for this session
        with st.form("tmdb_key_form"):
            tmp_key = st.text_input("Inserisci TMDb API key (solo per questa sessione)", type="password")
            submitted = st.form_submit_button("Usa per questa sessione")
        if submitted and tmp_key.strip():
            st.session_state["TMDB_API_KEY_OVERRIDE"] = tmp_key.strip()
            st.success("Chiave TMDb impostata per questa sessione. Ricarico la pagina...")
            st.rerun()
        return

    st.write("Il database originale resterà intatto. Verrà creato/aggiornato un file arricchito: cosimo-film-visti-detailed.csv")
    detailed_df = load_detailed_database()
    st.write(f"Righe nel database arricchito: {len(detailed_df)}")

    # Info: quali campi aggiungiamo
    with st.expander("Quali campi TMDb vengono aggiunti?"):
        st.write(", ".join(TMDB_ENRICH_COLS))

    # Define a row key to match originals with enriched
    def row_key(s: pd.Series):
        y = int(s["Year_Clean"]) if pd.notna(s.get("Year_Clean")) else None
        return f'{str(s.get("Name","")).strip().lower()}|{y}'

    base = df.copy()
    base["_key"] = base.apply(row_key, axis=1)
    enriched = detailed_df.copy()
    if not enriched.empty:
        if "_key" not in enriched.columns:
            # backfill keys for existing enriched file if absent
            enriched["_key"] = enriched.apply(
                lambda s: f'{str(s.get("Name","")).strip().lower()}|{int(s["Year_Clean"]) if pd.notna(s.get("Year_Clean")) else None}', axis=1
            )

    only_missing = st.checkbox("Arricchisci solo elementi mancanti", value=True)
    max_rows = st.number_input("Limite righe da elaborare", min_value=1, max_value=1000, value=50, step=1)
    do_enrich = st.button("Arricchisci ora")

    if do_enrich:
        if enriched.empty:
            merged = base.copy()
        else:
            # inner join to carry over existing enrichment; left join to keep all base
            merged = base.merge(enriched.drop_duplicates("_key"), on="_key", how="left", suffixes=("", "_OLD"))

        # Determine rows to process
        if only_missing:
            to_process_mask = merged["TMDB_ID"].isna() if "TMDB_ID" in merged.columns else pd.Series([True]*len(merged))
        else:
            to_process_mask = pd.Series([True]*len(merged))
        to_process_idx = merged[to_process_mask].index.tolist()[: int(max_rows)]

        progress = st.progress(0)
        status = st.empty()
        updated_rows = 0

        for i, idx in enumerate(to_process_idx, start=1):
            row = merged.loc[idx]
            payload = _enrich_row_with_tmdb(api_key, row)
            if payload:
                # attach payload into row
                for k, v in payload.items():
                    merged.at[idx, k] = v
                updated_rows += 1
            progress.progress(int(i*100/len(to_process_idx)))
            status.write(f"Elaborazione {i}/{len(to_process_idx)}")

            # small pause to be gentle with API limits
            time.sleep(0.10)

        # Persist enriched file: keep original columns + enrichment
        # Rebuild a clean output df: merge base with enriched columns
        enrich_cols_present = [c for c in TMDB_ENRICH_COLS if c in merged.columns]
        output_cols = [c for c in base.columns if c != "_key"] + ["_key"] + enrich_cols_present
        out_df = merged[output_cols].copy()
        save_detailed_database(out_df)
        st.success(f"Aggiornamento completato. Righe aggiornate: {updated_rows}. File: cosimo-film-visti-detailed.csv")

        # NEW: show which columns are newly added and refresh preview
        base_cols_set = set(df.columns) | {"_key"}
        new_cols = [c for c in out_df.columns if c not in base_cols_set]
        if new_cols:
            st.info(f"Colonne TMDb presenti nel file arricchito: {', '.join(new_cols)}")
        # refresh preview with current result
        detailed_df = out_df

        # Optional: preview only TMDb columns
        show_only_tmdb = st.checkbox("Mostra solo colonne TMDb nella preview", value=True)
        preview_cols = (["Name","Year_Clean"] + new_cols) if show_only_tmdb else list(detailed_df.columns)
        st.dataframe(detailed_df.tail(10)[preview_cols], use_container_width=True)

    # Preview both
    with st.expander("Anteprima database originale (prime 10 righe)"):
        st.dataframe(df.head(10), use_container_width=True)
    with st.expander("Anteprima database arricchito (prime 10 righe)"):
        st.dataframe(detailed_df.head(10) if not detailed_df.empty else pd.DataFrame(), use_container_width=True)

# =====================================
# ADD FILM FEATURE
# =====================================
CSV_BASE_FILE = 'cosimo-film-visti-excel.csv'

from math import floor
import io

def _simplify_rating_10(r10: float) -> float:
    if r10 is None or pd.isna(r10):
        return None
    half = r10 / 2.0
    # floor to nearest 0.5
    return floor(half * 2) / 2.0

def _fmt_simplified(val: float) -> str:
    if val is None or pd.isna(val):
        return ""
    if val.is_integer():
        return str(int(val))
    # use comma as in existing CSV
    return str(val).replace('.', ',')

def _append_film_row(row_dict: dict):
    # Ensure order matches existing header
    header = ["Name","Year","Rating","Rating 10","Duration","Director","Watched Date","Tag Diario","Greatness","Top"]
    file_exists = os.path.exists(CSV_BASE_FILE)
    if not file_exists:
        # create with header
        with open(CSV_BASE_FILE, 'w', encoding='cp1252', newline='') as f:
            f.write(';'.join(header) + '\n')
    # sanitize / replace None with empty
    values = []
    for h in header:
        v = row_dict.get(h, "")
        if v is None:
            v = ""
        # convert to str and ensure no stray semicolons
        vs = str(v).replace('\n',' ').replace('\r',' ').replace(';', ',')
        values.append(vs)
    line = ';'.join(values) + '\n'
    with open(CSV_BASE_FILE, 'a', encoding='cp1252', newline='') as f:
        f.write(line)

def show_add_film():
    st.header("Aggiungi Film")

    tab_manual, tab_bulk = st.tabs(["Manuale", "Importa in blocco"])

    with tab_bulk:
        st.subheader("Importa da CSV/Excel")
        st.caption("Formato atteso colonne: Name, Year, Rating 10, Duration, Director, Watched Date, Tag Diario. Rating verrà calcolato automaticamente come metà di Rating 10 (floor a 0.5).")

        # Template download
        template_cols = ["Name","Year","Rating 10","Duration","Director","Watched Date","Tag Diario"]
        tmpl_df = pd.DataFrame(columns=template_cols)
        csv_buf = io.StringIO()
        tmpl_df.to_csv(csv_buf, sep=';', index=False, encoding='cp1252')
        st.download_button("Scarica template CSV", data=csv_buf.getvalue().encode('cp1252', errors='ignore'), file_name="template-film.csv", mime="text/csv")

        uploaded = st.file_uploader("Carica file (CSV o Excel)", type=["csv","xlsx"], accept_multiple_files=False)
        dup_policy = st.radio("Gestione duplicati (Titolo + Anno)", ["Salta", "Sovrascrivi", "Permetti duplicati"], index=0, horizontal=True)
        do_enrich = st.checkbox("Arricchisci con TMDb dopo l'import", value=False)
        enrich_limit = st.number_input("Limite arricchimenti TMDb (per evitare tempi lunghi)", min_value=1, max_value=500, value=50, step=1)

        def _read_upload(file):
            name = file.name.lower()
            if name.endswith('.xlsx'):
                try:
                    return pd.read_excel(file)
                except Exception as e:
                    st.error(f"Errore lettura Excel: {e}")
                    return None
            else:
                # try detect delimiter ; vs ,
                try:
                    content = file.read()
                    # keep a copy for pandas
                    data_copy = io.BytesIO(content)
                    text = content.decode('cp1252', errors='ignore')
                    sep = ';' if text.count(';') >= text.count(',') else ','
                    df_ = pd.read_csv(io.StringIO(text), sep=sep)
                    # reset pointer
                    file.seek(0)
                    return df_
                except Exception as e:
                    st.error(f"Errore lettura CSV: {e}")
                    return None

        def _normalize_cols(df_in: pd.DataFrame) -> pd.DataFrame:
            df = df_in.copy()
            # normalize headers
            colmap = {}
            for c in df.columns:
                cl = c.strip().lower()
                if cl in ("name","titolo"):
                    colmap[c] = "Name"
                elif cl in ("year","anno"):
                    colmap[c] = "Year"
                elif cl in ("rating 10","rating10","voto 10","voto10"):
                    colmap[c] = "Rating 10"
                elif cl in ("duration","durata","minutes","minuti"):
                    colmap[c] = "Duration"
                elif cl in ("director","regista"):
                    colmap[c] = "Director"
                elif cl in ("watched date","data visione","watch date","viewed date"):
                    colmap[c] = "Watched Date"
                elif cl in ("tag diario","tag","diario"):
                    colmap[c] = "Tag Diario"
            if colmap:
                df = df.rename(columns=colmap)
            # keep only known columns
            for col in template_cols:
                if col not in df.columns:
                    df[col] = None
            return df[template_cols]

        def _prepare_rows(df_raw: pd.DataFrame) -> pd.DataFrame:
            df = _normalize_cols(df_raw)
            # parse types
            df['Name'] = df['Name'].astype(str).str.strip()
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
            # Rating 10 parse both comma/dot
            r10 = pd.to_numeric(df['Rating 10'].astype(str).str.replace(',', '.'), errors='coerce')
            # compute simplified Rating
            def _simp(x):
                if pd.isna(x):
                    return None
                return floor((x/2.0)*2)/2.0
            simplified = r10.apply(_simp)
            # Duration
            df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce').astype('Int64')
            df['Director'] = df['Director'].astype(str).fillna('').str.strip()
            # Dates
            dt = pd.to_datetime(df['Watched Date'], dayfirst=True, errors='coerce')
            df['Watched Date'] = dt.dt.strftime('%d/%m/%Y')
            df['Tag Diario'] = df['Tag Diario'].astype(str).fillna('').str.strip()
            # Greatness
            df['Greatness'] = ((r10 >= 7.5).astype(int)).fillna(0)
            # Rating as string with comma
            def _fmt(v):
                if v is None or pd.isna(v):
                    return ""
                if float(v).is_integer():
                    return str(int(v))
                return str(v).replace('.', ',')
            df['Rating'] = simplified.apply(_fmt)
            # Reorder to base columns
            base_cols = ["Name","Year","Rating","Rating 10","Duration","Director","Watched Date","Tag Diario","Greatness","Top"]
            df['Top'] = ""
            # Keep original Rating 10 formatting with comma
            df['Rating 10'] = df['Rating 10'].astype(str).str.replace('.', ',')
            return df[base_cols]

        if uploaded is not None:
            df_up = _read_upload(uploaded)
            if df_up is not None and not df_up.empty:
                prep = _prepare_rows(df_up)
                st.write("Anteprima (prime 20 righe):")
                st.dataframe(prep.head(20), use_container_width=True)
                with st.form("confirm_import_form"):
                    st.write(f"Righe pronte all'import: {len(prep)}")
                    confirmed = st.form_submit_button("Importa ora")
                if confirmed:
                    # Load current base
                    try:
                        base = pd.read_csv(CSV_BASE_FILE, sep=';', encoding='cp1252')
                    except Exception:
                        base = pd.DataFrame(columns=["Name","Year","Rating","Rating 10","Duration","Director","Watched Date","Tag Diario","Greatness","Top"])
                    # Build keys
                    def kbuild(s):
                        y = int(s['Year']) if pd.notna(s['Year']) else None
                        return f"{str(s['Name']).strip().lower()}|{y}"
                    prep['_key'] = prep.apply(kbuild, axis=1)
                    if not base.empty:
                        base['_key'] = base.apply(lambda s: f"{str(s['Name']).strip().lower()}|{int(pd.to_numeric(s['Year'], errors='coerce')) if pd.notna(pd.to_numeric(s['Year'], errors='coerce')) else None}", axis=1)
                    added = 0; updated = 0; skipped = 0
                    if base.empty:
                        out = prep.drop(columns=['_key'])
                        added = len(out)
                    else:
                        if dup_policy == "Permetti duplicati":
                            out = pd.concat([base, prep.drop(columns=['_key'])], ignore_index=True)
                            added = len(prep)
                        elif dup_policy == "Sovrascrivi":
                            # remove existing keys then append new
                            existing_keys = set(base['_key'].tolist())
                            mask_keep = ~base['_key'].isin(prep['_key'])
                            updated = len(prep[prep['_key'].isin(existing_keys)])
                            out = pd.concat([base[mask_keep].drop(columns=['_key']), prep.drop(columns=['_key'])], ignore_index=True)
                            added = len(prep) - updated
                        else:  # Salta
                            existing_keys = set(base['_key'].tolist())
                            to_add = prep[~prep['_key'].isin(existing_keys)].drop(columns=['_key'])
                            skipped = len(prep) - len(to_add)
                            out = pd.concat([base.drop(columns=['_key']), to_add], ignore_index=True)
                            added = len(to_add)
                    try:
                        out.to_csv(CSV_BASE_FILE, sep=';', index=False, encoding='cp1252')
                        load_database.clear()
                        st.success(f"Import completato. Aggiunti: {added}, Aggiornati: {updated}, Saltati: {skipped}")
                    except Exception as e:
                        st.error(f"Errore scrittura CSV base: {e}")
                        st.stop()

                    # Optional enrichment
                    if do_enrich:
                        api_key = get_tmdb_api_key()
                        if not api_key:
                            st.info("TMDb API key non presente. Puoi arricchire in seguito dalla sezione dedicata.")
                        else:
                            # prepare minimal rows to enrich
                            rows_for_enrich = prep.head(int(enrich_limit))
                            enriched_count = 0
                            det = load_detailed_database()
                            if not det.empty and '_key' not in det.columns:
                                det['_key'] = det.apply(lambda s: f"{str(s.get('Name','')).strip().lower()}|{int(s['Year_Clean']) if pd.notna(s.get('Year_Clean')) else None}", axis=1)
                            for _, r in rows_for_enrich.iterrows():
                                ser = pd.Series({'Name': r['Name'], 'Year_Clean': int(r['Year']) if pd.notna(r['Year']) else None})
                                payload = _enrich_row_with_tmdb(api_key, ser)
                                if payload:
                                    new_row = r.to_dict()
                                    new_row['Year_Clean'] = new_row['Year']
                                    new_row['_key'] = f"{str(new_row['Name']).strip().lower()}|{int(new_row['Year']) if pd.notna(new_row['Year']) else None}"
                                    for k,v in payload.items():
                                        new_row[k] = v
                                    if det.empty:
                                        det = pd.DataFrame([new_row])
                                    else:
                                        det = pd.concat([det, pd.DataFrame([new_row])], ignore_index=True)
                                    enriched_count += 1
                                    time.sleep(0.1)
                            try:
                                save_detailed_database(det)
                                st.success(f"Arricchimento TMDb completato per {enriched_count} righe")
                            except Exception as e:
                                st.error(f"Errore salvataggio file arricchito: {e}")

    # Manual tab (existing form)
    with tab_manual:
        st.info("Compila il form per aggiungere un film al database base (CSV). Dopo il salvataggio puoi opzionalmente arricchirlo con TMDb.")
        # Audit existing ratings
        with st.expander("Verifica discrepanze rating esistenti"):
            if st.button("Analizza rating", key="audit_ratings_btn"):
                try:
                    df_a = pd.read_csv(CSV_BASE_FILE, sep=';', encoding='cp1252')
                    # parse numeric
                    r10_num = pd.to_numeric(df_a['Rating 10'].astype(str).str.replace(',', '.'), errors='coerce')
                    simplified_current = pd.to_numeric(df_a['Rating'].astype(str).str.replace(',', '.'), errors='coerce')
                    expected = r10_num.apply(_simplify_rating_10)
                    mismatch_mask = (expected.notna()) & (simplified_current.notna()) & (expected != simplified_current)
                    mismatches = df_a[mismatch_mask].copy()
                    if mismatches.empty:
                        st.success("Nessuna discrepanza trovata.")
                    else:
                        st.warning(f"Discrepanze trovate: {len(mismatches)}")
                        show_cols = ['Name','Year','Rating','Rating 10']
                        mismatches['Expected_Rating'] = expected[mismatch_mask]
                        mismatches['Expected_Rating_Display'] = mismatches['Expected_Rating'].apply(_fmt_simplified)
                        st.dataframe(mismatches[show_cols + ['Expected_Rating_Display']].head(30), use_container_width=True)
                        if st.button("Correggi tutte le discrepanze", key="fix_ratings_btn"):
                            df_a.loc[mismatch_mask, 'Rating'] = expected[mismatch_mask].apply(_fmt_simplified)
                            # rewrite file preserving order
                            df_a.to_csv(CSV_BASE_FILE, sep=';', index=False, encoding='cp1252')
                            load_database.clear()
                            st.success("Rating corretti e file aggiornato.")
                except Exception as e:
                    st.error(f"Errore analisi: {e}")

        with st.form("add_film_form", clear_on_submit=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("Titolo *", "")
                year = st.number_input("Anno", min_value=1888, max_value=2100, value=datetime.now().year, step=1)
                duration = st.number_input("Durata (min)", min_value=1, max_value=1000, value=90, step=1)
            with col2:
                director = st.text_input("Regista", "")
                watched_date = st.date_input("Data visione", value=None, format="DD/MM/YYYY")
                tag_diario = st.text_input("Tag Diario", "")
            with col3:
                rating10 = st.number_input("Rating 10 (0-10)", min_value=0.0, max_value=10.0, value=0.0, step=0.5)
                enrich_now = st.checkbox("Arricchisci subito con TMDb (se chiave disponibile)", value=True)
                allow_duplicate = st.checkbox("Permetti duplicato (stesso titolo+anno)", value=False)
            submitted = st.form_submit_button("Salva Film")

        if submitted:
            if not name.strip():
                st.error("Titolo obbligatorio")
                return
            try:
                current_df = pd.read_csv(CSV_BASE_FILE, sep=';', encoding='cp1252')
            except Exception:
                current_df = pd.DataFrame()
            duplicate = False
            if not current_df.empty and not allow_duplicate:
                duplicate = ((current_df['Name'].astype(str).str.strip().str.lower() == name.strip().lower()) &
                             (pd.to_numeric(current_df['Year'], errors='coerce') == int(year))).any()
            if duplicate:
                st.warning("Film già presente (stesso titolo e anno). Spunta 'Permetti duplicato' per forzare.")
                return
            # compute simplified rating
            simplified = _simplify_rating_10(rating10)
            simplified_str = _fmt_simplified(simplified)
            rating10_str = (str(rating10).replace('.', ','))
            watch_date_str = watched_date.strftime('%d/%m/%Y') if watched_date else ""
            greatness = 1 if rating10 >= 7.5 else 0
            row = {
                "Name": name.strip(),
                "Year": int(year),
                "Rating": simplified_str,
                "Rating 10": rating10_str,
                "Duration": int(duration),
                "Director": director.strip(),
                "Watched Date": watch_date_str,
                "Tag Diario": tag_diario.strip(),
                "Greatness": greatness,
                "Top": "",
            }
            try:
                _append_film_row(row)
                load_database.clear()
                st.success("Film aggiunto al CSV base")
            except Exception as e:
                st.error(f"Errore salvataggio film: {e}")
                return

            # Optional immediate enrichment
            if enrich_now:
                api_key = get_tmdb_api_key()
                if not api_key:
                    st.info("Nessuna TMDb API key disponibile: arricchisci più tardi nella sezione Metadati TMDb.")
                else:
                    # Build minimal Series matching expectations
                    ser = pd.Series({
                        'Name': row['Name'],
                        'Year_Clean': row['Year'],
                    })
                    payload = _enrich_row_with_tmdb(api_key, ser)
                    if payload:
                        # Load / update detailed file
                        detailed = load_detailed_database()
                        base_new = pd.DataFrame([row])
                        # Add computed clean columns to base_new for key building later
                        base_new['Rating 10'] = base_new['Rating 10']
                        base_new['Year_Clean'] = base_new['Year']
                        base_new['_key'] = f"{row['Name'].strip().lower()}|{row['Year']}"
                        for k,v in payload.items():
                            base_new[k] = v
                        if detailed.empty:
                            # start new
                            save_detailed_database(base_new)
                        else:
                            if '_key' not in detailed.columns:
                                detailed['_key'] = detailed.apply(lambda s: f"{str(s.get('Name','')).strip().lower()}|{int(s['Year_Clean']) if pd.notna(s.get('Year_Clean')) else None}", axis=1)
                            updated = pd.concat([detailed, base_new], ignore_index=True)
                            save_detailed_database(updated)
                        st.success("Arricchimento TMDb completato per il film aggiunto")
                    else:
                        st.info("Nessun dato TMDb trovato ora; puoi riprovare in seguito.")

            # Show the row just added
            st.subheader("Anteprima nuova riga")
            st.dataframe(pd.DataFrame([row]), use_container_width=True)