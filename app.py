import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Globale CSS für kleinere Schrift
st.markdown("""
<style>
.main .block-container {
    font-size: 14px !important;
}
h3 {
    font-size: 18px !important;
}
h4 {
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# Session State (unverändert)
if 'df' not in st.session_state:
    st.session_state.df = None
if 'genes' not in st.session_state:
    st.session_state.genes = []
if 'gene_dict' not in st.session_state:
    st.session_state.gene_dict = {}

st.title('Genomisches Neugeborenenscreening', anchor=False)

# Upload (unverändert)
if st.session_state.df is None:
    uploaded_file = st.file_uploader('CSV hochladen', type='csv')
    if uploaded_file is not None:
        with st.spinner('Lade...'):
            df = pd.read_csv(uploaded_file, sep=',', quotechar='"', encoding='utf-8-sig', low_memory=False)
            st.session_state.df = df
            
            gene_dict = {}
            for col in df.columns:
                if 'Gen: ' in col and 'Erkrankung: ' in col and 'nationalen' in col and '[Kommentar]' not in col:
                    gene = col.split('Gen: ')[1].split('  Erkrankung:')[0].strip()
                    disease = col.split('Erkrankung: ')[1].split('"')[0].strip()
                    gene_dict[gene] = disease[:35] + '...' if len(disease) > 35 else disease
            st.session_state.genes = list(gene_dict.keys())
            st.session_state.gene_dict = gene_dict
            
        st.success(f'Geladen: {len(st.session_state.genes)} Gene')
        st.rerun()
else:
    if st.sidebar.button('Neue CSV', type='secondary'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Tabs (NUR Gen-Namen)
if st.session_state.df is not None:
    df = st.session_state.df
    tabs = st.tabs(st.session_state.genes)  # Nur Gene!
    
    for tab_idx, tab in enumerate(tabs):
        with tab:
            gene = st.session_state.genes[tab_idx]
            disease = st.session_state.gene_dict[gene]
            
            # Kursiv + separate Zeilen, klein
            st.markdown(f"**_{gene}_**", unsafe_allow_html=True)
            st.markdown(f"*{disease}*", unsafe_allow_html=True)
            
            # Spalten finden
            nat_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
            nat_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' in col]
            stud_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
            stud_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' in col]

            # Columns
            left_col, right_col = st.columns(2)
            
            with left_col:
                st.markdown("#### Nationales Screening")
                nat_data = df[nat_q_cols].stack().dropna()
                nat_data = nat_data[nat_data.isin(['Ja', 'Nein'])]
                ja_nat_pct = (nat_data == 'Ja').mean() * 100 if len(nat_data) > 0 else 0
                total_nat = len(nat_data)
                
                fig_nat = go.Figure(go.Bar(x=[''], y=[ja_nat_pct], 
                                           text=f'{ja_nat_pct:.1f}%',
                                           textposition='inside', textfont_size=12, showlegend=False,
                                           marker_color=['#10B981' if ja_nat_pct >= 80 else '#F59E0B']))
                fig_nat.update_layout(height=220, margin=dict(b=0,t=0,l=0,r=0), yaxis_range=[0,100])
                st.plotly_chart(fig_nat, use_container_width=True, key=f'nat_{gene}_{tab_idx}')
                st.caption(f'n={total_nat} | {"✅ ≥80%" if ja_nat_pct >= 80 else "<80%"}')

            with right_col:
                st.markdown("#### Wissenschaftliche Studie")
                stud_data = df[stud_q_cols].stack().dropna()
                stud_data = stud_data[stud_data.isin(['Ja', 'Nein'])]
                ja_stud_pct = (stud_data == 'Ja').mean() * 100 if len(stud_data) > 0 else 0
                total_stud = len(stud_data)
                
                fig_stud = go.Figure(go.Bar(x=[''], y=[ja_stud_pct], 
                                            text=f'{ja_stud_pct:.1f}%',
                                            textposition='inside', textfont_size=12, showlegend=False,
                                            marker_color=['#3B82F6' if ja_stud_pct >= 80 else '#93C5FD']))
                fig_stud.update_layout(height=220, margin=dict(b=0,t=0,l=0,r=0), yaxis_range=[0,100])
                st.plotly_chart(fig_stud, use_container_width=True, key=f'stud_{gene}_{tab_idx}')
                st.caption(f'n={total_stud} | {"✅ ≥80%" if ja_stud_pct >= 80 else "<80%"}')

            # Kommentare (kleiner)
            st.markdown("#### Kommentare")
            nat_comments = [c for c in df[nat_kom_cols].stack().dropna() if str(c).strip()]
            stud_comments = [c for c in df[stud_kom_cols].stack().dropna() if str(c).strip()]
            
            c1, c2 = st.columns(2)
            with c1:
                if nat_comments:
                    st.markdown("**National:**")
                    for c in nat_comments[:3]:
                        st.caption(f"• {c}")
                else:
                    st.caption("Keine")
            with c2:
                if stud_comments:
                    st.markdown("**Studie:**")
                    for c in stud_comments[:3]:
                        st.caption(f"• {c}")
                else:
                    st.caption("Keine")
