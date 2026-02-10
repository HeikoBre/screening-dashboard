import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Session State
if 'df' not in st.session_state:
    st.session_state.df = None
if 'genes' not in st.session_state:
    st.session_state.genes = []
if 'gene_dict' not in st.session_state:
    st.session_state.gene_dict = {}

st.title('Genomisches Neugeborenenscreening')

# Upload (einmalig)
if st.session_state.df is None:
    uploaded_file = st.file_uploader('CSV hochladen', type='csv')
    if uploaded_file is not None:
        with st.spinner('Lade...'):
            df = pd.read_csv(uploaded_file, sep=',', quotechar='"', encoding='utf-8-sig', low_memory=False)
            st.session_state.df = df
            
            # Gene + Erkrankungen
            gene_dict = {}
            for col in df.columns:
                if 'Gen: ' in col and 'Erkrankung: ' in col and 'nationalen' in col and '[Kommentar]' not in col:
                    gene = col.split('Gen: ')[1].split('  Erkrankung:')[0].strip()
                    disease = col.split('Erkrankung: ')[1].split('"')[0].strip()[:30] + '...' if len(col.split('Erkrankung: ')[1].split('"')[0]) > 30 else col.split('Erkrankung: ')[1].split('"')[0].strip()
                    gene_dict[gene] = disease
            st.session_state.genes = list(gene_dict.keys())
            st.session_state.gene_dict = gene_dict
            
        st.success(f'Geladen: {len(st.session_state.genes)} Gene')
        st.rerun()
else:
    if st.sidebar.button('Neue CSV', type='secondary'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Tabs
if st.session_state.df is not None:
    df = st.session_state.df
    tab_labels = [f"{gene} - {st.session_state.gene_dict.get(gene, '')}" for gene in st.session_state.genes]
    tabs = st.tabs(tab_labels)
    
    for tab_idx, tab in enumerate(tabs):
        with tab:
            gene = st.session_state.genes[tab_idx]
            disease_short = st.session_state.gene_dict[gene]
            
            st.markdown(f"### {gene} ({disease_short})")
            
            # Spalten finden
            nat_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
            nat_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' in col]
            stud_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
            stud_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' in col]

            # Columns für Alignment
            left_col, right_col = st.columns(2)
            
            with left_col:
                st.markdown("#### Nationales Screening")
                nat_data = df[nat_q_cols].stack().dropna()
                nat_data = nat_data[nat_data.isin(['Ja', 'Nein'])]
                ja_nat_pct = (nat_data == 'Ja').mean() * 100 if len(nat_data) > 0 else 0
                total_nat = len(nat_data)
                
                fig_nat = go.Figure(go.Bar(x=[''], y=[ja_nat_pct], 
                                           text=f'{ja_nat_pct:.1f}% (n={total_nat})',
                                           textposition='inside', textfont_size=14, showlegend=False,
                                           marker_color=['green' if ja_nat_pct >= 80 else 'orange']))
                fig_nat.update_layout(height=250, margin=dict(b=0,t=0,l=0,r=0), yaxis_range=[0,100])
                st.plotly_chart(fig_nat, use_container_width=True, key=f'nat_chart_{gene}_{tab_idx}')  # Unique key!
                
                st.caption(f'Zustimmung: {"✅ ≥80%" if ja_nat_pct >= 80 else "❌ <80%"}')

            with right_col:
                st.markdown("#### Wissenschaftliche Studie")
                stud_data = df[stud_q_cols].stack().dropna()
                stud_data = stud_data[stud_data.isin(['Ja', 'Nein'])]
                ja_stud_pct = (stud_data == 'Ja').mean() * 100 if len(stud_data) > 0 else 0
                total_stud = len(stud_data)
                
                fig_stud = go.Figure(go.Bar(x=[''], y=[ja_stud_pct], 
                                            text=f'{ja_stud_pct:.1f}% (n={total_stud})',
                                            textposition='inside', textfont_size=14, showlegend=False,
                                            marker_color=['blue' if ja_stud_pct >= 80 else 'lightblue']))
                fig_stud.update_layout(height=250, margin=dict(b=0,t=0,l=0,r=0), yaxis_range=[0,100])
                st.plotly_chart(fig_stud, use_container_width=True, key=f'stud_chart_{gene}_{tab_idx}')  # Unique key!
                
                st.caption(f'Zustimmung: {"✅ ≥80%" if ja_stud_pct >= 80 else "❌ <80%"}')

            # Kommentare
            st.markdown("#### Kommentare")
            nat_comments = [c for c in df[nat_kom_cols].stack().dropna() if str(c).strip()]
            stud_comments = [c for c in df[stud_kom_cols].stack().dropna() if str(c).strip()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**National:**")
                if nat_comments:
                    for c in nat_comments[:5]:
                        st.write(f"• {c}")
                else:
                    st.write("Keine")
            with col2:
                st.markdown("**Studie:**")
                if stud_comments:
                    for c in stud_comments[:5]:
                        st.write(f"• {c}")
                else:
                    st.write("Keine")
