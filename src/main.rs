mod course;
mod field;
mod learning;
mod progress;
mod voice;

use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use axum::body::{Body, Bytes};
use axum::extract::{DefaultBodyLimit, Path, Query, Request, State};
use axum::http::{HeaderMap, StatusCode, header};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use rust_embed::RustEmbed;
use serde::Deserialize;
use serde_json::{Value, json};

use course::{Feedback, Scene};
use voice::{Speech, model_path};

const CATALOG: &str = include_str!("../content/scenes.json");
const ITINERARY: &str = include_str!("../content/itinerary.json");
const FRENCH: &str = include_str!("../content/french.json");
const COURSE: &str = include_str!("../content/course.json");
const FIELD: &str = include_str!("../web/field-data.json");
const LANGUAGES: [&str; 3] = ["lb", "da", "fr"];

#[derive(RustEmbed)]
#[folder = "web/"]
struct Assets;

struct App {
    scenes: Vec<Scene>,
    course: learning::Course,
    field: field::Catalog,
    db: Mutex<rusqlite::Connection>,
    voices: PathBuf,
    speech: Mutex<Speech>,
    transcription: Arc<tokio::sync::Semaphore>,
    client: reqwest::Client,
    api_key: Option<String>,
}

type AppState = Arc<App>;
type ApiResult<T> = Result<Json<T>, Error>;

struct Error(StatusCode, &'static str);

impl Error {
    fn bad() -> Self {
        Self(StatusCode::BAD_REQUEST, "Revisa los datos del intento.")
    }
    fn storage() -> Self {
        Self(
            StatusCode::INTERNAL_SERVER_ERROR,
            "No se pudo guardar el progreso.",
        )
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        (self.0, Json(json!({ "error": self.1 }))).into_response()
    }
}

impl App {
    fn scene(&self, id: &str) -> Result<&Scene, Error> {
        self.scenes.iter().find(|scene| scene.id == id).ok_or(Error(
            StatusCode::NOT_FOUND,
            "Esta escena no está disponible.",
        ))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    rustls::crypto::ring::default_provider()
        .install_default()
        .ok();
    whisper_rs::install_logging_hooks();
    let exe = std::env::current_exe()?;
    let data = match std::env::var_os("IDIOMAS_DATA_DIR") {
        Some(path) => PathBuf::from(path),
        None => default_data_dir()?,
    };
    std::fs::create_dir_all(&data)?;
    let voices = std::env::var_os("IDIOMAS_VOICES_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            exe.parent()
                .unwrap_or(std::path::Path::new("."))
                .join("voices")
        });
    let port = std::env::var("IDIOMAS_PORT")
        .map(|value| value.parse())
        .unwrap_or(Ok(8787))?;
    let mut scenes: Vec<Scene> = serde_json::from_str(CATALOG)?;
    scenes.extend(serde_json::from_str::<Vec<Scene>>(ITINERARY)?);
    scenes.extend(serde_json::from_str::<Vec<Scene>>(FRENCH)?);
    scenes.sort_by(|a, b| (&a.lang, &a.level, a.week).cmp(&(&b.lang, &b.level, b.week)));
    let app = Arc::new(App {
        scenes,
        course: serde_json::from_str(COURSE)?,
        field: serde_json::from_str(FIELD)?,
        db: Mutex::new(progress::open(&data.join("progress.sqlite3"))?),
        voices,
        speech: Mutex::new(Speech::default()),
        transcription: Arc::new(tokio::sync::Semaphore::new(1)),
        client: reqwest::Client::builder()
            .timeout(Duration::from_secs(15))
            .build()?,
        api_key: std::env::var("OPENAI_API_KEY")
            .ok()
            .filter(|key| !key.trim().is_empty()),
    });
    // IDIOMAS_HOST=0.0.0.0 opens the app to other devices on the local
    // network (phone, tablet); by default only this computer can reach it.
    let host: std::net::IpAddr = std::env::var("IDIOMAS_HOST")
        .map(|value| value.parse())
        .unwrap_or(Ok(std::net::IpAddr::from([127, 0, 0, 1])))
        .map_err(|_| "IDIOMAS_HOST debe ser una IP, por ejemplo 0.0.0.0")?;
    let lan = !host.is_loopback();
    let listener = tokio::net::TcpListener::bind((host, port)).await?;
    let url = format!("http://localhost:{port}");
    let router = Router::new()
        .route("/", get(|| async { asset_response("index.html", None) }))
        .route("/assets/{*file}", get(assets))
        .route("/api/catalog", get(catalog))
        .route("/api/progress", get(read_progress))
        .route("/api/field-history/{lang}", get(field_history))
        .route("/api/field-results", post(field_results))
        .route("/api/diagnostics/{lang}", get(diagnostics))
        .route("/api/assessments", post(assess))
        .route("/api/recordings/{lang}", get(recording_list))
        .route(
            "/api/recordings/{scene}/{turn}/{id}",
            post(save_recording).layer(DefaultBodyLimit::max(1_920_000)),
        )
        .route(
            "/api/recording/{id}",
            get(download_recording).delete(delete_recording),
        )
        .route("/api/attempts", post(attempt))
        .route("/api/today", get(today))
        .route("/api/course", get(course_overview))
        .route("/api/lesson/{id}", get(lesson_view))
        .route("/api/lesson/answer", post(lesson_answer))
        .route("/api/srs/due", get(srs_due))
        .route("/api/srs/review", post(srs_review))
        .route("/api/srs/stats", get(srs_stats))
        .route("/api/learning/summary", get(learning_summary))
        .route(
            "/api/transcriptions/{lang}",
            post(transcribe).layer(DefaultBodyLimit::max(1_920_000)),
        )
        .route(
            "/api/conversation",
            post(conversation).layer(DefaultBodyLimit::max(48_000)),
        )
        .layer(DefaultBodyLimit::max(24_000))
        .layer(middleware::from_fn(move |request, next| {
            local_only(request, next, port, lan)
        }))
        .with_state(app);
    println!("Idiomas · {url}");
    if lan {
        match lan_address() {
            Some(ip) => println!("Desde otro dispositivo de tu red: http://{ip}:{port}"),
            None => println!("Desde otro dispositivo de tu red: http://<IP-de-este-equipo>:{port}"),
        }
    }
    println!("Deja esta ventana abierta mientras estudias; ciérrala (Ctrl+C) para apagar la app.");
    if std::env::args().any(|arg| arg == "--open") {
        open_browser(&url);
    }
    axum::serve(listener, router).await?;
    Ok(())
}

/// Where progress and recordings live when IDIOMAS_DATA_DIR is not set.
fn default_data_dir() -> Result<PathBuf, &'static str> {
    let home = || std::env::var_os("HOME").or_else(|| std::env::var_os("USERPROFILE"));
    if cfg!(target_os = "macos") {
        Ok(PathBuf::from(home().ok_or("Falta HOME")?).join("Library/Application Support/Idiomas"))
    } else if cfg!(windows) {
        let base = std::env::var_os("APPDATA").or_else(home).ok_or("Falta APPDATA")?;
        Ok(PathBuf::from(base).join("Idiomas"))
    } else {
        match std::env::var_os("XDG_DATA_HOME").filter(|value| !value.is_empty()) {
            Some(base) => Ok(PathBuf::from(base).join("idiomas")),
            None => Ok(PathBuf::from(home().ok_or("Falta HOME")?).join(".local/share/idiomas")),
        }
    }
}

