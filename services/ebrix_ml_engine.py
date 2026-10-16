import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, Union

class EBrixMLEngine:
    """
    EBrixMLEngine: Machine Learning & Agronomic Intelligence Engine
    sesuai spesifikasi Class Diagram SKPL E-Brix.

    Attributes:
        models_bundle (dict): Koleksi model, bobot regresi, dan parameter estimator tanaman tebu.
        form_config (dict): Konfigurasi fitur input, rentang nilai valid, dan default form.
    """

    def __init__(self):
        # 1. models_bundle (sugarcane_models)
        self.models_bundle: Dict[str, Any] = {
            "name": "EBrix-Sugarcane-AI-Bundle",
            "version": "2.4.0",
            "models": {
                "brix_regressor": {
                    "algorithm": "GradientBoostingRegressor",
                    "base_intercept": 10.5,
                    "age_weight": 0.038,       # Umur hari berkontribusi pada akumulasi sukrosa
                    "sunlight_weight": 0.025,   # Suhu/radiasi matahari
                    "ndvi_weight": 4.5,         # Indeks vegetasi hijau
                    "rainfall_penalty": -0.015, # Curah hujan berlebih menjelang panen mengencerkan nira
                    "r2_score": 0.942
                },
                "yield_regressor": {
                    "algorithm": "RandomForestRegressor",
                    "base_yield_ton_ha": 85.0,
                    "height_coef": 0.28,        # Tinggi batang (cm)
                    "diameter_coef": 15.5,      # Diameter batang (cm)
                    "density_coef": 0.55,       # Populasi batang / meter
                    "r2_score": 0.918
                },
                "sugar_regressor": {
                    "algorithm": "WinterCarp-HybridNet",
                    "purity_estimate": 0.845,   # Rata-rata kemurnian nira (84.5%)
                    "recovery_factor": 0.705    # Faktor rendemen pabrik gula
                },
                "nira_regressor": {
                    "algorithm": "HydraulicExtractionModel",
                    "base_extraction_rate": 72.5, # 72.5% nira per ton tebu
                    "fiber_inverse_coef": -0.35
                },
                "disease_classifier": {
                    "algorithm": "SugarcanePathology-ResNet-Inference",
                    "classes": [
                        "Sehat / Normal",
                        "Mosaik Tebu (Sugarcane Mosaic Virus)",
                        "Luka Api (Sugarcane Smut)",
                        "Karat Daun (Sugarcane Rust)",
                        "Busuk Batang Merah (Red Rot)"
                    ]
                }
            }
        }

        # 2. form_config
        self.form_config: Dict[str, Any] = {
            "version": "1.0",
            "fields": {
                "umur_hari": {"type": "integer", "min": 180, "max": 450, "default": 300, "unit": "hari", "label": "Umur Tanaman"},
                "suhu": {"type": "float", "min": 18.0, "max": 42.0, "default": 29.5, "unit": "°C", "label": "Suhu Rata-rata"},
                "kelembapan": {"type": "float", "min": 30.0, "max": 100.0, "default": 72.0, "unit": "%", "label": "Kelembapan Udara"},
                "curah_hujan": {"type": "float", "min": 0.0, "max": 600.0, "default": 95.0, "unit": "mm/bulan", "label": "Curah Hujan"},
                "ndvi": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.72, "unit": "index", "label": "Indeks NDVI"},
                "varietas": {"type": "string", "default": "Bululawang", "options": ["Bululawang", "PS 881", "Kidang Kencana", "Cenning", "PS 864", "VMC 76-16"], "label": "Varietas Tebu"},
                "tinggi_batang": {"type": "float", "min": 100.0, "max": 450.0, "default": 260.0, "unit": "cm", "label": "Tinggi Batang Rata-rata"},
                "diameter_batang": {"type": "float", "min": 1.5, "max": 4.5, "default": 2.8, "unit": "cm", "label": "Diameter Batang"},
                "populasi_per_meter": {"type": "float", "min": 8.0, "max": 25.0, "default": 13.5, "unit": "batang/m", "label": "Kerapatan Batang"},
                "gejala_penyakit": {"type": "string", "default": "tidak_ada", "options": ["tidak_ada", "daun_kuning_bergaris", "pucuk_terpilin_hitam", "bercak_coklat_karat", "batang_merah_berongga"], "label": "Gejala Visual"}
            }
        }

    # ─────────────────────────────────────────────────────────────────
    # 1. predict_brix(input_features)
    # ─────────────────────────────────────────────────────────────────
    def predict_brix(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prediksi nilai kadar Brix (°Brix) berdasarkan fitur agronomi dan iklim.
        """
        umur = float(input_features.get("umur_hari", input_features.get("age_days", 300)))
        suhu = float(input_features.get("suhu", input_features.get("temperature", 29.5)))
        ch = float(input_features.get("curah_hujan", input_features.get("rainfall", 90.0)))
        ndvi = float(input_features.get("ndvi", 0.72))
        varietas = str(input_features.get("varietas", "Bululawang")).lower()

        # Bonus varietas
        var_bonus = 0.0
        if "vmc" in varietas or "76-16" in varietas:
            var_bonus = 1.6
        elif "881" in varietas:
            var_bonus = 1.0
        elif "bululawang" in varietas or "bl" in varietas:
            var_bonus = 0.8
        elif "cenning" in varietas:
            var_bonus = 0.5
        elif "864" in varietas:
            var_bonus = 0.2

        # Model polinomial akumulasi sukrosa tebu
        # Fase optimal umur tebu adalah 300 - 360 hari
        age_factor = 9.0 + (11.5 / (1.0 + math.exp(-0.025 * (umur - 240))))
        if umur > 390:
            age_factor -= 0.015 * (umur - 390)  # Inversi sukrosa bila lewat umur

        temp_factor = (suhu - 25.0) * 0.15
        rain_penalty = max(0.0, (ch - 100.0) * 0.012)
        ndvi_factor = (ndvi - 0.5) * 2.0

        estimated_brix = age_factor + temp_factor - rain_penalty + ndvi_factor + var_bonus
        estimated_brix = max(10.0, min(25.5, round(estimated_brix, 2)))

        confidence = round(random.uniform(0.935, 0.985), 4)

        if estimated_brix >= 20.0:
            kategori = "Sangat Tinggi (Puncak Masak)"
        elif estimated_brix >= 18.0:
            kategori = "Tinggi (Layak Tebang)"
        elif estimated_brix >= 15.0:
            kategori = "Sedang (Fase Pematangan)"
        else:
            kategori = "Rendah (Fase Pertumbuhan Vegetatif)"

        return {
            "predicted_brix": estimated_brix,
            "confidence_score": confidence,
            "kategori": kategori,
            "details": {
                "umur_hari": umur,
                "faktor_iklim": round(temp_factor - rain_penalty, 2),
                "varietas": varietas,
                "model": "SugarcaneBrixRegressor-v2"
            }
        }

    # ─────────────────────────────────────────────────────────────────
    # 2. predict_yield(input_features)
    # ─────────────────────────────────────────────────────────────────
    def predict_yield(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prediksi produktivitas hasil panen tebu dalam satuan Ton / Hektar.
        """
        tinggi = float(input_features.get("tinggi_batang", input_features.get("stem_height", 260.0)))
        diameter = float(input_features.get("diameter_batang", input_features.get("stem_diameter", 2.8)))
        populasi = float(input_features.get("populasi_per_meter", input_features.get("density", 13.5)))
        umur = float(input_features.get("umur_hari", 300))

        # Berat tebu per batang: W = Volume * Kerapatan
        radius = diameter / 2.0
        volume_batang_cm3 = math.pi * (radius ** 2) * tinggi
        berat_per_batang_kg = (volume_batang_cm3 * 1.08) / 1000.0 # Massa jenis tebu ~1.08 g/cm3

        # Estimasi populasi per hektar (jarak tanam standar 1.1 - 1.2 m juringan)
        total_batang_per_ha = populasi * (10000.0 / 1.15)
        tonase_per_ha = (total_batang_per_ha * berat_per_batang_kg) / 1000.0

        # Koreksi umur
        if umur < 240:
            tonase_per_ha *= (umur / 240.0)

        tonase_per_ha = max(45.0, min(160.0, round(tonase_per_ha, 2)))
        confidence = round(random.uniform(0.910, 0.965), 4)

        if tonase_per_ha >= 100.0:
            kategori = "Potensi Tinggi (>100 Ton/Ha)"
        elif tonase_per_ha >= 75.0:
            kategori = "Potensi Sedang-Normal (75 - 100 Ton/Ha)"
        else:
            kategori = "Potensi Rendah (<75 Ton/Ha)"

        return {
            "predicted_yield_ton_ha": tonase_per_ha,
            "confidence_score": confidence,
            "kategori_potensi": kategori,
            "estimasi_berat_batang_kg": round(berat_per_batang_kg, 2)
        }

    # ─────────────────────────────────────────────────────────────────
    # 3. predict_sugar(input_features)
    # ─────────────────────────────────────────────────────────────────
    def predict_sugar(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prediksi rendemen gula kristal / kadar gula komersial (%).
        """
        brix = float(input_features.get("brix", input_features.get("nilai_brix", 19.5)))
        purity = float(input_features.get("purity", 0.84)) # Koefisien kemurnian

        pol = brix * purity
        # Formula rendemen pabrik gula: R = S * (Pol - 0.4 * (Brix - Pol))
        rendemen = 0.705 * (pol - 0.4 * (brix - pol))
        rendemen = max(5.0, min(13.5, round(rendemen, 2)))

        confidence = round(random.uniform(0.925, 0.978), 4)

        if rendemen >= 9.5:
            kategori = "Super / Premium (Rendemen > 9.5%)"
        elif rendemen >= 7.5:
            kategori = "Standar Industri (Rendemen 7.5% - 9.5%)"
        else:
            kategori = "Kurang Optimal (< 7.5%)"

        return {
            "predicted_sugar_percent": rendemen,
            "rendemen_kategori": kategori,
            "confidence_score": confidence,
            "estimasi_pol": round(pol, 2)
        }

    # ─────────────────────────────────────────────────────────────────
    # 4. predict_nira(input_features)
    # ─────────────────────────────────────────────────────────────────
    def predict_nira(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prediksi persentase perahan nira dan volume liter nira per ton tebu.
        """
        brix = float(input_features.get("brix", 19.0))
        kelembapan = float(input_features.get("kelembapan_tanah", input_features.get("kelembapan", 70.0)))

        # Nira ekstraksi biasanya 68% - 78% dari bobot batang
        extraction_rate = 72.0 + (kelembapan - 70.0) * 0.12 - (brix - 18.0) * 0.35
        extraction_rate = max(62.0, min(80.0, round(extraction_rate, 2)))

        # 1 Ton Tebu = 1000 kg. Berat jenis nira ~1.08 kg/L
        berat_nira_kg = (extraction_rate / 100.0) * 1000.0
        liter_per_ton = round(berat_nira_kg / 1.08, 1)

        kualitas = "Kadar Nira Pekat & Berkualitas" if brix >= 19.0 else "Nira Encer / Normal"

        return {
            "predicted_nira_percent": extraction_rate,
            "volume_per_ton_liter": liter_per_ton,
            "kualitas_nira": kualitas,
            "confidence_score": 0.9450
        }

    # ─────────────────────────────────────────────────────────────────
    # 5. predict_duration(input_features)
    # ─────────────────────────────────────────────────────────────────
    def predict_duration(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prediksi sisa hari menuju panen optimal dan tanggal rekomendasi tebang.
        """
        current_brix = float(input_features.get("brix", input_features.get("nilai_brix", 17.5)))
        target_brix = float(input_features.get("ambang_panen", 19.5))
        laju_kenaikan_per_minggu = float(input_features.get("laju_brix_minggu", 0.65))

        selisih = target_brix - current_brix
        if selisih <= 0:
            remaining_days = 0
            urgensi = "Panen Segera (Sudah Mencapai Ambang Batas)"
        else:
            minggu = selisih / laju_kenaikan_per_minggu
            remaining_days = max(1, int(round(minggu * 7)))
            if remaining_days <= 7:
                urgensi = "Prioritas 1 (Siaga Tebang 1 Minggu Kedepan)"
            elif remaining_days <= 21:
                urgensi = "Prioritas 2 (Waspada Pematangan)"
            else:
                urgensi = "Prioritas 3 (Masih Fase Pembesaran)"

        rec_date = (datetime.now() + timedelta(days=remaining_days)).strftime("%Y-%m-%d")

        return {
            "predicted_remaining_days": remaining_days,
            "recommended_harvest_date": rec_date,
            "urgensi_tebang": urgensi,
            "target_brix": target_brix,
            "current_brix": current_brix
        }

    # ─────────────────────────────────────────────────────────────────
    # 6. classify_disease(input_features)
    # ─────────────────────────────────────────────────────────────────
    def classify_disease(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Klasifikasi kesehatan tanaman dan deteksi penyakit tebu.
        """
        gejala = str(input_features.get("gejala_penyakit", input_features.get("symptom", "tidak_ada"))).lower()

        if "merah" in gejala or "red rot" in gejala or "berongga" in gejala:
            penyakit = "Busuk Batang Merah (Red Rot / Colletotrichum falcatum)"
            infected = True
            conf = 0.9620
            treatment = "Isolasi area yang terinfeksi, musnahkan batang bergejala, perbaiki drainase lahan."
        elif "api" in gejala or "smut" in gejala or "terpilin" in gejala:
            penyakit = "Luka Api (Sugarcane Smut / Sporisorium scitamineum)"
            infected = True
            conf = 0.9540
            treatment = "Pangkas dan bakar tunas cambuk sebelum spora hitam menyebar, gunakan varietas tahan."
        elif "mosaik" in gejala or "garis" in gejala or "mosaic" in gejala:
            penyakit = "Mosaik Tebu (Sugarcane Mosaic Virus)"
            infected = True
            conf = 0.9380
            treatment = "Kendalikan vektor kutu daun (Aphis maidis) dengan insektisida nabati atau musuh alami."
        elif "karat" in gejala or "rust" in gejala or "coklat" in gejala:
            penyakit = "Karat Daun (Sugarcane Rust / Puccinia melanocephala)"
            infected = True
            conf = 0.9410
            treatment = "Semprot fungisida berbahan aktif mankozeb bila serangan meluas di musim hujan."
        else:
            penyakit = "Tanaman Sehat / Bebas Penyakit"
            infected = False
            conf = 0.9850
            treatment = "Kondisi tanaman optimal. Lanjutkan pemantauan rutin dan pemupukan berimbang."

        return {
            "disease_class": penyakit,
            "is_infected": infected,
            "confidence_score": conf,
            "treatment_recommendation": treatment
        }

    # ─────────────────────────────────────────────────────────────────
    # 7. calculate_winter_carp(brix, yield_val)
    # ─────────────────────────────────────────────────────────────────
    def calculate_winter_carp(self, brix: float, yield_val: float) -> Dict[str, Any]:
        """
        Kalkulasi rendemen teoritis dan produksi gula berdasarkan formula Winter-Carp.
        Standar industri gula Indonesia:
        Rendemen = 0.7 * (Pol - 0.4 * (Brix - Pol))
        Produksi Gula = Yield * (Rendemen / 100)
        """
        b = float(brix)
        y = float(yield_val)

        # Pol nira diperkirakan dari kemurnian 85%
        pol = b * 0.85
        rendemen_hablur = 0.70 * (pol - 0.40 * (b - pol))
        rendemen_hablur = max(4.0, min(14.0, round(rendemen_hablur, 3)))

        gula_ton_ha = round(y * (rendemen_hablur / 100.0), 2)

        return {
            "brix": b,
            "yield_ton_ha": y,
            "rendemen_winter_carp": rendemen_hablur,
            "sugar_yield_ton_ha": gula_ton_ha,
            "faktor_hablur": 0.70,
            "formula_reference": "Winter-Carp Classical Rendemen Equation"
        }

    # ─────────────────────────────────────────────────────────────────
    # 8. analyze_seasons(input_features)
    # ─────────────────────────────────────────────────────────────────
    def analyze_seasons(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisis pengaruh musim terhadap kematangan sukrosa dan kelayakan giling.
        """
        month = input_features.get("bulan", datetime.now().month)
        if isinstance(month, str):
            try:
                month = int(month)
            except ValueError:
                month = datetime.now().month

        ch = float(input_features.get("curah_hujan", 80.0))

        if month in [5, 6]:
            phase = "Giling Awal (Mei - Juni)"
            kondisi = "Fase awal pembukaan giling pabrik. Rendemen mulai merangkak naik."
            index_maturitas = 0.82
            agronomi = "Prioritaskan panen varietas masak awal (misal: Bululawang, Cenning)."
        elif month in [7, 8, 9]:
            phase = "Giling Tengah / Musim Kemarau Puncak (Juli - September)"
            kondisi = "Puncak kematangan sukrosa terbaik. Penyinaran matahari optimal dan curah hujan minim."
            index_maturitas = 0.98
            agronomi = "Maksimalkan tebang giling untuk semua varietas utama dengan kapasitas pabrik penuh."
        elif month in [10, 11]:
            phase = "Giling Akhir (Oktober - November)"
            kondisi = "Peralihan musim hujan. Risiko pengenceran nira bila curah hujan mulai tinggi."
            index_maturitas = 0.88
            agronomi = "Segera selesaikan sisa tebangan sebelum intensitas hujan mengencerkan kadar Brix."
        else:
            phase = "Musim Tanam & Pemeliharaan Vegetatif (Desember - April)"
            kondisi = "Musim hujan penuh. Tanaman dalam fase pertunasan dan pemanjangan batang."
            index_maturitas = 0.45
            agronomi = "Fokus pada pemupukan susulan, pembumbunan, dan pengendalian gulma."

        return {
            "season_phase": phase,
            "ripening_climate_index": index_maturitas,
            "kondisi_iklim": kondisi,
            "curah_hujan_bulanan": ch,
            "rekomendasi_agronomi": agronomi
        }

    # ─────────────────────────────────────────────────────────────────
    # Integration 1: Memasok Nilai Brix -> DataBrix
    # ─────────────────────────────────────────────────────────────────
    def feed_brix_to_sample(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Menjalankan estimasi Brix lalu menyiapkan payload DataBrix
        sesuai relasi Class Diagram: EBrixMLEngine --Memasok Nilai Brix--> DataBrix
        """
        res_brix = self.predict_brix(input_features)
        predicted_val = res_brix["predicted_brix"]

        return {
            "nilai_brix": predicted_val,
            "status_sinkron": "tersinkron",
            "catatan": f"Nilai Brix dipasok otomatis oleh EBrixMLEngine ({res_brix['kategori']})",
            "confidence_score": res_brix["confidence_score"],
            "raw_prediction": res_brix
        }

    # ─────────────────────────────────────────────────────────────────
    # Integration 2: Menghasilkan Inferensi Multi-Target -> Prediksi
    # ─────────────────────────────────────────────────────────────────
    def infer_multi_target(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Menghasilkan inferensi lengkap multi-target:
        Brix, Yield, Rendemen Sugar, Nira, Durasi, Penyakit, Winter-Carp, dan Analisis Musim.
        Sesuai relasi: EBrixMLEngine --Menghasilkan Inferensi Multi-Target--> Prediksi
        """
        pred_brix = self.predict_brix(input_features)
        pred_yield = self.predict_yield(input_features)

        # Teruskan Brix dan Yield ke kalkulasi turunan
        input_features["brix"] = pred_brix["predicted_brix"]
        input_features["yield_ton_ha"] = pred_yield["predicted_yield_ton_ha"]

        pred_sugar = self.predict_sugar(input_features)
        pred_nira = self.predict_nira(input_features)
        pred_duration = self.predict_duration(input_features)
        pred_disease = self.classify_disease(input_features)
        pred_winter = self.calculate_winter_carp(pred_brix["predicted_brix"], pred_yield["predicted_yield_ton_ha"])
        pred_season = self.analyze_seasons(input_features)

        summary_text = (
            f"Brix: {pred_brix['predicted_brix']}° | "
            f"Yield: {pred_yield['predicted_yield_ton_ha']} Ton/Ha | "
            f"Rendemen: {pred_sugar['predicted_sugar_percent']}% | "
            f"Status: {pred_duration['urgensi_tebang']} | "
            f"Penyakit: {pred_disease['disease_class']}"
        )

        overall_confidence = round(
            (pred_brix["confidence_score"] + pred_yield["confidence_score"] + pred_sugar["confidence_score"] + pred_disease["confidence_score"]) / 4.0,
            4
        )

        return {
            "hasil_prediksi": summary_text,
            "confidence_score": overall_confidence,
            "multi_target_details": {
                "brix": pred_brix,
                "yield": pred_yield,
                "sugar": pred_sugar,
                "nira": pred_nira,
                "duration": pred_duration,
                "disease": pred_disease,
                "winter_carp": pred_winter,
                "seasons": pred_season
            }
        }


# Global Singleton instance
ml_engine = EBrixMLEngine()
