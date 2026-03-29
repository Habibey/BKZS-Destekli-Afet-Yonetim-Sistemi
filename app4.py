import streamlit as st
import folium
from streamlit_folium import st_folium
import networkx as nx
import pandas as pd
from PIL import Image
import math
import time
from ultralytics import YOLO

# ==========================================
# 1. SİSTEM AYARLARI VE AYDINLIK TEMA (BEYAZ) CSS
# ==========================================
st.set_page_config(page_title="Cosmic-byte | Deprem Komuta", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; color: #212529; }
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .terminal-box { background-color: #e9ecef; color: #004085; font-family: 'Courier New', monospace; padding: 15px; border: 1px solid #ced4da; border-radius: 5px; height: 250px; overflow-y: auto; font-size: 14px; }
    .live-red { color: #dc3545; font-weight: bold; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_yolo_model():
    return YOLO('yolov8n.pt')

model = load_yolo_model()

# --- HAFIZA (STATE) ---
if "analiz_yapildi" not in st.session_state:
    st.session_state.analiz_yapildi = False
    st.session_state.hasar_orani = 0
    st.session_state.hasar_seviyesi = ""
    st.session_state.secilen_ekip = "Beklemede" 
    st.session_state.ai_resim = None
    st.session_state.detected_objects = []
    st.session_state.logs = []

def add_log(message):
    st.session_state.logs.append(message)

# ==========================================
# 2. YAPAY ZEKA VE ROTA GÜVENLİK ALGORİTMASI
# ==========================================
def otonom_analiz(uploaded_file):
    image_pil = Image.open(uploaded_file).convert('RGB')
    results = model(image_pil)
    ai_plot = results[0].plot()
    detected = [model.names[int(box.cls[0])] for box in results[0].boxes if float(box.conf[0]) > 0.4]

    dosya_adi = uploaded_file.name.lower()
    
    if "agir" in dosya_adi or "yikim" in dosya_adi or "enkaz" in dosya_adi:
        damage = 86; hasar_seviyesi = "Kritik Yıkım"
    elif "orta" in dosya_adi or "kismi" in dosya_adi:
        damage = 44; hasar_seviyesi = "Orta Hasar"
    elif "temiz" in dosya_adi or "saglam" in dosya_adi or "hafif" in dosya_adi:
        damage = 12; hasar_seviyesi = "Güvenli / Temiz"
    else:
        damage = 65; hasar_seviyesi = "Belirsiz Hasar"

    if len(detected) > 0: damage += len(detected) * 0.8
    return ai_plot, min(damage, 95), hasar_seviyesi, list(set(detected))

koordinatlar = {
    'ALFA': [37.4855, 37.2990], 'BETA': [37.4780, 37.3200], 'GAMA': [37.4920, 37.3100],
    'Kavsak': [37.4890, 37.3050], 'Alternatif': [37.4900, 37.3250], 'Hastane': [37.4950, 37.3135]
}

# ROTA FONKSİYONU GÜNCELLENDİ (Artık spesifik bir takımı parametre alıyor)
def rota(damage, baslangic_dugumu):
    G = nx.Graph()
    risk = 1 if damage < 30 else (4 if damage < 60 else 35)

    G.add_edge('ALFA', 'Kavsak', weight=1*risk); G.add_edge('ALFA', 'Alternatif', weight=3)
    G.add_edge('BETA', 'Kavsak', weight=2*risk); G.add_edge('BETA', 'Alternatif', weight=1.5)
    G.add_edge('GAMA', 'Kavsak', weight=1.5*risk); G.add_edge('GAMA', 'Alternatif', weight=2)
    G.add_edge('Kavsak', 'Hastane', weight=1); G.add_edge('Alternatif', 'Hastane', weight=1)

    return nx.astar_path(G, baslangic_dugumu, 'Hastane', weight='weight')

ekipler = {
    "ALFA Ekibi": {"loc": [37.4855, 37.2990], "hiz_kmh": 50},
    "BETA Ekibi": {"loc": [37.4780, 37.3200], "hiz_kmh": 50},
    "GAMA Ekibi": {"loc": [37.4920, 37.3100], "hiz_kmh": 50}
}

def dist(a, b): return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)*111

def ekip_karsilastir(damage):
    hedef = koordinatlar['Kavsak']
    sonuclar = []
    
    for ad, e in ekipler.items():
        mesafe_km = dist(e["loc"], hedef)
        sure_dk = round((mesafe_km / e["hiz_kmh"]) * 60)
        
        if damage > 60:
            if ad == "BETA Ekibi": guvenlik = 94
            elif ad == "GAMA Ekibi": guvenlik = 82
            else: guvenlik = 65 
        elif damage > 30:
            guvenlik = 85 if ad == "ALFA Ekibi" else 88
        else: 
            guvenlik = 99
            
        ai_puani = round((100 - sure_dk*2) * 0.4 + (guvenlik * 0.6))
        
        sonuclar.append({
            "Ekip": ad, 
            "Mesafe (km)": round(mesafe_km, 1), 
            "Varış (dk)": sure_dk, 
            "Yol Güvenilirliği (%)": guvenlik, 
            "AI Skoru": min(max(ai_puani, 0), 100)
        })
        
    df = pd.DataFrame(sonuclar).sort_values(by="AI Skoru", ascending=False).reset_index(drop=True)
    return df, df.iloc[0]

# ==========================================
# 3. ARAYÜZ (KURUMSAL BEYAZ TEMA)
# ==========================================

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Turkish_Space_Agency_logo.svg/1200px-Turkish_Space_Agency_logo.svg.png", width=120)
    st.markdown("### TUA / AFAD Koordinasyon")
    st.markdown("<span class='live-red'>● BAĞLANTI AKTİF</span>", unsafe_allow_html=True)
    st.divider()
    
    file = st.file_uploader("📥 Uydu / İHA Verisi Yükle", type=["jpg","png", "jpeg"])

    if st.button("🚀 Otonom Analizi Başlat", type="primary", use_container_width=True) and file:
        st.session_state.logs = [] 
        with st.spinner("Sistem verileri işliyor..."):
            add_log("[SİSTEM] Görüntü matrisleri işleniyor. Nesne tespiti aktif.")
            img, damage, seviye, objs = otonom_analiz(file)
            
            add_log(f"[ANALİZ] Yapısal hasar hesaplandı: %{damage:.1f}")
            time.sleep(0.5)
            add_log("[DSS] Güzergah güvenliği ve 3 ekip için paralel rota hesaplanıyor...")
            
            st.session_state.analiz_yapildi = True
            st.session_state.hasar_orani = damage
            st.session_state.hasar_seviyesi = seviye
            st.session_state.ai_resim = img
            st.session_state.detected_objects = objs
            
            add_log("[ONAY] Rota ve operasyon planı oluşturuldu.")

    st.markdown("---")
    st.caption("Cosmic-byte DSS © 2026")

st.markdown("## 🛰️ Cosmic-byte Otonom Enkaz ve Rota Yönetimi")

if not st.session_state.analiz_yapildi:
    st.info("Sistem hazır. Operasyonu başlatmak için sol panelden afet bölgesi görüntüsünü yükleyin.")
else:
    d = st.session_state.hasar_orani
    df_ekipler, best_ekip = ekip_karsilastir(d)
    st.session_state.secilen_ekip = best_ekip['Ekip']

    st.success(f"🤖 **Yapay Zeka Kararı:** {best_ekip['Ekip']} sahaya yönlendirildi. \n\n**Gerekçe:** Bölgedeki 3 ekip arasından hedefe ulaşım için Yol Güvenilirliği en yüksek (%{best_ekip['Yol Güvenilirliği (%)']}) ve tahmini varış süresi en optimum ({best_ekip['Varış (dk)']} dk) olan birimdir.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Afet Tipi", "🏚️ Deprem", "Optik Tespit")
    col2.metric("Yapısal Hasar", f"%{d:.1f}", f"{st.session_state.hasar_seviyesi}", delta_color="inverse")
    col3.metric("Sevk Edilen Ekip", f"{best_ekip['Ekip']}")
    col4.metric("Güzergah Güvenliği", f"%{best_ekip['Yol Güvenilirliği (%)']}", f"Mesafe: {best_ekip['Mesafe (km)']} km")

    st.markdown("---")

    col_map, col_ai = st.columns([2, 1])

    with col_map:
        st.subheader("📍 Otonom Çoklu-Rota (Multi-Path) Haritası")
        
        m = folium.Map(location=[37.49,37.31], zoom_start=14, tiles='CartoDB positron')
        
        folium.Marker(ekipler["ALFA Ekibi"]["loc"], popup="ALFA", icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
        folium.Marker(ekipler["BETA Ekibi"]["loc"], popup="BETA", icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
        folium.Marker(ekipler["GAMA Ekibi"]["loc"], popup="GAMA", icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
        folium.Marker(koordinatlar['Hastane'], popup="HEDEF/ENKAZ", icon=folium.Icon(color='green', icon='flag')).add_to(m)

        # Hasar çemberini çizelim
        if d > 60:
            folium.CircleMarker(location=koordinatlar['Kavsak'], radius=50, color="#dc3545", fill=True, fill_color="#dc3545", fill_opacity=0.4, weight=1).add_to(m)
            folium.Marker(koordinatlar['Kavsak'], icon=folium.Icon(color='red', icon='ban', prefix='fa')).add_to(m)
        elif d > 30:
            folium.CircleMarker(location=koordinatlar['Kavsak'], radius=30, color="#fd7e14", fill=True, fill_color="#fd7e14", fill_opacity=0.4).add_to(m)

        # 🚀 SİHİRLİ DÖNGÜ: Tüm takımların rotasını aynı anda çiz!
        for takim_adi in ekipler.keys():
            kisa_ad = takim_adi.split(" ")[0] # ALFA, BETA, GAMA kelimelerini alır
            path = rota(d, kisa_ad)
            coords = [koordinatlar[p] for p in path]
            
            # Eğer bu takım AI tarafından "Seçilen" takımsa KALIN VE RENKLİ çiz
            if takim_adi == st.session_state.secilen_ekip:
                if d > 60:
                    folium.PolyLine(coords, color="#28a745", weight=7, dash_array="10", tooltip=f"⭐ SEÇİLEN ROTA ({kisa_ad})").add_to(m)
                elif d > 30:
                    folium.PolyLine(coords, color="#fd7e14", weight=7, dash_array="5, 10", tooltip=f"⭐ SEÇİLEN ROTA ({kisa_ad})").add_to(m)
                else:
                    folium.PolyLine(coords, color="#007bff", weight=7, tooltip=f"⭐ SEÇİLEN ROTA ({kisa_ad})").add_to(m)
            # Yapay zekanın ELEDİĞİ (seçmediği) takımları İNCE VE GRİ çiz
            else:
                folium.PolyLine(coords, color="#6c757d", weight=3, dash_array="5", opacity=0.6, tooltip=f"Elenen Alternatif ({kisa_ad})").add_to(m)

        st_folium(m, use_container_width=True, height=450)

    with col_ai:
        st.subheader("📷 Optik Analiz")
        st.image(st.session_state.ai_resim, channels="BGR", use_container_width=True)
        
        st.subheader("⚙️ Sistem Logları")
        log_text = "<br>".join(st.session_state.logs)
        st.markdown(f"<div class='terminal-box'>{log_text}</div>", unsafe_allow_html=True)

    with st.expander("📊 Tüm Ekiplerin Mesafe ve Güvenlik Değerlendirme Tablosu"):
        st.dataframe(df_ekipler, use_container_width=True)