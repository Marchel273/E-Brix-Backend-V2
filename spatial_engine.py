"""
E-Brix Spatial Engine — Interpolasi Geostatistika Kematangan Tebu (Brix)
=======================================================================
Port dari notebook `Machine Learning-E-Brix/Sugarcane_Spatial_Interpolation.ipynb`
ke backend Flask dengan 2 algoritma utama berakurasi tinggi:

1. Hybrid Regression-Kriging (`hybrid_rk`): Random Forest + Residual Ordinary Kriging
2. Kriging with External Drift (`ked`): Gaussian Semivariogram + External Drift (NDVI / Tren Spasial)
3. Ordinary Kriging (`kriging`) & IDW (`idw`) sebagai opsi/fallback saat sampel < 4 titik

Dilengkapi:
- Validasi silang out-of-sample (5-Fold CV untuk n > 15 / Leave-One-Out untuk n <= 15)
- Komparasi metrik langsung antara Hybrid Regression-Kriging dan KED
- Deteksi anomali spasial (residual out-of-fold |z| >= 2)
- Simulasi pembaruan harian agroklimat (GDD, dry-down, water dilution)
"""
import math
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

EARTH_R = 6371000.0  # meter

# Ambang kematangan (°Brix) — konsisten dengan legenda peta frontend
BRIX_LOW = 15.0
BRIX_HIGH = 19.0

METHOD_LABELS = {
    "hybrid_rk": "Hybrid Regression-Kriging (RF + Kriging)",
    "ked": "Kriging with External Drift (KED)",
    "kriging": "Ordinary Kriging",
    "idw": "Inverse Distance Weighting (IDW)",
}


# ------------------------------------------------------------------
# Utilitas koordinat & fitur spasial
# ------------------------------------------------------------------
def lonlat_to_xy(lon, lat, lon0, lat0):
    """Proyeksi equirectangular lokal (meter). Akurat untuk skala kebun (< 50 km)."""
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    x = np.radians(lon - lon0) * EARTH_R * math.cos(math.radians(lat0))
    y = np.radians(lat - lat0) * EARTH_R
    return np.column_stack([x, y])


def _pairwise(a, b):
    d2 = (a[:, None, :] - b[None, :, :]) ** 2
    return np.sqrt(d2.sum(-1))


def zone_of(brix):
    if brix > BRIX_HIGH:
        return "tinggi"
    if brix >= BRIX_LOW:
        return "sedang"
    return "rendah"


def _build_spatial_features(xy, scale=1.0, drift=None):
    """
    Rekayasa fitur spasial non-linear (koordinat ternormalisasi, jarak radial dari pusat
    kebun, kuadratik permukaan, dan opsional drift eksternal seperti NDVI).
    """
    s = max(float(scale), 1.0)
    xn = xy[:, 0] / s
    yn = xy[:, 1] / s
    r = np.sqrt(xn ** 2 + yn ** 2)
    cols = [xn, yn, r, xn ** 2, yn ** 2, xn * yn]
    if drift is not None:
        cols.append(np.asarray(drift, dtype=float))
    return np.column_stack(cols)


def _fit_drift_surface(xy, values, scale=1.0):
    """
    Membangun fungsi drift eksternal halus (tren linear + radial pusat kebun, 4 parameter
    dengan regularisasi Ridge) hanya dari titik latih (zero data leakage) agar stabil
    dan tidak mengalami overshooting di tepi petak ketika NDVI satelit belum tersedia.
    """
    s = max(float(scale), 1.0)
    xn = xy[:, 0] / s
    yn = xy[:, 1] / s
    r = np.sqrt(xn ** 2 + yn ** 2)
    X = np.column_stack([np.ones(len(xy)), xn, yn, r])
    reg = np.eye(X.shape[1]) * 0.5
    reg[0, 0] = 0.0
    coef = np.linalg.pinv(X.T @ X + reg) @ (X.T @ values)

    def predict_drift(target_xy):
        tx = target_xy[:, 0] / s
        ty = target_xy[:, 1] / s
        tr = np.sqrt(tx ** 2 + ty ** 2)
        Xt = np.column_stack([np.ones(len(target_xy)), tx, ty, tr])
        return Xt @ coef

    return predict_drift


