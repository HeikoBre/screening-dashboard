import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

st.title('Dashboard: Genomisches Neugeborenenscreening')

# Datei-Upload
uploaded_file = st.file_uploader('CSV hochladen (z.B. results-survey751417.csv)', type='csv')

if uploaded_file is not None:
    # CSV laden (Komma-separiert, UTF-8 BOM ignorieren)
    df = pd.read_csv(uploaded_file, sep=',', quotechar='"', encoding='utf-8-sig', low_memory=False)
    st.success(f'Datei geladen: {len(df)} Antworten, {len(df.columns)} Spalten.')

    # Alle Gene extrahieren (aus Spalten mit "Gen: ")
    gene_list = []
    for col in df.columns:
        if 'Gen: ' in col and 'Erkrankung: ' in col and 'nationalen' in col and '[Kommentar]' not in col:
            gene = col.split('Gen: ')[1].split('  Erkrankung:')[0].strip()
            gene_list.append(gene)
    genes = list(set(gene_list))
    
    if not genes:
        st.warning('Keine Gen-Spalten gefunden. Überprüfen Sie die CSV-Struktur.')
    else:
        selected_gene = st.sidebar.selectbox('Gen/Erkrankung wählen:', genes)

        # Spalten für nationales Screening und Studien finden
        nat_q_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
        nat_kom_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'nationalen' in col and '[Kommentar]' in col]
        stud_q_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
        stud_kom_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' in col]

        if nat_q_cols and stud_q_cols:
            # Nationale Screening: Ja % (nur Ja/Nein)
            nat_data = df[nat_q_cols].stack().dropna()
            nat_data = nat_data[nat_data.isin(['Ja', 'Nein'])]
            ja_nat_pct = (nat_data == 'Ja').mean() * 100 if len(nat_data) > 0 else 0
            total_nat = len(nat_data)

            # Studien: Ja %
            stud_data = df[stud_q_cols].stack().dropna()
            stud_data = stud_data[stud_data.isin(['Ja', 'Nein'])]
            ja_stud_pct = (stud_data == 'Ja').mean() * 100 if len(stud_data) > 0 else 0
            total_stud = len(stud_data)

            # Balkendiagramm
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Nationales Screening', x=[f'{ja_nat_pct:.1f}% (n={total_nat})'], 
                                 y=[ja_nat_pct], marker_color='green' if ja_nat_pct >= 80 else 'orange',
                                 text=f'{ja_nat_pct:.1f}%', textposition='auto'))
            fig.add_trace(go.Bar(name='Wiss. Studie', x=[f'{ja_stud_pct:.1f}% (n={total_stud})'], 
                                 y=[ja_stud_pct], marker_color='blue' if ja_stud_pct >= 80 else 'lightblue',
                                 text=f'{ja_stud_pct:.1f}%', textposition='auto'))
            fig.update_layout(barmode='group', title=f'Zustimmung {selected_gene}', 
                              yaxis=dict(range=[0,100], title='Ja-Prozentsatz'), height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric('Nationales Screening', f'{ja_nat_pct:.1f}%', 
                          '✅ ≥80%' if ja_nat_pct >= 80 else '❌ <80%', delta_color='normal')
            with col2:
                st.metric('Wiss. Studie', f'{ja_stud_pct:.1f}%', 
                          '✅ ≥80%' if ja_stud_pct >= 80 else '❌ <80%', delta_color='normal')

            # Kommentare
            st.subheader('Kommentare')
            nat_comments = df[nat_kom_cols].stack().dropna().tolist()
            stud_comments = df[stud_kom_cols].stack().dropna().tolist()
            if nat_comments or stud_comments:
                comments_df = pd.DataFrame({
                    'Kategorie': ['Nationales Screening'] * len(nat_comments) + ['Wiss. Studie'] * len(stud_comments),
                    'Kommentar': nat_comments + stud_comments
                })
                st.dataframe(comments_df, use_container_width=True, hide_index=True)
            else:
                st.info('Keine Kommentare vorhanden.')
        else:
            st.warning(f'Keine passenden Spalten für {selected_gene} gefunden.')
            
    # Vorschau der Daten
    if st.checkbox('Rohdaten-Vorschau (erste 5 Zeilen)'):
        st.dataframe(df.head(), use_container_width=True)
else:
    st.info('Bitte laden Sie die CSV-Datei hoch.')
