import io
import zipfile
import pandas as pd
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Convertidor de Fondos a Blanco", layout="centered")

st.title("🖼️ Procesador de Imágenes Masivo")
st.write("Sube tu archivo CSV con los enlaces de Sellbrite para convertirlos a fondo blanco y descargarlos en un ZIP.")

archivo_subido = st.file_uploader("Elige tu archivo CSV", type=["csv"])

if archivo_subido is not None:
    try:
        df = pd.read_csv(archivo_subido)
        df = df.dropna(how='all')
        
        if len(df) == 0:
            st.error("El archivo CSV está vacío.")
        else:
            col_nombre = df.columns[0]
            col_link = df.columns[1]
            
            st.success(f"¡Archivo cargado con éxito! Se encontraron {len(df)} filas para procesar.")
            
            if st.button("🚀 Comenzar Conversión Masiva"):
                barra_progreso = st.progress(0)
                texto_estado = st.empty()
                buffer_zip = io.BytesIO()
                con_errores = 0
                con_exitos = 0
                
                with zipfile.ZipFile(buffer_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for index, fila in df.iterrows():
                        progreso = (index + 1) / len(df)
                        barra_progreso.progress(progreso)
                        
                        nombre_imagen = str(fila[col_nombre]).strip()
                        url_imagen = str(fila[col_link]).strip()
                        
                        if not url_imagen.startswith("http"):
                            continue
                            
                        texto_estado.text(f"Procesando ({index+1}/{len(df)}): {nombre_imagen}")
                        
                        try:
                            respuesta = requests.get(url_imagen, timeout=15)
                            if respuesta.status_code == 200:
                                img = Image.open(io.BytesIO(respuesta.content)).convert("RGBA")
                                fondo_blanco = Image.new("RGBA", img.size, "WHITE")
                                imagen_final = Image.alpha_composite(fondo_blanco, img).convert("RGB")
                                
                                buffer_imagen = io.BytesIO()
                                imagen_final.save(buffer_imagen, format="JPEG", quality=92)
                                buffer_imagen.seek(0)
                                
                                zipf.writestr(f"{nombre_imagen}.jpg", buffer_imagen.read())
                                con_exitos += 1
                            else:
                                con_errores += 1
                        except Exception:
                            con_errores += 1
                
                barra_progreso.empty()
                texto_estado.empty()
                
                if con_exitos > 0:
                    st.success(f"¡Proceso terminado! {con_exitos} imágenes procesadas con éxito.")
                    if con_errores > 0:
                        st.warning(f"Nota: {con_errores} enlaces no pudieron ser descargados.")
                    
                    buffer_zip.seek(0)
                    st.download_button(
                        label="📦 Descargar archivo ZIP",
                        data=buffer_zip.read(),
                        file_name="imagenes_fondo_blanco.zip",
                        mime="application/zip"
                    )
                else:
                    st.error("No se pudo procesar ninguna imagen del archivo. Verifica los enlaces.")
                    
    except Exception as e:
        st.error(f"Ocurrió un error leyendo el archivo CSV: {e}")