# ------------------------------------------------------------------
# Model Geostatistika
# ------------------------------------------------------------------
class InverseDistanceWeighting:
    def __init__(self, power=2.0, k_neighbors=10):
        self.power = power
        self.k_neighbors = k_neighbors

    def fit(self, xy, values, drift=None):
        self.xy = np.asarray(xy, float)
        self.values = np.asarray(values, float)
        return self

    def predict(self, targets, target_drift=None):
        targets = np.atleast_2d(np.asarray(targets, float))
        k = min(self.k_neighbors, len(self.xy))
        d = _pairwise(targets, self.xy)
        idx = np.argsort(d, axis=1)[:, :k]
        dk = np.maximum(np.take_along_axis(d, idx, 1), 1e-6)
        w = 1.0 / dk ** self.power
        w /= w.sum(1, keepdims=True)
        preds = (w * self.values[idx]).sum(1)
        var = (w * (self.values[idx] - preds[:, None]) ** 2).sum(1)
        return preds, var


class OrdinaryKrigingModel:
    """Ordinary Kriging lokal dengan batched 3D solver (np.linalg.solve)."""

    def __init__(self, nugget=None, sill=None, range_val=None, k_neighbors=12, reg=1e-6):
        self.nugget = nugget
        self.sill = sill
        self.range_val = range_val
        self.k_neighbors = k_neighbors
        self.reg = reg

    def semivariogram(self, h):
        h = np.asarray(h, float)
        hr = np.minimum(h / self.range_val, 1.0)
        g = self.nugget + (self.sill - self.nugget) * (1.5 * hr - 0.5 * hr ** 3)
        return np.where(h == 0, 0.0, g)

    def fit(self, xy, values, drift=None):
        self.xy = np.asarray(xy, float)
        self.values = np.asarray(values, float)
        var = float(np.var(self.values))
        if self.sill is None:
            self.sill = max(var, 0.05)
        if self.nugget is None:
            self.nugget = 0.1 * self.sill
        if self.range_val is None:
            d = _pairwise(self.xy, self.xy)
            dmax = float(d.max()) if d.size else 1.0
            self.range_val = max(dmax * 0.5, 5.0)
        return self

    def predict(self, targets, target_drift=None):
        targets = np.atleast_2d(np.asarray(targets, float))
        m = len(targets)
        k = min(self.k_neighbors, len(self.xy))
        d_t = _pairwise(targets, self.xy)
        idx = np.argsort(d_t, axis=1)[:, :k]
        lc = self.xy[idx]
        ly = self.values[idx]
        ld = np.sqrt(((lc[:, :, None, :] - lc[:, None, :, :]) ** 2).sum(-1))

        K = np.zeros((m, k + 1, k + 1))
        K[:, :k, :k] = self.semivariogram(ld) + np.eye(k)[None] * self.reg
        K[:, :k, k] = 1.0
        K[:, k, :k] = 1.0

        g_t = self.semivariogram(np.take_along_axis(d_t, idx, 1))
        rhs = np.ones((m, k + 1, 1))
        rhs[:, :k, 0] = g_t
        try:
            sol = np.linalg.solve(K, rhs)[..., 0]
        except np.linalg.LinAlgError:
            sol = (np.linalg.pinv(K) @ rhs)[..., 0]
        w, mu = sol[:, :k], sol[:, k]
        preds = (w * ly).sum(1)
        var = np.maximum((w * g_t).sum(1) + mu, 0.0)
        return preds, var


