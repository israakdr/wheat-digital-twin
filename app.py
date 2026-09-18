import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="التوأم الرقمي للقمح", page_icon="🌾", layout="wide")

st.title("🌾 التوأم الرقمي للقمح في الجزائر")
st.markdown("### منصة ذكية لدعم قرار الري")

st.sidebar.header("⚙️ الإعدادات")

wilaya = st.sidebar.selectbox(
    "اختر الولاية",
    ["تيارت", "سطيف", "بسكرة", "الوادي"]
)

coords = {
    "تيارت": (35.37, 1.32),
    "سطيف": (36.19, 5.41),
    "بسكرة": (34.85, 5.73),
    "الوادي": (33.37, 6.87)
}

lat, lon = coords[wilaya]

date = st.sidebar.date_input("اختر التاريخ", pd.Timestamp.now())

if st.sidebar.button("احسب التوصية", type="primary"):
    with st.spinner("⏳ جاري سحب البيانات..."):
        url = (
            f"https://power.larc.nasa.gov/api/temporal/daily/point"
            f"?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M"
            f"&community=AG"
            f"&longitude={lon}"
            f"&latitude={lat}"
            f"&start={date.strftime('%Y%m%d')}"
            f"&end={date.strftime('%Y%m%d')}"
            f"&format=JSON"
        )
        
        response = requests.get(url)
        data = response.json()
        
        params = data['properties']['parameter']
        tmean = params['T2M'][date.strftime('%Y%m%d')]
        tmax = params['T2M_MAX'][date.strftime('%Y%m%d')]
        tmin = params['T2M_MIN'][date.strftime('%Y%m%d')]
        rain = params['PRECTOTCORR'][date.strftime('%Y%m%d')]
        humidity = params['RH2M'][date.strftime('%Y%m%d')]
        
        tdiff = max(tmax - tmin, 0)
        et0 = 0.0023 * (tmean + 17.8) * np.sqrt(tdiff) * 15
        et0 = max(et0, 0)
        
        kc = 0.7
        etc = et0 * kc
        deficit = max(etc - rain, 0)
        
        if deficit < 2:
            recommendation = "✅ لا تسقِ اليوم"
            color = "green"
        elif deficit < 5:
            recommendation = "⚠️ راقب، قد تحتاج للري قريباً"
            color = "orange"
        else:
            recommendation = "🚨 اسقِ اليوم"
            color = "red"
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🌡️ متوسط الحرارة", f"{tmean:.1f}°C")
        st.metric("💧 الأمطار", f"{rain:.1f} mm")
    
    with col2:
        st.metric("🔥 أعلى حرارة", f"{tmax:.1f}°C")
        st.metric("💨 الرطوبة", f"{humidity:.1f}%")
    
    with col3:
        st.metric("🌱 احتياج القمح", f"{etc:.2f} mm")
        st.metric("📉 العجز المائي", f"{deficit:.2f} mm")
    
    st.markdown("---")
    st.markdown(f"### التوصية: :{color}[{recommendation}]")
    
    with st.expander("📖 كيف حسبنا التوصية؟"):
        st.write(f"""
        - **النتح المرجعي (ET0)**: {et0:.2f} mm
        - **معامل المحصول (Kc)**: {kc}
        - **احتياج القمح (ETc)**: {etc:.2f} mm
        - **الأمطار**: {rain:.2f} mm
        - **العجز المائي**: {deficit:.2f} mm
        """)

else:
    st.info("👈 اختر الولاية والتاريخ، ثم اضغط 'احسب التوصية'")
    # ============================================
# المحاكاة ثلاثية الأبعاد للحقل
# ============================================

import plotly.graph_objects as go

st.markdown("---")
st.markdown("## 🗺️ محاكاة الحقل ثلاثي الأبعاد")

# إعدادات الحقل
grid_size = 10  # حقل 10×10
np.random.seed(42)

# محاكاة حالة كل خلية (رطوبة التربة)
# في الواقع، هذه البيانات تأتي من الأقمار الصناعية (NDVI)
soil_moisture = np.random.uniform(0.2, 0.9, (grid_size, grid_size))

# تصنيف الحالة
def classify_cell(moisture):
    if moisture < 0.3:
        return "جاف (يحتاج ري)"
    elif moisture < 0.6:
        return "متوسط"
    else:
        return "رطب (جيد)"

# إنشاء خريطة الحقل
fig = go.Figure(data=[
    go.Surface(
        z=soil_moisture,
        colorscale=[
            [0.0, 'red'],      # جاف
            [0.5, 'yellow'],   # متوسط
            [1.0, 'green']     # رطب
        ],
        colorbar=dict(title="رطوبة التربة"),
        hovertemplate="الموقع: (%{x}, %{y})<br>الرطوبة: %{z:.2f}<extra></extra>"
    )
])

fig.update_layout(
    title="🗺️ خريطة رطوبة التربة في الحقل",
    scene=dict(
        xaxis_title="الموقع X",
        yaxis=dict(title="الموقع Y"),
        zaxis=dict(title="رطوبة التربة"),
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
    ),
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# ============================================
# تحليل الحقل
# ============================================

st.markdown("### 📊 تحليل الحقل")

col1, col2, col3 = st.columns(3)

dry_cells = np.sum(soil_moisture < 0.3)
medium_cells = np.sum((soil_moisture >= 0.3) & (soil_moisture < 0.6))
wet_cells = np.sum(soil_moisture >= 0.6)

with col1:
    st.metric("🔴 خلايا جافة", f"{dry_cells} / {grid_size*grid_size}")

with col2:
    st.metric("🟡 خلايا متوسطة", f"{medium_cells} / {grid_size*grid_size}")

with col3:
    st.metric("🟢 خلايا رطبة", f"{wet_cells} / {grid_size*grid_size}")

# ============================================
# التوصية العامة
# ============================================

if dry_cells > grid_size * grid_size * 0.3:
    st.error("🚨 أكثر من 30% من الحقل جاف! يُنصح بالري الفوري.")
elif dry_cells > grid_size * grid_size * 0.15:
    st.warning("⚠️ بعض المناطق جافة. راقب الحقل عن قرب.")
else:
    st.success("✅ الحقل في حالة جيدة. لا حاجة للري الآن.")