fn open_browser(url: &str) {
    let result = if cfg!(target_os = "macos") {
        std::process::Command::new("open").arg(url).spawn()
    } else if cfg!(windows) {
        std::process::Command::new("cmd").args(["/C", "start", "", url]).spawn()
    } else {
        std::process::Command::new("xdg-open").arg(url).spawn()
    };
    if result.is_err() {
        println!("Abre {url} en tu navegador.");
    }
}

/// The address other devices on the network can use. Connecting a UDP
/// socket sends nothing; it only asks the OS which interface it would use.
fn lan_address() -> Option<std::net::IpAddr> {
    let socket = std::net::UdpSocket::bind(("0.0.0.0", 0)).ok()?;
    socket.connect(("192.0.2.1", 80)).ok()?;
    socket.local_addr().ok().map(|addr| addr.ip())
}

async fn local_only(request: Request, next: Next, port: u16, lan: bool) -> Response {
    let hosts = [format!("localhost:{port}"), format!("127.0.0.1:{port}")];
    let host = request
        .headers()
        .get(header::HOST)
        .and_then(|value| value.to_str().ok())
        .unwrap_or("")
        .to_owned();
    // On the network, accept a bare IP address (http://192.168.1.20:8787) but
    // never a domain name, which keeps DNS-rebinding attacks out.
    let lan_host = lan
        && host
            .parse::<std::net::SocketAddr>()
            .is_ok_and(|addr| addr.port() == port);
    let host_ok = hosts.iter().any(|known| *known == host) || lan_host;
    let origin_ok = request
        .headers()
        .get(header::ORIGIN)
        .is_none_or(|value| value == format!("http://{host}").as_str());
    let cross_site = request
        .headers()
        .get("sec-fetch-site")
        .is_some_and(|value| value == "cross-site");
    if !host_ok || !origin_ok || cross_site {
        return StatusCode::FORBIDDEN.into_response();
    }
    let mut response = next.run(request).await;
    response
        .headers_mut()
        .insert(header::X_CONTENT_TYPE_OPTIONS, "nosniff".parse().unwrap());
    response.headers_mut().insert(header::CONTENT_SECURITY_POLICY,
        "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; media-src 'self' blob:; connect-src 'self'".parse().unwrap());
    response
}

async fn assets(Path(file): Path<String>, headers: HeaderMap) -> Response {
    asset_response(
        &file,
        headers
            .get(header::RANGE)
            .and_then(|value| value.to_str().ok()),
    )
}