class KrigingExternalDriftModel:
    """
    Kriging with External Drift (KED) — Gaussian Semivariogram + External Drift Covariate.
    Port langsung dari Cell 10 notebook `Sugarcane_Spatial_Interpolation.ipynb` dengan
    batched 3D augmented matrix (k+2 x k+2).
    """

    def __init__(self, nugget=None, sill=None, range_val=None, k_neighbors=12, reg=1e-4):
        self.nugget = nugget
        self.sill = sill
        self.range_val = range_val
        self.k_neighbors = k_neighbors
        self.reg = reg
        self._drift_fn = None

    def semivariogram(self, h):
        h = np.asarray(h, float)
        g = self.nugget + (self.sill - self.nugget) * (1.0 - np.exp(-3.0 * (h / self.range_val) ** 2))
        return np.where(h == 0, 0.0, g)

    def fit(self, xy, values, drift=None):
        self.xy = np.asarray(xy, float)
        self.values = np.asarray(values, float)
        d = _pairwise(self.xy, self.xy)
        self._scale = max(float(d.max()) * 0.5, 5.0) if d.size else 10.0

        if drift is not None:
            self.drift_var = np.asarray(drift, float)
            self._drift_fn = None
        else:
            self._drift_fn = _fit_drift_surface(self.xy, self.values, self._scale)
            self.drift_var = self._drift_fn(self.xy)

        # Standardisasi drift agar kondisi matriks (k+2 x k+2) stabil secara numerik
        self._drift_mean = float(np.mean(self.drift_var))
        self._drift_std = float(np.std(self.drift_var)) or 1.0
        self.drift_norm = (self.drift_var - self._drift_mean) / self._drift_std

        resid_var = float(np.var(self.values - self.drift_var)) if self._drift_fn else float(np.var(self.values))
        if self.sill is None:
            self.sill = max(resid_var, 0.1)
        if self.nugget is None:
            self.nugget = 0.18 * self.sill
        if self.range_val is None:
            self.range_val = max(self._scale, 10.0)
        self._eff_reg = max(self.reg, 0.02 * self.sill)
        return self

    def predict(self, targets, target_drift=None):
        targets = np.atleast_2d(np.asarray(targets, float))
        m = len(targets)
        k = min(self.k_neighbors, len(self.xy))

        if target_drift is not None:
            td_raw = np.asarray(target_drift, float)
        elif self._drift_fn is not None:
            td_raw = self._drift_fn(targets)
        else:
            # Jika drift diberikan saat fit tapi tidak saat target, interpolasi drift via IDW
            d_tmp = _pairwise(targets, self.xy)
            i_tmp = np.argsort(d_tmp, axis=1)[:, :k]
            w_tmp = 1.0 / np.maximum(np.take_along_axis(d_tmp, i_tmp, 1), 1e-6) ** 2
            w_tmp /= w_tmp.sum(1, keepdims=True)
            td_raw = (w_tmp * self.drift_var[i_tmp]).sum(1)

        td = (td_raw - self._drift_mean) / self._drift_std

        d_t = _pairwise(targets, self.xy)
        idx = np.argsort(d_t, axis=1)[:, :k]
        lc = self.xy[idx]
        ly = self.values[idx]
        lf = self.drift_norm[idx]

        ld = np.sqrt(((lc[:, :, None, :] - lc[:, None, :, :]) ** 2).sum(-1))
        gamma_mat = self.semivariogram(ld)
        diag = np.arange(k)
        gamma_mat[:, diag, diag] = 0.0

        K = np.zeros((m, k + 2, k + 2), dtype=float)
        K[:, :k, :k] = gamma_mat + np.eye(k)[None] * getattr(self, "_eff_reg", self.reg)
        K[:, :k, k] = 1.0
        K[:, k, :k] = 1.0
        K[:, :k, k + 1] = lf
        K[:, k + 1, :k] = lf
        # Regularisasi mikro pada blok Lagrange drift untuk mencegah singularitas saat lf konstan
        K[:, k + 1, k + 1] = -1e-4

        g_t = self.semivariogram(np.take_along_axis(d_t, idx, 1))
        rhs = np.zeros((m, k + 2, 1), dtype=float)
        rhs[:, :k, 0] = g_t
        rhs[:, k, 0] = 1.0
        rhs[:, k + 1, 0] = td

        try:
            sol = np.linalg.solve(K, rhs)[..., 0]
        except np.linalg.LinAlgError:
            sol = (np.linalg.pinv(K) @ rhs)[..., 0]

        w = sol[:, :k]
        preds = (w * ly).sum(1)
        var = np.maximum((w * g_t).sum(1) + sol[:, k] + sol[:, k + 1] * td, 0.0)
        return preds, var


