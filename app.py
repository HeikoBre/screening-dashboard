import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# CSV laden (passen Sie den Pfad an, wenn nötig)
@st.cache_data
def load_data():
    df = pd.read_csv('results-survey751417.csv', sep=';', low_memory=False)  # LimeSurvey nutzt oft ;
    return df

df = load_data()

# Gen/Erkrankungen identifizieren (aus Spaltennamen extrahieren)
genes = [col.split('Gen ')[1].split(' Erkrankung')[0] for col in df.columns if 'Gen ' in col and 'nationalen' in col]
genes = list(set(genes))  # Einzigartig
st.title('Wöchentliches Dashboard: Genomisches Neugeborenenscreening')

# Sidebar für Auswahl
selected_gene = st.sidebar.selectbox('Gen/Erkrankung wählen:', genes)

# Daten für ausgewähltes Gen filtern
nat_cols = [col for col in df.columns if f'Gen {selected_gene}' in col and 'nationalen' in col and 'Kommentar' not in col]
stud_cols = [col for col in df.columns if f'Gen {selected_gene}' in col and 'wissenschaftlicher' in col and 'Kommentar' not in col]
nat_kom = [col for col in df.columns if f'Gen {selected_gene}' in col and 'nationalen' in col and 'Kommentar' in col]
stud_kom = [col for col in df.columns if f'Gen {selected_gene}' in col and 'wissenschaftlicher' in col and 'Kommentar' in col]

if nat_cols and stud_cols:
    # Nationale Screening: Ja-Anteil (ohne Nicht beantwortbar)
    nat_df = df[nat_cols].melt(ignore_index=False).dropna()
    nat_df = nat_df[nat_df['value'].isin(['Ja', 'Nein'])]  # Ignoriere "Ich kann..."
    ja_nat_pct = (nat_df['value'] == 'Ja').mean() * 100 if len(nat_df) > 0 else 0

    # Studien: Ja-Anteil
    stud_df = df[stud_cols].melt(ignore_index=False).dropna()
    stud_df = stud_df[stud_df['value'].isin(['Ja', 'Nein'])]
    ja_stud_pct = (stud_df['value'] == 'Ja').mean() * 100 if len(stud_df) > 0 else 0

    # Balkendiagramm
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Nationales Screening', x=['Ja %'], y=[ja_nat_pct], 
                         marker_color='green' if ja_nat_pct >= 80 else 'orange',
                         text=f'{ja_nat_pct:.1f}%', textposition='auto'))
    fig.add_trace(go.Bar(name='Wiss. Studie', x=['Ja %'], y=[ja_stud_pct], 
                         marker_color='blue' if ja_stud_pct >= 80 else 'lightblue',
                         text=f'{ja_stud_pct:.1f}%', textposition='auto'))
    fig.update_layout(barmode='group', title=f'Zustimmung für {selected_gene}', yaxis_title='Prozentsatz Ja-Antworten')
    st.plotly_chart(fig, use_container_width=True)

    # Schwellenwert-Info
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Nationales Screening', f'{ja_nat_pct:.1f}%', delta='✅ ≥80%' if ja_nat_pct >= 80 else '❌ <80%')
    with col2:
        st.metric('Wiss. Studie', f'{ja_stud_pct:.1f}%', delta='✅ ≥80%' if ja_stud_pct >= 80 else '❌ <80%')

    # Kommentare anzeigen
    st.subheader('Kommentare')
    nat_comments = df[nat_kom].dropna().stack().tolist()
    stud_comments = df[stud_kom].dropna().stack().tolist()
    comments_df = pd.DataFrame({'Kategorie': ['National']*len(nat_comments) + ['Studie']*len(stud_comments),
                                'Kommentar': nat_comments + stud_comments})
    st.dataframe(comments_df, use_container_width=True)

else:
    st.warning(f'Keine Daten für {selected_gene} gefunden.')
