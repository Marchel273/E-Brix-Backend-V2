"""
E-Brix ML Engine — Logika Prediksi Tebu Ensemble Terintegrasi
Memuat model dari model_artifacts/ dan menyediakan fungsi prediksi
untuk digunakan oleh controller backend utama.
"""
import os
import json
import copy
import pickle
import numpy as np
import pandas as pd

# ============================================================
# Memuat Model & Preprocessor Ensemble (> 90%)
# ============================================================
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model_artifacts')

_models_loaded = False
model_yield = None
model_sugar = None
model_nira = None
model_brix = None
model_duration = None
model_disease = None
label_encoders = None
le_disease = None
num_imputer = None
cat_imputer = None
feature_columns = None
num_cols = None
cat_cols = None
form_config = None


def load_models():
    """Memuat seluruh model ensemble dan preprocessor dari model_artifacts/."""
    global _models_loaded
    global model_yield, model_sugar, model_nira, model_brix, model_duration, model_disease
    global label_encoders, le_disease, num_imputer, cat_imputer
    global feature_columns, num_cols, cat_cols, form_config

    if _models_loaded:
        return

    print("[ML Engine] Memuat model ensemble dan preprocessor...")

    models_pkl = os.path.join(MODEL_DIR, 'sugarcane_models.pkl')
    if not os.path.exists(models_pkl):
        raise FileNotFoundError(f"Model file tidak ditemukan: {models_pkl}")

    with open(models_pkl, 'rb') as f:
        models_bundle = pickle.load(f)

    model_yield = models_bundle['model_yield']
    model_sugar = models_bundle['model_sugar']
    model_nira = models_bundle['model_nira']
    model_brix = models_bundle['model_brix']
    model_duration = models_bundle['model_duration']
    model_disease = models_bundle['model_disease']

    label_encoders = models_bundle['label_encoders']
    le_disease = models_bundle['le_disease']
    num_imputer = models_bundle['num_imputer']
    cat_imputer = models_bundle['cat_imputer']
    feature_columns = models_bundle['feature_names']
    num_cols = models_bundle['num_cols']
    cat_cols = models_bundle['cat_cols']

    config_path = os.path.join(MODEL_DIR, 'form_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        form_config = json.load(f)

    _models_loaded = True
    print("[ML Engine] Seluruh model ensemble high-performance berhasil dimuat!")


# ============================================================
# Konfigurasi Musim Indonesia (Negara Tropis)
# ============================================================
MUSIM_PENGHUJAN = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
MUSIM_KEMARAU   = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']

MONTH_NAMES_ID = {
    'Jan': 'Januari', 'Feb': 'Februari', 'Mar': 'Maret',
    'Apr': 'April',   'May': 'Mei',      'Jun': 'Juni',
    'Jul': 'Juli',    'Aug': 'Agustus',  'Sep': 'September',
    'Oct': 'Oktober', 'Nov': 'November', 'Dec': 'Desember',
}

ALL_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

LABEL_ID = {
    'Month': 'Bulan Tanam',
    'Temp_Avg_C': 'Suhu Udara Sekitar (°C)',
    'Rainfall_Total_mm': 'Curah Hujan Musiman (mm)',
    'Soil_Type': 'Jenis Tanah',
    'Irrigation_Method_Type': 'Cara Pengairan',
    'Water_Quality_Category': 'Kualitas Air Pengairan',
    'Planting_Method': 'Cara Tanam',
    'Variety': 'Varietas Bibit Tebu',
    'Fertilizer_Type': 'Jenis Pupuk Utama',
    'Weed_Control': 'Cara Basmi Gulma/Rumput Liar',
    'Pest_Level': 'Tingkat Serangan Hama',
}

FEATURE_GROUPS = {
    '🌤️ Kondisi Lingkungan': ['Month', 'Temp_Avg_C', 'Rainfall_Total_mm', 'Soil_Type'],
    '💧 Pengairan': ['Irrigation_Method_Type', 'Water_Quality_Category'],
    '🌱 Bibit & Tanam': ['Variety', 'Planting_Method'],
    '🚜 Perawatan & Hama': ['Fertilizer_Type', 'Weed_Control', 'Pest_Level'],
}

CAT_TRANSLATE = {
    'Month': {'Jan': 'Januari', 'Feb': 'Februari', 'Mar': 'Maret', 'Apr': 'April',
              'May': 'Mei', 'Jun': 'Juni', 'Jul': 'Juli', 'Aug': 'Agustus',
              'Sep': 'September', 'Oct': 'Oktober', 'Nov': 'November', 'Dec': 'Desember'},
    'Soil_Type': {'Clay': 'Tanah Liat (Lempung)', 'Sandy': 'Tanah Pasir', 'Loamy': 'Tanah Gembur (Loam)', 'Alluvial': 'Tanah Endapan (Aluvial)'},
    'Irrigation_Method_Type': {'Flood': 'Banjir / Leb, Dialirkan', 'Drip': 'Tetes (Pipa)', 'Sprinkler': 'Disemprot / Sprinkler'},
    'Water_Quality_Category': {'Good': 'Bagus / Tawar', 'Moderate': 'Sedang', 'Saline': 'Payau / Agak Asin'},
    'Planting_Method': {'Paired Row': 'Baris Ganda', 'Straight Row': 'Baris Lurus (Standar)', 'Trench': 'Sistem Parit', 'Circular': 'Melingkar'},
    'Weed_Control': {'Manual': 'Cabut Manual / Dicangkul', 'Chemical': 'Semprot Obat Kimia'},
    'Pest_Level': {'Low': 'Ringan', 'Medium': 'Sedang', 'High': 'Parah'},
}


def get_form_config():
    """Mengembalikan konfigurasi form untuk UI."""
    load_models()
    groups = {}
    for group_name, cols in FEATURE_GROUPS.items():
        fields = []
        for col in cols:
            if col not in feature_columns:
                continue
            label = LABEL_ID.get(col, col)
            if col in cat_cols:
                options = form_config['cat_options'].get(col, [])
                translate = CAT_TRANSLATE.get(col, {})
                opt_list = [{'value': v, 'label': translate.get(v, v)} for v in options]
                fields.append({'name': col, 'label': label, 'type': 'select', 'options': opt_list})
            else:
                ranges = form_config['num_ranges'].get(col, {})
                fields.append({
                    'name': col, 'label': label, 'type': 'number',
                    'min': ranges.get('min', 0),
                    'max': ranges.get('max', 100),
                    'default': round(ranges.get('mean', 0), 2),
                    'step': 0.01 if ranges.get('max', 100) < 50 else 0.1,
                })
        if fields:
            groups[group_name] = fields
    return groups


def _build_feature_row(input_dict):
    """Membangun 1 baris DataFrame yang siap di-predict oleh model ensemble."""
    load_models()
    row_data = {}
    for col in feature_columns:
        val = input_dict.get(col)
        if col in num_cols:
            if val is not None and val != '':
                try:
                    row_data[col] = float(val)
                except (ValueError, TypeError):
                    row_data[col] = form_config['num_ranges'].get(col, {}).get('mean', 0.0)
            else:
                row_data[col] = form_config['num_ranges'].get(col, {}).get('mean', 0.0)
        else:
            if val is None or val == '':
                val = form_config['cat_options'].get(col, [''])[0]
            row_data[col] = str(val)

    df_row = pd.DataFrame([row_data])

    # Hitung fitur turunan agrikultur
    if 'NPK_Total' in feature_columns:
        n = df_row.get('Nitrogen_kg_per_acre', pd.Series([0.0])).iloc[0]
        p = df_row.get('Phosphorus_kg_per_acre', pd.Series([0.0])).iloc[0]
        k = df_row.get('Potassium_kg_per_acre', pd.Series([0.0])).iloc[0]
        df_row['NPK_Total'] = n + p + k

    if 'Temp_Range_C' in feature_columns:
        t_max = df_row.get('Temp_Max_C', pd.Series([32.0])).iloc[0]
        t_min = df_row.get('Temp_Min_C', pd.Series([20.0])).iloc[0]
        df_row['Temp_Range_C'] = t_max - t_min

    if 'Rain_Per_Day' in feature_columns:
        dur = df_row.get('Crop_Duration_Days', pd.Series([326.0])).iloc[0]
        dur = 326.0 if dur == 0 else dur
        rain = df_row.get('Rainfall_Total_mm', pd.Series([1200.0])).iloc[0]
        df_row['Rain_Per_Day'] = rain / dur

    if 'Bio_Index' in feature_columns:
        h = df_row.get('Cane_Height_cm', pd.Series([180.0])).iloc[0]
        d = df_row.get('Cane_Diameter_cm', pd.Series([3.0])).iloc[0]
        tc = df_row.get('Tillering_Count', pd.Series([8.0])).iloc[0]
        pd_val = df_row.get('Plant_Density', pd.Series([120000.0])).iloc[0]
        df_row['Bio_Index'] = (h / 180.0) + (d / 3.0) + (tc / 8.0) + (pd_val / 120000.0)

    # Encoding fitur kategorikal
    for col in cat_cols:
        if col in label_encoders:
            try:
                df_row[col] = label_encoders[col].transform(df_row[col].astype(str))
            except (ValueError, KeyError):
                df_row[col] = 0

    return df_row[feature_columns]


def _run_single_prediction(input_dict):
    """Mengembalikan dict prediksi dari model ensemble high-performance (> 90%)."""
    load_models()
    X_row = _build_feature_row(input_dict)

    pred_yield = float(model_yield.predict(X_row)[0])
    pred_sugar = float(model_sugar.predict(X_row)[0])
    pred_nira = float(model_nira.predict(X_row)[0])
    pred_brix = float(model_brix.predict(X_row)[0])
    pred_duration = float(model_duration.predict(X_row)[0])

    pred_disease_proba = model_disease.predict_proba(X_row)[0]
    pred_disease_idx = int(np.argmax(pred_disease_proba))
    pred_disease_label = le_disease.inverse_transform([pred_disease_idx])[0]
    pred_disease_conf = float(pred_disease_proba[pred_disease_idx]) * 100

    disease_score = {'Low': 1, 'Medium': 2, 'High': 3}.get(pred_disease_label, 2)

    return {
        'yield': pred_yield,
        'sugar': pred_sugar,
        'nira': pred_nira,
        'brix': pred_brix,
        'duration': pred_duration,
        'disease_label': pred_disease_label,
        'disease_conf': pred_disease_conf,
        'disease_proba': pred_disease_proba,
        'disease_score': disease_score,
    }


def _run_season_analysis(data):
    """
    Menjalankan prediksi untuk semua 12 bulan (parameter lain tetap),
    lalu membandingkan performa Musim Penghujan vs Musim Kemarau.
    """
    load_models()
    disease_id = {'Low': 'Rendah', 'Medium': 'Sedang', 'High': 'Tinggi'}

    base_input = {}
    for col in feature_columns:
        val = data.get(col)
        if col in num_cols:
            base_input[col] = float(val) if val is not None and val != '' else form_config['num_ranges'][col]['mean']
        else:
            if val is None or val == '':
                val = form_config['cat_options'][col][0]
            base_input[col] = val

    month_results = {}
    for month in ALL_MONTHS:
        m_input = copy.deepcopy(base_input)
        if 'Month' in feature_columns:
            m_input['Month'] = month
        pred = _run_single_prediction(m_input)
        month_results[month] = pred

    def aggregate_season(months_list):
        yields = [month_results[m]['yield'] for m in months_list]
        brixs = [month_results[m]['brix'] for m in months_list]
        durations = [month_results[m]['duration'] for m in months_list]
        d_scores = [month_results[m]['disease_score'] for m in months_list]
        return {
            'avg_yield': np.mean(yields),
            'avg_brix': np.mean(brixs),
            'avg_duration': np.mean(durations),
            'avg_disease_score': np.mean(d_scores),
            'months': months_list,
        }

    hujan = aggregate_season(MUSIM_PENGHUJAN)
    kemarau = aggregate_season(MUSIM_KEMARAU)

    all_yields = [month_results[m]['yield'] for m in ALL_MONTHS]
    all_brixs = [month_results[m]['brix'] for m in ALL_MONTHS]
    yield_min, yield_max = min(all_yields), max(all_yields)
    brix_min, brix_max = min(all_brixs), max(all_brixs)

    best_month = None
    best_score = -1
    month_details = []

    for month in ALL_MONTHS:
        r = month_results[month]
        y_norm = (r['yield'] - yield_min) / (yield_max - yield_min + 1e-9)
        b_norm = (r['brix'] - brix_min) / (brix_max - brix_min + 1e-9)
        d_norm = 1.0 - (r['disease_score'] - 1) / 2.0

        score = 0.40 * y_norm + 0.35 * b_norm + 0.25 * d_norm
        musim = 'Penghujan' if month in MUSIM_PENGHUJAN else 'Kemarau'

        month_details.append({
            'bulan_en': month,
            'bulan_id': MONTH_NAMES_ID[month],
            'musim': musim,
            'yield': round(r['yield'], 2),
            'brix': round(r['brix'], 2),
            'duration': round(r['duration'], 0),
            'disease': disease_id.get(r['disease_label'], r['disease_label']),
            'disease_en': r['disease_label'],
            'score': round(score * 100, 1),
        })

        if score > best_score:
            best_score = score
            best_month = month

    hujan_scores = [d['score'] for d in month_details if d['musim'] == 'Penghujan']
    kemarau_scores = [d['score'] for d in month_details if d['musim'] == 'Kemarau']
    avg_hujan_score = np.mean(hujan_scores)
    avg_kemarau_score = np.mean(kemarau_scores)

    if avg_hujan_score > avg_kemarau_score:
        musim_terbaik = 'Penghujan'
        musim_terbaik_emoji = '🌧️'
    else:
        musim_terbaik = 'Kemarau'
        musim_terbaik_emoji = '☀️'

    selisih_persen = abs(avg_hujan_score - avg_kemarau_score)

    if musim_terbaik == 'Penghujan':
        penjelasan = (
            f"Berdasarkan analisis AI terhadap 12 bulan tanam, Musim Penghujan (Okt–Mar) "
            f"lebih unggul dengan skor rata-rata {avg_hujan_score:.1f} vs {avg_kemarau_score:.1f} (Kemarau). "
            f"Ketersediaan air hujan alami mendukung pertumbuhan vegetatif tebu di fase awal. "
            f"Bulan terbaik: {MONTH_NAMES_ID[best_month]} (skor {best_score*100:.1f})."
        )
    else:
        penjelasan = (
            f"Berdasarkan analisis AI terhadap 12 bulan tanam, Musim Kemarau (Apr–Sep) "
            f"lebih unggul dengan skor rata-rata {avg_kemarau_score:.1f} vs {avg_hujan_score:.1f} (Penghujan). "
            f"Intensitas cahaya matahari yang tinggi memaksimalkan fotosintesis dan akumulasi sukrosa. "
            f"Bulan terbaik: {MONTH_NAMES_ID[best_month]} (skor {best_score*100:.1f})."
        )

    return {
        'musim_terbaik': musim_terbaik,
        'musim_terbaik_emoji': musim_terbaik_emoji,
        'bulan_terbaik_en': best_month,
        'bulan_terbaik_id': MONTH_NAMES_ID[best_month],
        'skor_terbaik': round(best_score * 100, 1),
        'penghujan': {
            'avg_yield': round(hujan['avg_yield'], 2),
            'avg_brix': round(hujan['avg_brix'], 2),
            'avg_duration': round(hujan['avg_duration'], 0),
            'avg_disease_score': round(hujan['avg_disease_score'], 2),
            'avg_composite_score': round(avg_hujan_score, 1),
            'periode': 'Oktober – Maret',
        },
        'kemarau': {
            'avg_yield': round(kemarau['avg_yield'], 2),
            'avg_brix': round(kemarau['avg_brix'], 2),
            'avg_duration': round(kemarau['avg_duration'], 0),
            'avg_disease_score': round(kemarau['avg_disease_score'], 2),
            'avg_composite_score': round(avg_kemarau_score, 1),
            'periode': 'April – September',
        },
        'selisih_persen': round(selisih_persen, 1),
        'penjelasan': penjelasan,
        'detail_bulanan': month_details,
    }


def run_prediction(input_data):
    """
    Fungsi utama prediksi — mengembalikan dict lengkap dengan prediksi,
    analisis musim, dan rekomendasi. Dipanggil oleh controller.
    """
    load_models()

    pred = _run_single_prediction(input_data)
    pred_yield = pred['yield']
    pred_brix = pred['brix']
    pred_duration = pred['duration']
    pred_disease_label = pred['disease_label']
    pred_disease_conf = pred['disease_conf']
    pred_disease_proba = pred['disease_proba']
    pred_sugar = pred['sugar']
    pred_nira = pred['nira']

    disease_id = {'Low': 'Rendah', 'Medium': 'Sedang', 'High': 'Tinggi'}

    bulan_panen = int(pred_duration / 30)
    sisa_hari = int(pred_duration % 30)

    # Perhitungan Gula Rumus Winter-Carp (Industri Gula)
    HK_STANDAR = 0.80
    pol_standar = pred_brix * HK_STANDAR
    nn_standar = pol_standar - 0.4 * (pred_brix - pol_standar)
    nn_cepat = 0.72 * pred_brix

    HK_OPTIMIS = 0.85
    pol_optimis = pred_brix * HK_OPTIMIS
    nn_optimis = pol_optimis - 0.4 * (pred_brix - pol_optimis)

    potensi_gula_standar = pred_yield * (nn_standar / 100.0)
    potensi_gula_optimis = pred_yield * (nn_optimis / 100.0)

    # Actionable Recommendations
    rec_hasil = "Pertahankan jadwal pengairan dan nutrisi saat ini. Hasil panen diprediksi sudah optimal."
    if pred_yield < 200:
        rec_hasil = "Terapkan pemupukan berimbang (tambahkan Kalium) dan pastikan pengairan cukup di fase pertumbuhan vegetatif untuk mendongkrak tonase panen."

    rec_brix = "Kadar nira diprediksi sangat baik. Lakukan tebang-angkut-giling dengan cepat agar tidak terjadi inversi sukrosa."
    if pred_brix < 18:
        rec_brix = "Hentikan irigasi (dry-off) 4-6 minggu sebelum jadwal panen untuk memaksa tebu berhenti tumbuh dan memacu akumulasi kristal gula (sukrosa)."

    rec_penyakit = "Risiko rendah. Tetap lakukan pemantauan rutin dan kendalikan gulma di sekitar tanaman tebu."
    if pred_disease_label == 'High':
        rec_penyakit = "Risiko penyakit/hama TINGGI! Segera aplikasikan fungisida/insektisida sistemik, perbaiki drainase kebun (cegah genangan), dan pangkas daun bawah yang sakit."
    elif pred_disease_label == 'Medium':
        rec_penyakit = "Risiko SEDANG. Tingkatkan sanitasi kebun dengan klentek (mengelupas daun kering) untuk mengurangi kelembapan dan tempat sembunyi hama."

    season_analysis = _run_season_analysis(input_data)

    prediksi = {
        'hasil_panen': round(pred_yield, 2),
        'kadar_gula_brix': round(pred_brix, 2),
        'durasi_panen_hari': round(pred_duration, 0),
        'durasi_panen_bulan': bulan_panen,
        'durasi_panen_sisa_hari': sisa_hari,
        'keparahan_penyakit': disease_id.get(pred_disease_label, pred_disease_label),
        'keparahan_penyakit_en': pred_disease_label,
        'kepercayaan_penyakit': round(pred_disease_conf, 1),
        'probabilitas_penyakit': {
            disease_id.get(cls, cls): round(float(prob) * 100, 1)
            for cls, prob in zip(le_disease.classes_, pred_disease_proba)
        },
        'perhitungan_gula': {
            'brix': round(pred_brix, 2),
            'hk_standar_persen': int(HK_STANDAR * 100),
            'hk_optimis_persen': int(HK_OPTIMIS * 100),
            'pol_standar': round(pol_standar, 2),
            'pol_optimis': round(pol_optimis, 2),
            'nn_standar': round(nn_standar, 2),
            'nn_optimis': round(nn_optimis, 2),
            'nn_cepat': round(nn_cepat, 2),
            'potensi_gula_standar': round(potensi_gula_standar, 2),
            'potensi_gula_optimis': round(potensi_gula_optimis, 2),
        },
        'potensi_gula': round(potensi_gula_standar, 2),
        'potensi_gula_kristal': round(pred_sugar, 2),
        'produksi_nira': round(pred_nira, 2),
    }

    rekomendasi = {
        'waktu_panen': f"Jadwalkan panen {int(pred_duration)} hari (~{bulan_panen} bulan {sisa_hari} hari) lagi saat rendemen memuncak.",
        'tindakan_hasil': rec_hasil,
        'tindakan_brix': rec_brix,
        'tindakan_penyakit': rec_penyakit,
        'musim_tanam': season_analysis['penjelasan'],
        'gula': (
            f"Rumus Winter-Carp: Pol = Brix × HK, lalu NN = Pol − 0.4 × (Brix − Pol). "
            f"Dengan Brix = {pred_brix:.2f}% dan HK = 80%, diperoleh Pol = {pol_standar:.2f}%, "
            f"Nilai Nira (NN) = {nn_standar:.2f} gram gula per 100g nira. "
            f"Rumus cepat: NN = 0.72 × {pred_brix:.2f} = {nn_cepat:.2f} g/100g nira. "
            f"Potensi total gula dari panen: {potensi_gula_standar:.2f} – {potensi_gula_optimis:.2f} Quintal/Acre."
        ),
    }

    return {
        'success': True,
        'prediksi': prediksi,
        'analisis_musim': season_analysis,
        'rekomendasi': rekomendasi,
    }