class HybridRegressionKrigingModel:
    """
    Hybrid Regression-Kriging (Random Forest + Ordinary Kriging Residual).
    Menggabungkan pembelajaran tren non-linear Random Forest dengan interpolasi
    geostatistika Kriging pada residual spasialnya.
    """

    def __init__(self, n_estimators=60, max_depth=8, min_samples_leaf=2, k_neighbors=12, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.k_neighbors = k_neighbors
        self.random_state = random_state

    def fit(self, xy, values, drift=None):
        self.xy = np.asarray(xy, float)
        self.values = np.asarray(values, float)
        d = _pairwise(self.xy, self.xy)
        self._scale = max(float(d.max()) * 0.5, 5.0) if d.size else 10.0
        self._has_drift = drift is not None
        self._drift_obs = np.asarray(drift, float) if drift is not None else None

        X_feat = _build_spatial_features(self.xy, self._scale, self._drift_obs)
        self.rf = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_leaf=min(self.min_samples_leaf, max(1, len(self.values) // 4)),
            random_state=self.random_state,
            n_jobs=1,
        )
        self.rf.fit(X_feat, self.values)

        # Residual = nilai aktual - tren Random Forest
        trend_pred = self.rf.predict(X_feat)
        residuals = self.values - trend_pred
        self.kriging_resid = OrdinaryKrigingModel(k_neighbors=self.k_neighbors).fit(self.xy, residuals)
        return self

    def predict(self, targets, target_drift=None):
        targets = np.atleast_2d(np.asarray(targets, float))
        td = None
        if self._has_drift:
            if target_drift is not None:
                td = np.asarray(target_drift, float)
            else:
                k = min(self.k_neighbors, len(self.xy))
                d_tmp = _pairwise(targets, self.xy)
                i_tmp = np.argsort(d_tmp, axis=1)[:, :k]
                w_tmp = 1.0 / np.maximum(np.take_along_axis(d_tmp, i_tmp, 1), 1e-6) ** 2
                w_tmp /= w_tmp.sum(1, keepdims=True)
                td = (w_tmp * self._drift_obs[i_tmp]).sum(1)

        X_target = _build_spatial_features(targets, self._scale, td)
        trend_preds = self.rf.predict(X_target)
        resid_preds, resid_var = self.kriging_resid.predict(targets)
        preds = trend_preds + resid_preds
        return preds, resid_var


def build_model(xy, values, method="auto", drift=None, fast_cv=False):
    n = len(values)
    # Fallback aman saat titik terlalu sedikit
    if n < 4 or method == "idw":
        return "idw", InverseDistanceWeighting().fit(xy, values)
    if method == "kriging":
        return "kriging", OrdinaryKrigingModel().fit(xy, values)
    if method == "ked":
        return "ked", KrigingExternalDriftModel().fit(xy, values, drift=drift)
    # Default utama ("auto" atau "hybrid_rk"): Hybrid Regression-Kriging (RF + Kriging)
    n_est = 30 if fast_cv else 60
    return "hybrid_rk", HybridRegressionKrigingModel(n_estimators=n_est).fit(xy, values, drift=drift)


# ------------------------------------------------------------------
# Validasi Silang (5-Fold CV untuk n > 15, LOO untuk n <= 15) + Anomali
# ------------------------------------------------------------------
def cross_validate(xy, values, method, drift=None):
    n = len(values)
    if n < 4:
        return None, np.zeros(n)

    preds = np.zeros(n)
    if n <= 15:
        cv_mode = "LOO"
        for i in range(n):
            mask = np.arange(n) != i
            d_tr = drift[mask] if drift is not None else None
            d_te = drift[i:i + 1] if drift is not None else None
            _, mdl = build_model(xy[mask], values[mask], method, drift=d_tr, fast_cv=True)
            preds[i] = mdl.predict(xy[i:i + 1], target_drift=d_te)[0][0]
    else:
        cv_mode = "5-Fold CV"
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        for tr_idx, te_idx in kf.split(xy):
            d_tr = drift[tr_idx] if drift is not None else None
            d_te = drift[te_idx] if drift is not None else None
            _, mdl = build_model(xy[tr_idx], values[tr_idx], method, drift=d_tr, fast_cv=True)
            preds[te_idx] = mdl.predict(xy[te_idx], target_drift=d_te)[0]

    resid = values - preds
    mae = float(np.mean(np.abs(resid)))
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    ss_tot = float(np.sum((values - values.mean()) ** 2))
    r2 = float(1 - np.sum(resid ** 2) / ss_tot) if ss_tot > 1e-9 else None
    acc = float(max(0.0, 100.0 - np.mean(np.abs(resid) / np.maximum(values, 1e-6)) * 100))
    return {
        "cv_mode": cv_mode,
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 4) if r2 is not None else None,
        "akurasi_persen": round(acc, 2),
        "n_sampel": int(n),
    }, resid


# ------------------------------------------------------------------
# API utama
# ------------------------------------------------------------------
def interpolate(samples, bbox=None, clip_fn=None, method="auto", max_cells=1600):
    """
    samples : list of dict {lon, lat, brix, id, (opsional) ndvi/drift}
    bbox    : (minlon, minlat, maxlon, maxlat) area grid; default = bbox sampel + buffer
    clip_fn : callable(lon, lat) -> bool, untuk memotong grid ke poligon blok/lahan
    method  : 'auto' (= hybrid_rk), 'hybrid_rk', 'ked', 'kriging', 'idw'
    Returns dict siap JSON (GeoJSON grid sel + anomali + metrik + komparasi KED vs Hybrid).
    """
    if not samples:
        return {
            "success": True,
            "grid": {"type": "FeatureCollection", "features": []},
            "anomalies": {"type": "FeatureCollection", "features": []},
            "summary": None,
            "validation": None,
            "comparison": None,
            "method": None,
            "method_label": None,
            "message": "Belum ada titik sampel Brix pada area ini",
        }

    lon = np.array([s["lon"] for s in samples], float)
    lat = np.array([s["lat"] for s in samples], float)
    val = np.array([s["brix"] for s in samples], float)
    lon0, lat0 = float(lon.mean()), float(lat.mean())
    xy = lonlat_to_xy(lon, lat, lon0, lat0)

    # Ekstrak drift eksternal (NDVI) bila seluruh titik memilikinya
    drift = None
    if all(s.get("ndvi") is not None for s in samples):
        drift = np.array([float(s["ndvi"]) for s in samples], float)

    used, model = build_model(xy, val, method, drift=drift)

    if bbox is None:
        pad_lon = max((lon.max() - lon.min()) * 0.15, 0.0005)
        pad_lat = max((lat.max() - lat.min()) * 0.15, 0.0005)
        bbox = (lon.min() - pad_lon, lat.min() - pad_lat, lon.max() + pad_lon, lat.max() + pad_lat)
    minx, miny, maxx, maxy = bbox

    # Resolusi adaptif: sel persegi (dalam meter) dengan jumlah sel <= max_cells
    w_m = max((maxx - minx) * 111320 * math.cos(math.radians(lat0)), 1.0)
    h_m = max((maxy - miny) * 110540, 1.0)
    cell_m = max(math.sqrt(w_m * h_m / max_cells), 2.0)
    nx = max(int(math.ceil(w_m / cell_m)), 2)
    ny = max(int(math.ceil(h_m / cell_m)), 2)
    dlon = (maxx - minx) / nx
    dlat = (maxy - miny) / ny

    cx = minx + dlon * (np.arange(nx) + 0.5)
    cy = miny + dlat * (np.arange(ny) + 0.5)
    GX, GY = np.meshgrid(cx, cy)
    glon, glat = GX.ravel(), GY.ravel()
    if clip_fn is not None:
        keep = np.array([clip_fn(a, b) for a, b in zip(glon, glat)], bool)
        if keep.any():
            glon, glat = glon[keep], glat[keep]

    preds, var = model.predict(lonlat_to_xy(glon, glat, lon0, lat0))
    preds = np.clip(preds, 0.0, 30.0)

    features = []
    for a, b, p, v in zip(glon, glat, preds, var):
        hx, hy = dlon / 2, dlat / 2
        features.append({
            "type": "Feature",
            "properties": {
                "brix": round(float(p), 2),
                "std": round(float(np.sqrt(v)), 3),
                "zona": zone_of(p),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [a - hx, b - hy], [a + hx, b - hy], [a + hx, b + hy], [a - hx, b + hy], [a - hx, b - hy]
                ]],
            },
        })

    # Validasi metode aktif & komparasi 2 algoritma utama (Hybrid RF+Kriging vs KED)
    validation, resid = cross_validate(xy, val, used, drift=drift)
    comparison = None
    if len(val) >= 4:
        comp = {}
        for m_key in ("hybrid_rk", "ked"):
            if m_key == used:
                comp[m_key] = validation
            else:
                v_other, _ = cross_validate(xy, val, m_key, drift=drift)
                comp[m_key] = v_other
        comparison = comp

    anomalies = []
    if validation is not None:
        sd = float(np.std(resid)) or 1.0
        for s, r in zip(samples, resid):
            z = r / sd
            if abs(z) >= 2.0:
                anomalies.append({
                    "type": "Feature",
                    "properties": {
                        "id": s.get("id"),
                        "brix_aktual": round(s["brix"], 2),
                        "brix_estimasi": round(s["brix"] - float(r), 2),
                        "z_score": round(float(z), 2),
                        "jenis": (
                            "Brix jauh di bawah sekitar (indikasi stres/penyakit)"
                            if z < 0
                            else "Brix jauh di atas sekitar (cek ulang pengukuran)"
                        ),
                    },
                    "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
                })

    zones = [zone_of(p) for p in preds]
    total = max(len(zones), 1)
    summary = {
        "jumlah_sel": len(features),
        "ukuran_sel_meter": round(cell_m, 1),
        "brix_min": round(float(preds.min()), 2) if len(preds) else None,
        "brix_max": round(float(preds.max()), 2) if len(preds) else None,
        "brix_rata": round(float(preds.mean()), 2) if len(preds) else None,
        "persen_zona": {z: round(zones.count(z) / total * 100, 1) for z in ("rendah", "sedang", "tinggi")},
        "jumlah_anomali": len(anomalies),
    }

    params = None
    if used == "ked":
        params = {
            "semivariogram": "gaussian",
            "nugget": round(model.nugget, 4),
            "sill": round(model.sill, 4),
            "range_meter": round(model.range_val, 1),
            "k_neighbors": model.k_neighbors,
            "drift_source": "ndvi" if drift is not None else "spatial_trend_surface",
        }
    elif used == "hybrid_rk":
        params = {
            "rf_estimators": model.n_estimators,
            "rf_max_depth": model.max_depth,
            "residual_nugget": round(model.kriging_resid.nugget, 4),
            "residual_sill": round(model.kriging_resid.sill, 4),
            "residual_range_meter": round(model.kriging_resid.range_val, 1),
            "k_neighbors": model.k_neighbors,
        }
    elif used == "kriging":
        params = {
            "semivariogram": "spherical",
            "nugget": round(model.nugget, 4),
            "sill": round(model.sill, 4),
            "range_meter": round(model.range_val, 1),
            "k_neighbors": model.k_neighbors,
        }

    return {
        "success": True,
        "method": used,
        "method_label": METHOD_LABELS.get(used, used),
        "parameters": params,
        "grid": {"type": "FeatureCollection", "features": features},
        "anomalies": {"type": "FeatureCollection", "features": anomalies},
        "summary": summary,
        "validation": validation,
        "comparison": comparison,
    }