fn asset_response(file: &str, range: Option<&str>) -> Response {
    let Some(asset) = Assets::get(file) else {
        return StatusCode::NOT_FOUND.into_response();
    };
    let content_type = match file.rsplit('.').next() {
        Some("html") => "text/html; charset=utf-8",
        Some("js") => "text/javascript; charset=utf-8",
        Some("css") => "text/css; charset=utf-8",
        Some("mp3") => "audio/mpeg",
        Some("json") => "application/json; charset=utf-8",
        _ => "application/octet-stream",
    };
    served_bytes(asset.data.into_owned(), content_type, range)
}

fn served_bytes(bytes: Vec<u8>, content_type: &'static str, range: Option<&str>) -> Response {
    let size = bytes.len();
    let mut response = Response::builder().header(header::CONTENT_TYPE, content_type);
    if content_type.starts_with("audio/") {
        response = response.header(header::ACCEPT_RANGES, "bytes");
        if let Some(range) = range {
            if let Some((start, end)) = byte_range(range, size) {
                return response
                    .status(StatusCode::PARTIAL_CONTENT)
                    .header(header::CONTENT_RANGE, format!("bytes {start}-{end}/{size}"))
                    .header(header::CONTENT_LENGTH, end - start + 1)
                    .body(Body::from(bytes[start..=end].to_vec()))
                    .unwrap();
            }
            return response
                .status(StatusCode::RANGE_NOT_SATISFIABLE)
                .header(header::CONTENT_RANGE, format!("bytes */{size}"))
                .body(Body::empty())
                .unwrap();
        }
    }
    response
        .header(header::CONTENT_LENGTH, size)
        .body(Body::from(bytes))
        .unwrap()
}

fn byte_range(range: &str, size: usize) -> Option<(usize, usize)> {
    let last = size.checked_sub(1)?;
    let (start, end) = range.strip_prefix("bytes=")?.split_once('-')?;
    if start.is_empty() {
        let suffix: usize = end.parse().ok()?;
        return (suffix > 0).then(|| (size.saturating_sub(suffix), last));
    }
    let start: usize = start.parse().ok()?;
    let end = if end.is_empty() {
        last
    } else {
        end.parse::<usize>().ok()?.min(last)
    };
    (start <= end).then_some((start, end))
}

async fn catalog(State(app): State<AppState>) -> Json<Value> {
    Json(json!({
        "scenes": &app.scenes,
        "voice": LANGUAGES.map(|lang| (lang, model_path(&app.voices, lang).is_file())).into_iter()
            .collect::<std::collections::BTreeMap<_, _>>(),
        "cloud": app.api_key.is_some()
    }))
}

async fn read_progress(State(app): State<AppState>) -> ApiResult<progress::Progress> {
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::read(&connection)
        .map(Json)
        .map_err(|_| Error::storage())
}

#[derive(Deserialize)]
struct Submission {
    id: String,
    scene: String,
    activity: String,
    #[serde(default)]
    text: String,
    choice: Option<usize>,
}

async fn attempt(
    State(app): State<AppState>,
    Json(input): Json<Submission>,
) -> ApiResult<Feedback> {
    if !valid_id(&input.id) || input.text.chars().count() > 4_000 {
        return Err(Error::bad());
    }
    let scene = app.scene(&input.scene)?;
    let text = input.text.trim();
    let mut review = None;
    let (feedback, completed) = match input.activity.as_str() {
        "listening" | "reading" => {
            let quiz = if input.activity == "listening" {
                &scene.listening
            } else {
                &scene.reading.quiz
            };
            let choice = input
                .choice
                .filter(|&choice| choice < quiz.choices.len())
                .ok_or_else(Error::bad)?;
            (course::evaluate_quiz(quiz, choice), choice == quiz.answer)
        }
        "writing" if !text.is_empty() => (
            Feedback {
                status: "reference",
                example: scene.writing.model.clone(),
                explanation: scene.writing.rubric.clone(),
            },
            true,
        ),
        activity if !text.is_empty() => {
            let (kind, position) = activity.split_once('/').ok_or_else(Error::bad)?;
            let index: usize = position.parse().map_err(|_| Error::bad())?;
            if index.to_string() != position {
                return Err(Error::bad());
            }
            if kind == "repeat" {
                let turn = scene.turns.get(index).ok_or_else(Error::bad)?;
                let mut feedback = course::evaluate_turn(turn, text);
                if course::normalize(&turn.model) == course::normalize(text) {
                    feedback.status = "correct";
                } else {
                    feedback.status = "correction";
                    feedback.explanation = "Escucha el modelo otra vez y compáralo con lo que has escrito o transcrito.".into();
                }
                return store_feedback(&app, &input, &scene.id, feedback, false, None);
            }
            let (feedback, exercise, reviewing) = match kind {
                "turn" | "review" => (
                    course::evaluate_turn(scene.turns.get(index).ok_or_else(Error::bad)?, text),
                    false,
                    kind == "review",
                ),
                "exercise" | "review-exercise" => (
                    course::evaluate_exercise(&scene.exercise(index).ok_or_else(Error::bad)?, text),
                    true,
                    kind == "review-exercise",
                ),
                _ => return Err(Error::bad()),
            };
            // An unmatched open reply stays ungraded. It can still be completed as practice.
            if feedback.status != "reference" || reviewing {
                review = Some(progress::ReviewUpdate {
                    index,
                    exercise,
                    reviewing,
                    correct: feedback.status == "correct",
                });
            }
            let complete = !exercise || feedback.status == "correct";
            (feedback, complete)
        }
        _ => return Err(Error::bad()),
    };
    store_feedback(&app, &input, &scene.id, feedback, completed, review)
}

