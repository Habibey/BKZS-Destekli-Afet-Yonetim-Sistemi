# Cosmic-byte: Yerli Uydu Destekli Afet Yönetim Sistemi

## Hackathon Projesi: Afet Yönetiminde Yerli Uydu Verisi Entegrasyonu

Bu proje, afet bölgelerinde uydu görüntülerini yapay zeka ile analiz ederek kurtarma ekiplerine en güvenli rotayı öneren bir demo sistemidir.

### Özellikler

- **Uydu Görüntü Analizi**: OpenCV ile change detection kullanarak hasar tespiti
- **AI Nesne Tespiti**: YOLOv8 ile görüntülerde nesne analizi
- **A* Algoritması**: Hasar oranına göre en kısa ve güvenli rota hesaplama
- **Ekip Önerisi**: Mesafe ve kapasiteye göre en uygun ekibin önerilmesi
- **Interaktif Harita**: Folium ile rota görselleştirme

### Kurulum ve Çalıştırma

1. Gerekli paketleri yükleyin:
```bash
pip install streamlit ultralytics opencv-python folium streamlit-folium networkx pillow
```

2. Uygulamayı başlatın:
```bash
streamlit run app.py
```

3. Tarayıcıda açılan sayfada:
   - Afet öncesi ve sonrası uydu görüntülerini yükleyin
   - "Analiz Başlat" butonuna tıklayın
   - Hasar oranını, AI tespitlerini ve rota önerisini görün

### Kullanım

- **Görüntü Yükleme**: PNG/JPG formatında afet öncesi ve sonrası görüntüler
- **Hasar Analizi**: Change detection ile yıkıntı alanları tespit edilir
- **AI Tespiti**: YOLO ile araç, insan gibi nesneler tespit edilir
- **Rota Planlama**: A* algoritması ile güvenli yol hesaplanır
- **Ekip Önerisi**: En yakın ve uygun kapasiteli ekip önerilir

### Teknoloji Stack

- **Frontend**: Streamlit
- **AI/Model**: YOLOv8 (Ultralytics)
- **Görüntü İşleme**: OpenCV
- **Graf Teorisi**: NetworkX
- **Harita**: Folium
- **Dil**: Python

### Demo Senaryosu

Pazarcık/Maraş depremi senaryosu baz alınmıştır. Sistem, uydu verilerini analiz ederek hasar oranını hesaplar ve ekiplere rota önerir.

Bu proje hackathon için geliştirilmiş bir demo olup, gerçek afet yönetim sistemlerinde kullanılabilir.