def daily_weather_update(mean_brix, weather):
    """
    Simulasi pembaruan kematangan harian (port engine GDD notebook).
    weather: {temp_max, temp_min, rainfall_mm, sunshine_hours, days}
    """
    t_max = float(weather.get("temp_max", 33.0))
    t_min = float(weather.get("temp_min", 23.0))
    rain = float(weather.get("rainfall_mm", 0.0))
    sun = float(weather.get("sunshine_hours", 8.0))
    days = max(int(weather.get("days", 1)), 1)

    gdd = max(0.0, (t_max + t_min) / 2.0 - 12.0)          # base temp tebu 12°C
    gain = 0.012 * gdd                                     # akumulasi sukrosa
    if rain < 2 and sun >= 7:
        gain += 0.08                                       # dry-down
    dilution = 0.015 * rain if rain > 10 else 0.0          # pengenceran nira
    delta = (gain - dilution) * days
    new_brix = float(np.clip(mean_brix + delta, 0.0, 26.0))
    return {
        "gdd_harian": round(gdd, 2),
        "delta_brix": round(delta, 3),
        "brix_awal": round(float(mean_brix), 2),
        "brix_proyeksi": round(new_brix, 2),
        "zona_proyeksi": zone_of(new_brix),
        "catatan": (
            "Hujan lebat menurunkan Brix sementara (pengenceran)"
            if dilution > gain
            else "Kondisi mendukung akumulasi sukrosa"
        ),
    }