fn store_feedback(
    app: &App,
    input: &Submission,
    scene: &str,
    feedback: Feedback,
    completed: bool,
    review: Option<progress::ReviewUpdate>,
) -> ApiResult<Feedback> {
    let mut connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::record(
        &mut connection,
        progress::Attempt {
            id: &input.id,
            scene,
            activity: &input.activity,
            completed,
            outcome: feedback.status,
            review,
        },
    )
    .map_err(|_| Error::storage())?;
    Ok(Json(feedback))
}

fn valid_id(id: &str) -> bool {
    (8..=80).contains(&id.len())
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}

fn valid_lang(lang: &str) -> Result<(), Error> {
    LANGUAGES
        .contains(&lang)
        .then_some(())
        .ok_or_else(Error::bad)
}

#[derive(Deserialize)]
struct LangQuery {
    lang: String,
    limit: Option<usize>,
}

fn lesson_state_map(
    states: &[progress::LessonState],
) -> std::collections::HashMap<String, progress::LessonState> {
    states
        .iter()
        .map(|state| (state.lesson.clone(), state.clone()))
        .collect()
}

fn due_json(app: &App, due: &[progress::DueItem]) -> Vec<Value> {
    due.iter()
        .filter_map(|entry| {
            let item = app.course.item(&entry.item)?;
            Some(json!({
                "id": item.id,
                "text": item.text,
                "translation": item.translation,
                "example": item.example,
                "example_es": item.example_es,
                "audio": item.audio,
                "level": item.level,
                "due": entry.due,
                "interval": entry.interval,
                "reps": entry.reps,
                "lapses": entry.lapses,
            }))
        })
        .collect()
}

fn lesson_brief(lesson: &learning::Lesson, state: Option<&progress::LessonState>) -> Value {
    json!({
        "id": lesson.id,
        "day": lesson.day,
        "week": lesson.week,
        "level": lesson.level,
        "title": lesson.title,
        "goal": lesson.goal,
        "tasks": lesson.tasks.len(),
        "checkpoint": lesson.checkpoint,
        "completed": state.is_some_and(|state| state.completed),
        "tasks_done": state.map_or(0, |state| state.tasks_done),
        "tasks_total": state.map_or(lesson.tasks.len() as i64, |state| state.tasks_total),
    })
}

