<div align="center">

# 🇱🇺 🇩🇰 🇫🇷 TrioLingo

**Aprende luxemburgués, danés y francés desde el español, con una webapp que corre en tu propio equipo.**

Sin cuentas, sin anuncios y sin nube: tu progreso se queda en tu equipo.

![Rust](https://img.shields.io/badge/hecho_con-Rust-b7410e?logo=rust&logoColor=white)
![Web](https://img.shields.io/badge/interfaz-web-2b7a62)
![Plataformas](https://img.shields.io/badge/macOS_·_Linux_·_Windows-servidor-555)
![Móvil](https://img.shields.io/badge/móvil_y_tablet-por_wifi-555)
![Idioma de la interfaz](https://img.shields.io/badge/interfaz-español-c60b1e)

[Qué trae](#-qué-trae) ·
[Inicio rápido](#-inicio-rápido) ·
[Instalación paso a paso](#-instalación-paso-a-paso) ·
[Móvil y tablet](#-usarlo-desde-el-móvil-o-la-tablet) ·
[Tus datos](#-tus-datos) ·
[Problemas frecuentes](#-problemas-frecuentes)

</div>

---

## ✨ Qué trae

| Idioma | Niveles | Contenido |
| --- | --- | --- |
| 🇱🇺 **Luxemburgués** | A1 → C2 | 200 semanas · 1.000 lecciones · ~13.000 tareas · audio en cada diálogo |
| 🇩🇰 **Danés** | A1 → C2 | 200 semanas · 1.000 lecciones · ~13.000 tareas · audio en cada diálogo |
| 🇫🇷 **Francés** | A1 → A2 | 8 situaciones prácticas para vivir y trabajar en Luxemburgo (pedir que te hablen en francés, comprar, alquilar, una entrevista…) |

Cada semana tiene cinco días de trabajo con tareas variadas:

- 🎧 **Escuchar.** Diálogos con audio, frase a frase o la conversación entera, y preguntas de comprensión.
- ✍️ **Escribir.** Dictados, traducciones, huecos para completar y redacciones con un modelo para compararte.
- 🗣️ **Hablar.** Puedes grabarte, escucharte y comparar con la referencia. Con los modelos de voz opcionales, la transcripción se hace en tu equipo.
- 📚 **Gramática y vocabulario.** Explicaciones breves y tarjetas con **repaso espaciado** que vuelven cuando toca.
- 📈 **Progreso.** Ves tus tareas hechas, el tiempo de estudio y tus grabaciones guardadas, y puedes retomar cada lección donde la dejaste.
- 📴 **Funciona sin conexión.** Una vez compilada, la app no necesita internet.

> [!NOTE]
> **Estado del contenido:** las semanas B1–C2, más parte de A1 y A2, son **borradores** (170 de 200 por idioma) a la espera de revisión por hablantes nativos. Las dudas concretas están en [`content/enrichment/REVISION.md`](content/enrichment/REVISION.md). Los niveles siguen el MCER como orientación, pero la app no acredita ningún nivel.

---

## 🚀 Inicio rápido

TrioLingo es **una webapp con un pequeño servidor**. Lo enciendes en un ordenador (Mac, Linux o Windows) y lo usas desde el navegador de ese ordenador o de cualquier móvil o tablet conectado a tu wifi.

```sh
git clone https://github.com/rynethdev/TrioLingo.git
cd TrioLingo
cargo build --release
./target/release/idiomas --open
```

Se abre **http://localhost:8787** en el navegador. Elige idioma y empieza por **Hoy**. 🎉

Si `cargo` no existe o la compilación falla, sigue las instrucciones de tu sistema 👇

---

## 🧰 Instalación paso a paso

Solo hace falta compilar una vez; las siguientes veces basta con arrancar la app. La primera compilación tarda unos **3–10 minutos** según el equipo. La descarga pesa unos **150 MB**, porque incluye todos los audios del curso.

<details open>
<summary><b>🍎 macOS</b> (probado en Apple Silicon)</summary>

**1. Instala las herramientas** (en la app Terminal):

```sh
xcode-select --install                                           # compilador de Apple
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"   # Homebrew, si no lo tienes
brew install cmake
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh  # Rust (acepta las opciones por defecto)
```

Cierra y vuelve a abrir la Terminal para que encuentre `cargo`.

**2. Descarga y compila:**

```sh
git clone https://github.com/rynethdev/TrioLingo.git
cd TrioLingo
cargo build --release
```

**3. Arranca la app:**

```sh
./target/release/idiomas --open
```

💡 Si prefieres abrirla con doble clic, ejecuta `./scripts/package-mac.sh`. Eso crea `dist/Abrir Idiomas.command`, que puedes abrir con doble clic desde el Finder.

</details>

<details>
<summary><b>🐧 Linux</b> (debería funcionar; aún sin probar: si algo falla, abre un issue)</summary>

**1. Instala las herramientas:**

```sh
# Debian / Ubuntu / Mint
sudo apt update && sudo apt install -y build-essential cmake clang libclang-dev git curl

# Fedora
sudo dnf install -y gcc gcc-c++ cmake clang clang-devel git curl

# Arch
sudo pacman -S --needed base-devel cmake clang git curl
```

Después instala Rust:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

**2. Descarga y compila:**

```sh
git clone https://github.com/rynethdev/TrioLingo.git
cd TrioLingo
cargo build --release
```

**3. Arranca la app:**

```sh
./target/release/idiomas --open
```

`--open` usa `xdg-open` para abrir el navegador. En un servidor sin escritorio, omítelo y entra desde otro dispositivo (mira [Móvil y tablet](#-usarlo-desde-el-móvil-o-la-tablet)).

</details>

<details>
<summary><b>🪟 Windows 10 / 11</b> (todavía sin probar: si algo falla, abre un issue)</summary>

**1. Instala las herramientas.** Abre **PowerShell** y ejecuta:

```powershell
winget install --id Git.Git -e
winget install --id Kitware.CMake -e
winget install --id LLVM.LLVM -e
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
winget install --id Rustlang.Rustup -e
```

Cierra PowerShell y ábrelo de nuevo para que reconozca los programas nuevos.

**2. Descarga y compila:**

```powershell
git clone https://github.com/rynethdev/TrioLingo.git
cd TrioLingo
cargo build --release
```

Si da un error sobre `libclang`, indícale dónde está LLVM y compila otra vez:

```powershell
$env:LIBCLANG_PATH = "C:\Program Files\LLVM\bin"
cargo build --release
```

**3. Arranca la app:**

```powershell
.\target\release\idiomas.exe --open
```

</details>

### ▶️ Las siguientes veces

Entra en la carpeta `TrioLingo` y ejecuta lo mismo que en el paso 3:

| Sistema | Comando |
| --- | --- |
| macOS / Linux | `./target/release/idiomas --open` |
| Windows | `.\target\release\idiomas.exe --open` |

Mantén abierta la ventana de la terminal mientras estudias. Para apagar la app, pulsa **Ctrl + C** o cierra esa ventana.

### 🔄 Actualizar a la última versión

```sh
git pull
cargo build --release
```

Tu progreso no se pierde al actualizar, porque se guarda fuera de la carpeta del proyecto.

---

## 📱 Usarlo desde el móvil o la tablet

Por seguridad, la app solo acepta conexiones **desde el mismo equipo** salvo que la abras a tu red. Para estudiar desde el móvil o la tablet:

**1.** En el ordenador, arranca la app con `IDIOMAS_HOST=0.0.0.0`:

| Sistema | Comando |
| --- | --- |
| macOS / Linux | `IDIOMAS_HOST=0.0.0.0 ./target/release/idiomas` |
| Windows (PowerShell) | `$env:IDIOMAS_HOST="0.0.0.0"; .\target\release\idiomas.exe` |
| Windows (cmd) | `set "IDIOMAS_HOST=0.0.0.0" && .\target\release\idiomas.exe` |

**2.** La terminal muestra la dirección que debes usar, por ejemplo:

```
Idiomas · http://localhost:8787
Desde otro dispositivo de tu red: http://192.168.1.20:8787
```

**3.** Abre esa dirección (`http://192.168.1.20:8787`) en el navegador del móvil. Para tenerla a mano, usa *Compartir → Añadir a pantalla de inicio*.

Ten en cuenta lo siguiente:

- 📶 El móvil y el ordenador tienen que estar **en la misma wifi**, y el ordenador tiene que seguir encendido con la app abierta.
- 🛡️ Si macOS o Windows preguntan si quieres **permitir conexiones entrantes**, responde que sí.
- 👥 **Hay un solo perfil.** Todos los dispositivos comparten el mismo progreso, así que es ideal para una persona con varios aparatos.
- 🔒 Cualquiera en tu wifi podría abrir la app. Úsalo en redes de confianza, como la de tu casa, y no en una wifi pública.
- 🎙️ **El micrófono solo funciona en el propio ordenador.** Los navegadores bloquean el micrófono en páginas `http://` que no sean `localhost`. Desde el móvil se puede escuchar y hacer todas las tareas, pero no grabarse.

---

## 💾 Tus datos

Tu progreso, tus respuestas y tus grabaciones se guardan en **un solo archivo** (`progress.sqlite3`) **fuera** de la carpeta del proyecto. Por eso nunca se suben a git, y cada persona que descarga TrioLingo empieza de cero.

| Sistema | Ubicación |
| --- | --- |
| 🍎 macOS | `~/Library/Application Support/Idiomas/` |
| 🐧 Linux | `~/.local/share/idiomas/` (o `$XDG_DATA_HOME/idiomas/`) |
| 🪟 Windows | `%APPDATA%\Idiomas\` |

- **Copia de seguridad:** con la app cerrada, copia `progress.sqlite3` a otro sitio.
- **Empezar de cero:** con la app cerrada, borra ese archivo, o muévelo si quieres conservarlo.
- **Otra carpeta:** usa la variable `IDIOMAS_DATA_DIR`. Así puedes tener, por ejemplo, un perfil por persona en el mismo equipo:
  ```sh
  IDIOMAS_DATA_DIR=~/idiomas-ana IDIOMAS_PORT=8788 ./target/release/idiomas --open
  ```

---

## ⚙️ Configuración

Todo es opcional y se configura con variables de entorno al arrancar:

| Variable | Valor por defecto | Para qué sirve |
| --- | --- | --- |
| `IDIOMAS_PORT` | `8787` | Puerto del servidor; cámbialo si el 8787 ya está ocupado. |
| `IDIOMAS_HOST` | `127.0.0.1` | Usa `0.0.0.0` para entrar desde otros dispositivos de tu red. |
| `IDIOMAS_DATA_DIR` | según el sistema ([ver arriba](#-tus-datos)) | Carpeta del progreso. |
| `IDIOMAS_VOICES_DIR` | `voices/` junto al ejecutable | Carpeta de los modelos de transcripción. |
| `OPENAI_API_KEY` | (vacía) | Activa la *conversación libre* (ver abajo). |

### 🎙️ Transcripción de voz (opcional)

Puedes grabarte y escucharte sin instalar nada más. Para que la app **transcriba** lo que dices, en tu equipo y sin internet, hacen falta los modelos de voz (`lb.bin`, `da.bin`, ~250 MB), que no van en el repositorio por su tamaño.

Para generarlos (macOS o Linux, con Python 3.11, [uv](https://docs.astral.sh/uv/) y FFmpeg instalados):

```sh
./scripts/prepare-voice.sh       # crea dist/voices/ (también regenera los audios: tarda bastante)
IDIOMAS_VOICES_DIR=dist/voices ./target/release/idiomas --open
```

### 💬 Conversación libre (opcional)

Si quieres practicar con respuestas y correcciones escritas generadas por IA:

1. Arranca la app con `OPENAI_API_KEY` configurada, por ejemplo `OPENAI_API_KEY=sk-... ./target/release/idiomas --open`.
2. Actívala en **Ajustes**.

La app solo envía a la API de OpenAI tu respuesta confirmada y hasta tres turnos recientes. Todo lo demás sigue siendo local.

---

## 🧭 Cómo estudiar

1. En **Hoy** abre la siguiente lección. Cada semana tiene cinco días: escucha, vocabulario, gramática, habla y lectura/escritura.
2. Escucha con **▶ Escuchar la conversación** o frase a frase. Después responde, escribe y compárate con el modelo. Con **← Anterior** puedes volver a tareas que ya hiciste.
3. Al terminar una lección, sus expresiones pasan a **Vocabulario**. Repasa las tarjetas pendientes cada día: los intervalos se ajustan a cómo las recuerdas.
4. En **Práctica** encontrarás simulaciones, controles de nivel y pronunciación.
5. Para **francés**, elige 🇫🇷 *Francés* en el selector de idioma y entra en **Práctica**: ahí están sus 8 situaciones.

---

## 🆘 Problemas frecuentes

<details>
<summary><b><code>cargo: command not found</code></b></summary>

Rust no está instalado, o la terminal no lo encuentra todavía. Instálalo con [rustup](https://rustup.rs) y **abre una terminal nueva**. En Linux o macOS también puedes ejecutar `source "$HOME/.cargo/env"`.
</details>

<details>
<summary><b>La compilación falla con <code>cmake</code>, <code>libclang</code> o <code>clang</code></b></summary>

El motor de transcripción (whisper.cpp) se compila junto con la app y necesita CMake y Clang. Instala los paquetes de tu sistema que aparecen en [Instalación paso a paso](#-instalación-paso-a-paso). En Windows, además, define `LIBCLANG_PATH` como se explica allí.
</details>

<details>
<summary><b><code>Address already in use</code>: el puerto está ocupado</b></summary>

Ya hay otra copia de la app (u otro programa) usando el 8787. Cierra la otra ventana, o arranca en otro puerto:

```sh
IDIOMAS_PORT=8788 ./target/release/idiomas --open
```
</details>

<details>
<summary><b>El móvil no carga la página</b></summary>

- Comprueba que arrancaste la app con `IDIOMAS_HOST=0.0.0.0` y que usas la IP que muestra la terminal, no `localhost`.
- El móvil tiene que estar en la misma wifi (no en datos móviles ni en una red de invitados).
- Revisa el cortafuegos del ordenador y permite conexiones entrantes para `idiomas`.
</details>

<details>
<summary><b>No suena el audio</b></summary>

Sube el volumen y desactiva el modo silencio del móvil. Si sigue sin sonar, recarga la página (Ctrl/Cmd + R). Los audios van incluidos en la app, así que no necesitan internet.
</details>

<details>
<summary><b>Página en blanco o <code>403 Forbidden</code></b></summary>

Entra por `http://localhost:8787` (o por la IP que muestra la terminal en modo red). Por seguridad, la app rechaza nombres de dominio y peticiones que vienen de otras páginas web.
</details>

---

## 🛠️ Desarrollo

```
src/        servidor en Rust (Axum + SQLite)
web/        interfaz (HTML, CSS y JavaScript sin dependencias) y audios del curso
content/    contenido del curso en JSON
scripts/    generación del curso, del audio y auditoría
tests/      pruebas del contenido (Python)
```

El contenido y la interfaz **se incrustan en el ejecutable** al compilar. Después de cambiar algo en `content/` o `web/`, ejecuta `cargo build --release` y reinicia la app.

Flujo para modificar el curso:

```sh
python3 scripts/build-upper-expansion.py    # o build-a1-/build-a2-expansion.py
python3 scripts/build-course.py             # genera content/course.json
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/audit-course.py             # integridad, audio y repetición
cargo test
```

- Las escenas base están en `content/scenes.json` y `content/itinerary.json`, y el francés en `content/french.json`.
- El material extra de B1–C2 (segundo diálogo, gramática, vocabulario y transferencia) está en `content/enrichment/wNNN.json`. Valídalo con `python3 scripts/check-enrichment.py`.
- Para generar los audios que falten: `.build/voice-env/bin/python scripts/generate-audio.py --upper-expansion --missing da`. Genera un idioma cada vez para no agotar la memoria. Antes hay que ejecutar `./scripts/prepare-voice.sh` una vez.

¿Hablas luxemburgués o danés? La revisión de los borradores es la ayuda más valiosa que puedes dar: empieza por [`content/enrichment/REVISION.md`](content/enrichment/REVISION.md). 🙏

---

## 🙌 Créditos

- Voz sintética en luxemburgués: [VITS2 Claude](https://huggingface.co/ZLSCompLing/VITS2-Claude), del Zenter fir d'Lëtzebuerger Sprooch (MIT).
- Voz sintética en danés: [Piper Talesyntese](https://huggingface.co/rhasspy/piper-voices/blob/main/da/da_DK/talesyntese/medium/MODEL_CARD).
- Transcripción en luxemburgués: [LuxASR Base](https://huggingface.co/unilux/whisper-base-v1-luxembourgish), de la Universidad de Luxemburgo (OpenMDW 1.1).
- Transcripción en danés: [Whisper Small Danish](https://huggingface.co/thorhojhus/whisper-small-danish) (MIT).
- Motor de transcripción: [whisper.cpp](https://github.com/ggml-org/whisper.cpp) mediante [whisper-rs](https://github.com/tazz4843/whisper-rs).
- Niveles orientados por los [descriptores del MCER](https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-descriptors-search).
