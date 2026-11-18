# 🎧 Bot de Recomendaciones Musicales para Telegram

Bot de Telegram que recomienda música de dos formas:

1. **Por canción:** le dices una canción que te gusta y te recomienda **5 canciones parecidas**, del **mismo idioma** y de la **misma época**.
2. **Por artista:** le dices un artista y te recomienda **5 canciones de sus mejores álbumes**.

Bot: [t.me/musica_elcojo_bot](https://t.me/musica_elcojo_bot)

---

## 🛠️ Tecnologías utilizadas

| Librería | Para qué se usa |
|----------|-----------------|
| **Python 3.11+** | Lenguaje principal |
| **python-telegram-bot** | Conectar el bot con Telegram (comandos, botones y mensajes) |
| **requests** | Consultar la API pública de **Deezer** (gratis, no necesita clave) |
| **lingua-language-detector** | Detectar el idioma de las canciones a partir de sus títulos |

---

## ⚙️ Cómo funciona

### Opción 1: Recomendar por canción

1. Busca la canción en Deezer y obtiene su **año de lanzamiento**.
2. Detecta el **idioma** juntando los títulos de las canciones y álbumes más populares del artista (con más texto el detector acierta más).
3. Pide a Deezer los **artistas relacionados**, que vienen ordenados del más parecido al menos parecido según lo que escuchan sus usuarios.
4. Revisa cada artista relacionado y aplica dos filtros:
   - **Idioma:** si canta en otro idioma, se descarta.
   - **Época:** la canción puede ser **máximo 2 años más nueva** que la original. Si salió antes, no hay límite.
5. Toma una canción por artista hasta completar 5. Si no alcanza, completa con otras canciones del mismo artista que cumplan los filtros.

### Opción 2: Recomendar por artista

1. Trae los álbumes del artista e ignora sencillos, EPs y versiones repetidas (Deluxe, Remastered, etc.).
2. Ordena los álbumes por **número de fans en Deezer** (los mejores álbumes).
3. Toma la **canción más popular** de cada uno de los 5 mejores álbumes.

---

## 📦 Instalación

```powershell
# 1. Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar las librerías
pip install -r requirements.txt

# 3. Configurar el token del bot (se obtiene con @BotFather)
$env:TELEGRAM_TOKEN="tu_token_aqui"

# 4. Ejecutar el bot
python bot.py
```

---

## 💬 Uso

| Comando | Ejemplo | Resultado |
|---------|---------|-----------|
| `/start` | `/start` | Muestra el menú con botones |
| `/cancion` | `/cancion Tusa Karol G` | 5 canciones parecidas |
| `/artista` | `/artista Soda Stereo` | 5 canciones de sus mejores álbumes |
| `/ayuda` | `/ayuda` | Explica cómo usar el bot |

También se puede tocar un botón del menú y luego escribir solo el nombre.

---

## 📁 Estructura del proyecto

```
machine-learning-Bot-telegram/
├── bot.py             # Comandos, botones y mensajes de Telegram
├── musica.py          # Lógica de recomendaciones (Deezer + detección de idioma)
├── requirements.txt   # Librerías necesarias
├── Indicaciones.txt   # Pasos rápidos para ejecutar el bot
└── README.md
```

---

## ⚠️ Limitaciones

- El año que entrega Deezer es el del álbum, por lo que una canción que aparece en un recopilatorio reciente puede verse más nueva.
- El idioma se detecta con los títulos y no con la letra, así que puede fallar con títulos muy cortos o que son nombres propios.

---

## 🔒 Seguridad

- El token **no** se guarda en el código: se lee de la variable de entorno `TELEGRAM_TOKEN`.
- Si el token se expone, se debe revocar en [@BotFather](https://t.me/BotFather).

---

## 👤 Autor

- **David Muñoz** — Tecnología en Análisis y Desarrollo de Software (ADSO), SENA Regional Antioquia, ficha 3228140