async fn today(State(app): State<AppState>, Query(query): Query<LangQuery>) -> ApiResult<Value> {
    valid_lang(&query.lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let states = progress::lesson_states(&connection, &query.lang).map_err(|_| Error::storage())?;
    let map = lesson_state_map(&states);
    let done = states
        .iter()
        .filter(|state| state.completed)
        .map(|state| state.lesson.clone())
        .collect::<std::collections::HashSet<_>>();
    let lessons = app.course.lessons(&query.lang);
    // Do not silently jump over unpublished weeks and present that as a continuous course.
    let first_pending = app.course.first_unfinished(&query.lang, &done);
    let last_completed_week = lessons
        .iter()
        .filter(|lesson| done.contains(&lesson.id))
        .map(|lesson| lesson.week)
        .max()
        .unwrap_or(0);
    let next = first_pending.filter(|lesson| lesson.week <= last_completed_week + 1);
    let completed = lessons
        .iter()
        .filter(|lesson| done.contains(&lesson.id))
        .count();
    let level = next
        .map(|lesson| lesson.level.as_str())
        .or_else(|| {
            lessons
                .iter()
                .rev()
                .find(|lesson| done.contains(&lesson.id))
                .map(|lesson| lesson.level.as_str())
        })
        .unwrap_or("A1");
    let (hours_low, hours_high) = learning::level_hours(level);
    let due = progress::due_items(&connection, &query.lang, 20).map_err(|_| Error::storage())?;
    let stats = progress::item_stats(&connection, &query.lang).map_err(|_| Error::storage())?;
    let streak = progress::streak(&connection, &query.lang).map_err(|_| Error::storage())?;
    let minutes = progress::minutes_week(&connection, &query.lang).map_err(|_| Error::storage())?;
    let tasks = progress::task_count(&connection, &query.lang).map_err(|_| Error::storage())?;

    let unit = next.and_then(|lesson| {
        app.course
            .units(&query.lang)
            .into_iter()
            .find(|unit| unit.id == lesson.unit)
            .map(|unit| {
                json!({
                    "id": unit.id,
                    "title": unit.title,
                    "can_do": unit.can_do,
                    "week": unit.week,
                    "level": unit.level,
                    "editorial_status": unit.editorial_status,
                    "lessons": unit.lessons.iter().map(|lesson| lesson_brief(lesson, map.get(&lesson.id))).collect::<Vec<_>>(),
                })
            })
    });

    Ok(Json(json!({
        "lang": query.lang,
        "next": next.map(|lesson| lesson_brief(lesson, map.get(&lesson.id))),
        "next_available": first_pending.filter(|_| next.is_none()).map(|lesson| lesson_brief(lesson, map.get(&lesson.id))),
        "unit": unit,
        "due": {
            "count": stats.due,
            "items": due_json(&app, &due),
        },
        "stats": {
            "level": level,
            "week": next.map_or(last_completed_week.max(1), |lesson| lesson.week),
            "total_weeks": learning::total_weeks(),
            "lessons_completed": completed,
            "lessons_total": lessons.len(),
            "tasks_done": tasks,
            "streak": streak,
            "minutes_week": minutes,
            "hours_low": hours_low,
            "hours_high": hours_high,
            "vocabulary": {
                "total": stats.total,
                "due": stats.due,
                "learned": stats.learned,
                "reviews_today": stats.reviews_today,
                "reviews_week": stats.reviews_week,
            },
        },
    })))
}

async fn course_overview(
    State(app): State<AppState>,
    Query(query): Query<LangQuery>,
) -> ApiResult<Value> {
    valid_lang(&query.lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let states = progress::lesson_states(&connection, &query.lang).map_err(|_| Error::storage())?;
    let map = lesson_state_map(&states);
    let lessons = app.course.lessons(&query.lang);
    let completed = lessons
        .iter()
        .filter(|lesson| map.get(&lesson.id).is_some_and(|state| state.completed))
        .count();
    let units = app
        .course
        .units(&query.lang)
        .into_iter()
        .map(|unit| {
            json!({
                "id": unit.id,
                "week": unit.week,
                "level": unit.level,
                "title": unit.title,
                "can_do": unit.can_do,
                "editorial_status": unit.editorial_status,
                "lessons": unit.lessons.iter().map(|lesson| lesson_brief(lesson, map.get(&lesson.id))).collect::<Vec<_>>(),
            })
        })
        .collect::<Vec<_>>();
    Ok(Json(json!({
        "lang": query.lang,
        "units": units,
        "roadmap": app.course.roadmap,
        "coverage": app.course.roadmap.iter().map(|stage| {
            let published = app.course.units(&query.lang).into_iter()
                .filter(|unit| unit.level == stage.level).collect::<Vec<_>>();
            json!({"level": stage.level, "planned_weeks": stage.end - stage.start + 1,
                   "published_weeks": published.iter().map(|unit| unit.week).collect::<Vec<_>>(),
                   "draft_weeks": published.iter().filter(|unit| unit.editorial_status.is_some()).map(|unit| unit.week).collect::<Vec<_>>(),
                   "published_lessons": published.iter().map(|unit| unit.lessons.len()).sum::<usize>()})
        }).collect::<Vec<_>>(),
        "stats": {
            "lessons_completed": completed,
            "lessons_total": lessons.len(),
        },
    })))
}

async fn lesson_view(State(app): State<AppState>, Path(id): Path<String>) -> ApiResult<Value> {
    let lesson = app.course.lesson(&id).ok_or(Error(
        StatusCode::NOT_FOUND,
        "Esta lección no está disponible.",
    ))?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let state = progress::lesson_states(&connection, &lesson.lang)
        .map_err(|_| Error::storage())?
        .into_iter()
        .find(|state| state.lesson == id);
    let unit = app
        .course
        .units(&lesson.lang)
        .into_iter()
        .find(|unit| unit.id == lesson.unit)
        .map(|unit| {
            json!({"id": unit.id, "title": unit.title, "can_do": unit.can_do,
                           "editorial_status": unit.editorial_status})
        });
    let done_tasks = progress::completed_tasks(&connection, &id).map_err(|_| Error::storage())?;
    let items = lesson
        .items
        .iter()
        .chain(lesson.tasks.iter().flat_map(|task| task.items.iter()))
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .filter_map(|item| app.course.item(item))
        .collect::<Vec<_>>();
    Ok(Json(json!({
        "lesson": lesson,
        "state": state,
        "done_tasks": done_tasks,
        "unit": unit,
        "items": items,
        "level_hours": {
            "low": learning::level_hours(&lesson.level).0,
            "high": learning::level_hours(&lesson.level).1,
        },
    })))
}

#[derive(Deserialize)]
struct LessonAnswer {
    id: String,
    lesson: String,
    task: usize,
    #[serde(default)]
    text: String,
    choice: Option<usize>,
    #[serde(default)]
    duration_seconds: u32,
}

async fn lesson_answer(
    State(app): State<AppState>,
    Json(input): Json<LessonAnswer>,
) -> ApiResult<Value> {
    if !valid_id(&input.id) || input.text.chars().count() > 4_000 {
        return Err(Error::bad());
    }
    let lesson = app.course.lesson(&input.lesson).ok_or(Error::bad())?;
    let task = lesson.tasks.get(input.task).ok_or(Error::bad())?;
    let grade = learning::evaluate(task, &input.text, input.choice);
    let counted = !grade.graded || grade.correct;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let state = progress::record_task(
        &connection,
        &input.id,
        &lesson.id,
        &lesson.lang,
        input.task,
        &task.kind,
        grade.correct,
        counted,
        lesson.tasks.len(),
        input.duration_seconds,
    )
    .map_err(|_| Error::storage())?;
    if state.completed {
        progress::introduce_items(&connection, &lesson.lang, &lesson.items)
            .map_err(|_| Error::storage())?;
    }
    Ok(Json(json!({
        "feedback": grade.feedback,
        "correct": grade.correct,
        "graded": grade.graded,
        "counted": counted,
        "state": state,
    })))
}

async fn srs_due(State(app): State<AppState>, Query(query): Query<LangQuery>) -> ApiResult<Value> {
    valid_lang(&query.lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let due = progress::due_items(&connection, &query.lang, query.limit.unwrap_or(40).min(200))
        .map_err(|_| Error::storage())?;
    let stats = progress::item_stats(&connection, &query.lang).map_err(|_| Error::storage())?;
    Ok(Json(json!({
        "items": due_json(&app, &due),
        "stats": stats,
    })))
}

#[derive(Deserialize)]
struct SrsReview {
    id: String,
    item: String,
    grade: u8,
}

async fn srs_review(State(app): State<AppState>, Json(input): Json<SrsReview>) -> ApiResult<Value> {
    if !valid_id(&input.id) || input.grade > 3 {
        return Err(Error::bad());
    }
    let item = app.course.item(&input.item).ok_or(Error::bad())?;
    let mut connection = app.db.lock().map_err(|_| Error::storage())?;
    let due = progress::review_item(
        &mut connection,
        &input.id,
        &item.id,
        &item.lang,
        input.grade,
    )
    .map_err(|_| Error::storage())?;
    let stats = progress::item_stats(&connection, &item.lang).map_err(|_| Error::storage())?;
    Ok(Json(json!({ "due": due, "stats": stats })))
}

async fn srs_stats(
    State(app): State<AppState>,
    Query(query): Query<LangQuery>,
) -> ApiResult<Value> {
    valid_lang(&query.lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let stats = progress::item_stats(&connection, &query.lang).map_err(|_| Error::storage())?;
    let streak = progress::streak(&connection, &query.lang).map_err(|_| Error::storage())?;
    let minutes = progress::minutes_week(&connection, &query.lang).map_err(|_| Error::storage())?;
    let states = progress::lesson_states(&connection, &query.lang).map_err(|_| Error::storage())?;
    Ok(Json(json!({
        "stats": stats,
        "streak": streak,
        "minutes_week": minutes,
        "lessons_completed": states.iter().filter(|state| state.completed).count(),
        "lessons_total": app.course.lessons(&query.lang).len(),
    })))
}

async fn learning_summary(
    State(app): State<AppState>,
    Query(query): Query<LangQuery>,
) -> ApiResult<Value> {
    valid_lang(&query.lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let states = progress::lesson_states(&connection, &query.lang).map_err(|_| Error::storage())?;
    let lessons = app.course.lessons(&query.lang);
    let completed = lessons
        .iter()
        .filter(|lesson| {
            states
                .iter()
                .any(|state| state.lesson == lesson.id && state.completed)
        })
        .count();
    let level = lessons
        .iter()
        .rev()
        .find(|lesson| {
            states
                .iter()
                .any(|state| state.lesson == lesson.id && state.completed)
        })
        .map(|lesson| lesson.level.clone())
        .unwrap_or_else(|| "A1".into());
    let stats = progress::item_stats(&connection, &query.lang).map_err(|_| Error::storage())?;
    let streak = progress::streak(&connection, &query.lang).map_err(|_| Error::storage())?;
    let minutes = progress::minutes_week(&connection, &query.lang).map_err(|_| Error::storage())?;
    let tasks = progress::task_count(&connection, &query.lang).map_err(|_| Error::storage())?;
    let seconds =
        progress::seconds_total(&connection, &query.lang).map_err(|_| Error::storage())?;
    let hours = seconds as f64 / 3600.0;
    let (hours_low, hours_high) = learning::level_hours(&level);
    Ok(Json(json!({
        "level": level,
        "lessons_completed": completed,
        "lessons_total": lessons.len(),
        "tasks_done": tasks,
        "streak": streak,
        "minutes_week": minutes,
        "hours_measured": (hours * 100.0).round() / 100.0,
        "hours_low": hours_low,
        "hours_high": hours_high,
        "vocabulary": stats,
        "by_level": lessons.iter().fold(
            std::collections::BTreeMap::<String, (usize, usize)>::new(),
            |mut map, lesson| {
                let entry = map.entry(lesson.level.clone()).or_default();
                entry.1 += 1;
                if states.iter().any(|state| state.lesson == lesson.id && state.completed) {
                    entry.0 += 1;
                }
                map
            }
        ).into_iter().map(|(level, (done, total))| json!({"level": level, "done": done, "total": total})).collect::<Vec<_>>(),
    })))
}

async fn field_history(
    State(app): State<AppState>,
    Path(lang): Path<String>,
) -> ApiResult<field::History> {
    valid_lang(&lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    field::history(&connection, &lang)
        .map(Json)
        .map_err(|_| Error::storage())
}

async fn field_results(
    State(app): State<AppState>,
    Json(input): Json<field::Submission>,
) -> ApiResult<field::Outcome> {
    valid_lang(&input.lang)?;
    if !valid_id(&input.id) {
        return Err(Error::bad());
    }
    let result = app.field.evaluate(&input).ok_or_else(Error::bad)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    field::store(&connection, &input, &result).map_err(|_| Error::storage())?;
    Ok(Json(result))
}

async fn diagnostics(
    State(app): State<AppState>,
    Path(lang): Path<String>,
) -> ApiResult<progress::Diagnostics> {
    valid_lang(&lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::diagnostics(&connection, &lang)
        .map(Json)
        .map_err(|_| Error::storage())
}

#[derive(Deserialize)]
struct Assessment {
    id: String,
    scene: String,
    activity: String,
    score: u8,
}

async fn assess(
    State(app): State<AppState>,
    Json(input): Json<Assessment>,
) -> Result<StatusCode, Error> {
    app.scene(&input.scene)?;
    if !valid_id(&input.id)
        || !matches!(input.activity.as_str(), "speaking" | "writing")
        || input.score > 2
    {
        return Err(Error::bad());
    }
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::assess(
        &connection,
        &input.id,
        &input.scene,
        &input.activity,
        input.score,
    )
    .map_err(|_| Error::storage())?;
    Ok(StatusCode::NO_CONTENT)
}

#[derive(Deserialize)]
struct Page {
    page: Option<u32>,
}

async fn recording_list(
    State(app): State<AppState>,
    Path(lang): Path<String>,
    Query(query): Query<Page>,
) -> ApiResult<progress::RecordingPage> {
    valid_lang(&lang)?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::recording_list(&connection, &lang, query.page.unwrap_or(0))
        .map(Json)
        .map_err(|_| Error::storage())
}

async fn save_recording(
    State(app): State<AppState>,
    Path((scene, turn, id)): Path<(String, usize, String)>,
    bytes: Bytes,
) -> Result<StatusCode, Error> {
    let scene = app.scene(&scene)?;
    if !valid_id(&id) || turn >= scene.turns.len() {
        return Err(Error::bad());
    }
    voice::decode_audio(&bytes)
        .map_err(|message| Error(StatusCode::UNPROCESSABLE_ENTITY, message))?;
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::save_recording(&connection, &id, &scene.id, turn, &bytes)
        .map_err(|_| Error::storage())?;
    Ok(StatusCode::CREATED)
}

async fn delete_recording(
    State(app): State<AppState>,
    Path(id): Path<String>,
) -> Result<StatusCode, Error> {
    if !valid_id(&id) {
        return Err(Error::bad());
    }
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    progress::delete_recording(&connection, &id).map_err(|_| Error::storage())?;
    Ok(StatusCode::NO_CONTENT)
}

async fn download_recording(
    State(app): State<AppState>,
    Path(id): Path<String>,
    headers: HeaderMap,
) -> Result<Response, Error> {
    if !valid_id(&id) {
        return Err(Error::bad());
    }
    let connection = app.db.lock().map_err(|_| Error::storage())?;
    let pcm = progress::recording(&connection, &id).map_err(|err| match err {
        rusqlite::Error::QueryReturnedNoRows => {
            Error(StatusCode::NOT_FOUND, "La grabación no está disponible.")
        }
        _ => Error::storage(),
    })?;
    let mut wav = Vec::with_capacity(44 + pcm.len());
    wav.extend(b"RIFF");
    wav.extend(((pcm.len() + 36) as u32).to_le_bytes());
    wav.extend(b"WAVEfmt ");
    wav.extend(16u32.to_le_bytes());
    wav.extend(1u16.to_le_bytes());
    wav.extend(1u16.to_le_bytes());
    wav.extend(16_000u32.to_le_bytes());
    wav.extend(32_000u32.to_le_bytes());
    wav.extend(2u16.to_le_bytes());
    wav.extend(16u16.to_le_bytes());
    wav.extend(b"data");
    wav.extend((pcm.len() as u32).to_le_bytes());
    wav.extend(pcm);
    let range = headers
        .get(header::RANGE)
        .and_then(|value| value.to_str().ok());
    let mut response = served_bytes(wav, "audio/wav", range);
    response
        .headers_mut()
        .insert(header::CACHE_CONTROL, "no-store".parse().unwrap());
    Ok(response)
}

async fn transcribe(
    State(app): State<AppState>,
    Path(lang): Path<String>,
    bytes: Bytes,
) -> ApiResult<Value> {
    if !LANGUAGES.contains(&lang.as_str()) {
        return Err(Error::bad());
    }
    let model = model_path(&app.voices, &lang);
    if !model.is_file() {
        return Err(Error(
            StatusCode::SERVICE_UNAVAILABLE,
            "Falta el modelo de voz de este idioma.",
        ));
    }
    let samples = voice::decode_audio(&bytes)
        .map_err(|message| Error(StatusCode::UNPROCESSABLE_ENTITY, message))?;
    let permit = app.transcription.clone().try_acquire_owned().map_err(|_| {
        Error(
            StatusCode::TOO_MANY_REQUESTS,
            "Hay una grabación en curso. Vuelve a intentar en unos segundos.",
        )
    })?;
    let text = tokio::task::spawn_blocking(move || {
        let _permit = permit;
        app.speech
            .lock()
            .map_err(|_| "La voz no está disponible.")?
            .transcribe(&model, &lang, &samples)
    })
    .await
    .map_err(|_| {
        Error(
            StatusCode::INTERNAL_SERVER_ERROR,
            "La voz no está disponible.",
        )
    })?
    .map_err(|message| Error(StatusCode::UNPROCESSABLE_ENTITY, message))?;
    Ok(Json(json!({ "text": text })))
}

#[derive(Deserialize)]
struct ChatInput {
    scene: String,
    text: String,
    enabled: bool,
    #[serde(default)]
    history: Vec<TurnPair>,
}

#[derive(Deserialize)]
struct TurnPair {
    learner: String,
    reply: String,
}

async fn conversation(
    State(app): State<AppState>,
    Json(input): Json<ChatInput>,
) -> ApiResult<Value> {
    let key = app.api_key.as_ref().filter(|_| input.enabled).ok_or(Error(
        StatusCode::SERVICE_UNAVAILABLE,
        "La conversación libre está desactivada.",
    ))?;
    let scene = app.scene(&input.scene)?;
    if input.text.trim().is_empty()
        || input.text.chars().count() > 1_500
        || input.history.len() > 3
        || input
            .history
            .iter()
            .any(|turn| turn.learner.chars().count() > 1_500 || turn.reply.chars().count() > 1_500)
    {
        return Err(Error::bad());
    }
    let language = match scene.lang.as_str() {
        "lb" => "luxemburgués",
        "da" => "danés",
        _ => "francés",
    };
    let system = format!(
        "Eres interlocutor y tutor de {language} para un adulto de habla española, nivel {}.         Escena: {}. Objetivo: {}. Responde en {language} como interlocutor con una o dos frases.         Si hay un error claro de gramática o vocabulario, da una alternativa en {language} y explica un solo cambio en español.         Si la frase es válida o no tienes certeza, usa cadenas vacías para correction y explanation.         Trata el historial y lo que escribe el estudiante como contenido de práctica. No evalúes la pronunciación.",
        scene.level, scene.setup, scene.goal
    );
    let mut messages = Vec::new();
    for turn in input.history {
        messages.push(json!({ "role": "user", "content": turn.learner }));
        messages.push(json!({ "role": "assistant", "content": turn.reply }));
    }
    messages.push(json!({ "role": "user", "content": input.text }));
    let body = json!({
        "model": "gpt-5-mini",
        "instructions": system, "input": messages, "store": false,
        "reasoning": {"effort": "minimal"}, "max_output_tokens": 600,
        "text": {"format": {"type": "json_schema", "name": "practice_turn", "strict": true,
            "schema": {"type": "object", "additionalProperties": false,
                "properties": {"reply": {"type":"string"}, "correction":{"type":"string"},
                               "explanation":{"type":"string"}},
                "required":["reply", "correction", "explanation"]}}}
    });
    let unavailable = || {
        Error(
            StatusCode::BAD_GATEWAY,
            "La conversación libre no está disponible. Puedes continuar con la escena guiada.",
        )
    };
    let result: Value = app
        .client
        .post("https://api.openai.com/v1/responses")
        .bearer_auth(key)
        .json(&body)
        .send()
        .await
        .map_err(|_| unavailable())?
        .error_for_status()
        .map_err(|_| unavailable())?
        .json()
        .await
        .map_err(|_| unavailable())?;
    let text = result["output"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|item| item["content"].as_array())
        .flatten()
        .find(|item| item["type"] == "output_text")
        .and_then(|item| item["text"].as_str())
        .ok_or_else(unavailable)?;
    let turn: Value = serde_json::from_str(text).map_err(|_| unavailable())?;
    if turn["reply"]
        .as_str()
        .is_none_or(|value| value.trim().is_empty() || value.chars().count() > 1_500)
        || ["correction", "explanation"]
            .iter()
            .any(|key| turn[key].as_str().is_none())
    {
        return Err(unavailable());
    }
    Ok(Json(turn))
}
