use std::path::Path;

use rusqlite::{Connection, Result, params};
use serde::Serialize;

#[derive(Serialize)]
pub struct Progress {
    activities: Vec<Completed>,
    reviews: Vec<Review>,
    exercises: Vec<Review>,
}

#[derive(Serialize)]
struct Completed {
    scene: String,
    activity: String,
}

#[derive(Serialize)]
struct Review {
    scene: String,
    turn: i64,
    due: bool,
    date: String,
}

pub fn open(path: &Path) -> Result<Connection> {
    let mut connection = Connection::open(path)?;
    connection.execute_batch("PRAGMA journal_mode = WAL;")?;
    let transaction = connection.transaction()?;
    transaction.execute_batch(
        "CREATE TABLE IF NOT EXISTS attempts (
             id TEXT PRIMARY KEY, scene TEXT NOT NULL, activity TEXT NOT NULL,
             completed INTEGER NOT NULL CHECK (completed IN (0, 1)),
             at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
             outcome TEXT
         );
         CREATE TABLE IF NOT EXISTS reviews (
             scene TEXT NOT NULL, turn INTEGER NOT NULL, stage INTEGER NOT NULL,
             due TEXT NOT NULL, PRIMARY KEY (scene, turn)
         );
         CREATE TABLE IF NOT EXISTS exercise_reviews (
             scene TEXT NOT NULL, turn INTEGER NOT NULL, stage INTEGER NOT NULL,
             due TEXT NOT NULL, PRIMARY KEY (scene, turn)
         );
         CREATE TABLE IF NOT EXISTS self_assessments (
             id TEXT PRIMARY KEY, scene TEXT NOT NULL, activity TEXT NOT NULL,
             score INTEGER NOT NULL, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
         );
         CREATE TABLE IF NOT EXISTS recordings (
             id TEXT PRIMARY KEY, scene TEXT NOT NULL, turn INTEGER NOT NULL,
             audio BLOB NOT NULL, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
         );
         CREATE TABLE IF NOT EXISTS field_attempts (
             id TEXT PRIMARY KEY, lang TEXT NOT NULL, mode TEXT NOT NULL, exercise TEXT NOT NULL,
             score1 INTEGER NOT NULL, score2 INTEGER NOT NULL, score3 INTEGER NOT NULL, score4 INTEGER NOT NULL,
             variant INTEGER NOT NULL, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
         );
          CREATE TABLE IF NOT EXISTS item_reviews (
             item TEXT PRIMARY KEY, lang TEXT NOT NULL,
             interval INTEGER NOT NULL DEFAULT 0, ease REAL NOT NULL DEFAULT 2.5,
             reps INTEGER NOT NULL DEFAULT 0, lapses INTEGER NOT NULL DEFAULT 0,
             due TEXT NOT NULL, last TEXT,
              first TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
          );
          CREATE TABLE IF NOT EXISTS item_review_events (
              id TEXT PRIMARY KEY, item TEXT NOT NULL, lang TEXT NOT NULL,
              grade INTEGER NOT NULL, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
          );
         CREATE TABLE IF NOT EXISTS lesson_progress (
             lesson TEXT PRIMARY KEY, lang TEXT NOT NULL,
             completed INTEGER NOT NULL DEFAULT 0,
             tasks_done INTEGER NOT NULL DEFAULT 0, tasks_total INTEGER NOT NULL,
             correct INTEGER NOT NULL DEFAULT 0,
             started TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, finished TEXT
         );
          CREATE TABLE IF NOT EXISTS task_attempts (
              id TEXT PRIMARY KEY, lesson TEXT NOT NULL, task INTEGER NOT NULL,
              kind TEXT NOT NULL, correct INTEGER NOT NULL, counted INTEGER NOT NULL DEFAULT 0,
              at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              duration_seconds INTEGER NOT NULL DEFAULT 0
         );
         CREATE TABLE IF NOT EXISTS study_minutes (
             day TEXT PRIMARY KEY, minutes INTEGER NOT NULL DEFAULT 0
         );
         CREATE INDEX IF NOT EXISTS field_attempts_lang ON field_attempts(lang, mode, exercise, at);
         CREATE INDEX IF NOT EXISTS attempts_scene_activity ON attempts(scene, activity, at);
         CREATE INDEX IF NOT EXISTS recordings_scene_time ON recordings(scene, at);
          CREATE INDEX IF NOT EXISTS item_reviews_lang_due ON item_reviews(lang, due);
          CREATE INDEX IF NOT EXISTS item_review_events_lang_at ON item_review_events(lang, at);
         CREATE INDEX IF NOT EXISTS task_attempts_lesson ON task_attempts(lesson, at);",
    )?;
    let has_outcome: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM pragma_table_info('attempts') WHERE name = 'outcome')",
        [],
        |r| r.get(0),
    )?;
    if !has_outcome {
        transaction.execute("ALTER TABLE attempts ADD COLUMN outcome TEXT", [])?;
    }
    let has_duration: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM pragma_table_info('task_attempts') WHERE name = 'duration_seconds')",
        [], |row| row.get(0),
    )?;
    if !has_duration {
        transaction.execute(
            "ALTER TABLE task_attempts ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 0",
            [],
        )?;
    }
    transaction.commit()?;
    Ok(connection)
}

fn reviews(connection: &Connection, exercises: bool) -> Result<Vec<Review>> {
    let table = if exercises {
        "exercise_reviews"
    } else {
        "reviews"
    };
    let mut query = connection.prepare(&format!(
        "SELECT scene, turn, due <= date('now','localtime'), due FROM {table} ORDER BY due, scene, turn"
    ))?;
    query
        .query_map([], |row| {
            Ok(Review {
                scene: row.get(0)?,
                turn: row.get(1)?,
                due: row.get(2)?,
                date: row.get(3)?,
            })
        })?
        .collect()
}

pub fn read(connection: &Connection) -> Result<Progress> {
    let mut activities = connection.prepare(
        "SELECT DISTINCT scene, activity FROM attempts WHERE completed = 1
         AND activity NOT LIKE 'review/%' AND activity NOT LIKE 'review-exercise/%'",
    )?;
    let activities = activities
        .query_map([], |row| {
            Ok(Completed {
                scene: row.get(0)?,
                activity: row.get(1)?,
            })
        })?
        .collect::<Result<_>>()?;
    Ok(Progress {
        activities,
        reviews: reviews(connection, false)?,
        exercises: reviews(connection, true)?,
    })
}

pub struct Attempt<'a> {
    pub id: &'a str,
    pub scene: &'a str,
    pub activity: &'a str,
    pub completed: bool,
    pub outcome: &'a str,
    pub review: Option<ReviewUpdate>,
}

pub struct ReviewUpdate {
    pub index: usize,
    pub correct: bool,
    pub reviewing: bool,
    pub exercise: bool,
}

pub fn record(connection: &mut Connection, attempt: Attempt<'_>) -> Result<()> {
    let transaction = connection.transaction()?;
    let inserted = transaction.execute(
        "INSERT INTO attempts(id, scene, activity, completed, outcome) VALUES (?1, ?2, ?3, ?4, ?5)
         ON CONFLICT(id) DO NOTHING",
        params![
            attempt.id,
            attempt.scene,
            attempt.activity,
            attempt.completed,
            attempt.outcome
        ],
    )?;
    if let (1, Some(update)) = (inserted, attempt.review) {
        let table = if update.exercise {
            "exercise_reviews"
        } else {
            "reviews"
        };
        transaction.execute(
            &format!(
                "INSERT INTO {table}(scene, turn, stage, due)
             VALUES (?1, ?2, 0, date('now','localtime','+1 day'))
             ON CONFLICT(scene, turn) DO UPDATE SET
               due = date('now','localtime', CASE
                   WHEN NOT ?3 THEN '+1 day'
                   WHEN stage = 0 THEN '+3 days'
                   WHEN stage = 1 THEN '+7 days'
                   WHEN stage = 2 THEN '+14 days'
                   WHEN stage = 3 THEN '+30 days'
                   ELSE '+60 days' END),
               stage = CASE WHEN NOT ?3 THEN 0 ELSE min(stage+1, 5) END
             WHERE (?4 AND due <= date('now','localtime')) OR (NOT ?4 AND NOT ?3)"
            ),
            params![
                attempt.scene,
                update.index as i64,
                update.correct,
                update.reviewing
            ],
        )?;
    }
    transaction.commit()
}

pub fn assess(
    connection: &Connection,
    id: &str,
    scene: &str,
    activity: &str,
    score: u8,
) -> Result<()> {
    connection.execute(
        "INSERT INTO self_assessments(id, scene, activity, score) VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT(id) DO NOTHING",
        params![id, scene, activity, score],
    )?;
    Ok(())
}

#[derive(Serialize)]
pub struct Diagnostics {
    measurements: Vec<Measurement>,
    reflections: Vec<Reflection>,
    days: Vec<String>,
}

#[derive(Serialize)]
struct Measurement {
    scene: String,
    activity: String,
    first: String,
    last: String,
    at: String,
}

#[derive(Serialize)]
struct Reflection {
    scene: String,
    activity: String,
    score: u8,
}

pub fn diagnostics(connection: &Connection, lang: &str) -> Result<Diagnostics> {
    let prefix = format!("{lang}-%");
    let mut measurements = connection.prepare(
        "WITH results AS (
            SELECT scene, CASE
                WHEN activity LIKE 'review/%' THEN replace(activity, 'review/', 'turn/')
                WHEN activity LIKE 'review-exercise/%' THEN replace(activity, 'review-exercise/', 'exercise/')
                ELSE activity END AS kind, outcome, at, rowid
            FROM attempts WHERE scene LIKE ?1 AND outcome IN ('correct','retry','correction')
        ), history AS (
            SELECT scene, kind, at, rowid, outcome,
                first_value(outcome) OVER (PARTITION BY scene, kind ORDER BY at, rowid) AS first,
                row_number() OVER (PARTITION BY scene, kind ORDER BY at DESC, rowid DESC) AS recent
            FROM results
        )
        SELECT scene, kind, first, outcome, at FROM history WHERE recent = 1 ORDER BY at DESC, rowid DESC",
    )?;
    let measurements = measurements
        .query_map([&prefix], |row| {
            Ok(Measurement {
                scene: row.get(0)?,
                activity: row.get(1)?,
                first: row.get(2)?,
                last: row.get(3)?,
                at: row.get(4)?,
            })
        })?
        .collect::<Result<_>>()?;

    let mut reflections = connection.prepare(
        "WITH latest AS (
            SELECT scene, activity, score, at, rowid,
                   row_number() OVER (PARTITION BY scene, activity ORDER BY at DESC, rowid DESC) AS recent
            FROM self_assessments WHERE scene LIKE ?1
         )
         SELECT scene, activity, score FROM latest WHERE recent = 1 ORDER BY at DESC, rowid DESC",
    )?;
    let reflections = reflections
        .query_map([&prefix], |row| {
            Ok(Reflection {
                scene: row.get(0)?,
                activity: row.get(1)?,
                score: row.get(2)?,
            })
        })?
        .collect::<Result<_>>()?;

    let mut days = connection.prepare(
        "SELECT DISTINCT date(at,'localtime') FROM (
           SELECT at FROM attempts WHERE scene LIKE ?1
           UNION ALL SELECT at FROM self_assessments WHERE scene LIKE ?1
           UNION ALL SELECT at FROM recordings WHERE scene LIKE ?1
           UNION ALL SELECT at FROM field_attempts WHERE lang = ?2
         ) WHERE date(at,'localtime') >= date('now','localtime','-27 days') ORDER BY 1",
    )?;
    let days = days
        .query_map(params![&prefix, lang], |row| row.get(0))?
        .collect::<Result<_>>()?;
    Ok(Diagnostics {
        measurements,
        reflections,
        days,
    })
}

#[derive(Serialize)]
pub struct Recording {
    id: String,
    scene: String,
    turn: usize,
    at: String,
    duration_ms: i64,
}

#[derive(Serialize)]
pub struct RecordingPage {
    items: Vec<Recording>,
    more: bool,
}

pub fn recording_list(connection: &Connection, lang: &str, page: u32) -> Result<RecordingPage> {
    let mut query = connection.prepare(
        "SELECT id, scene, turn, at, length(audio)/32 FROM recordings
         WHERE scene LIKE ?1 ORDER BY at DESC, rowid DESC LIMIT 21 OFFSET ?2",
    )?;
    let mut items = query
        .query_map(params![format!("{lang}-%"), i64::from(page) * 20], |row| {
            Ok(Recording {
                id: row.get(0)?,
                scene: row.get(1)?,
                turn: row.get::<_, i64>(2)? as usize,
                at: row.get(3)?,
                duration_ms: row.get(4)?,
            })
        })?
        .collect::<Result<Vec<_>>>()?;
    let more = items.len() > 20;
    items.truncate(20);
    Ok(RecordingPage { items, more })
}

pub fn save_recording(
    connection: &Connection,
    id: &str,
    scene: &str,
    turn: usize,
    audio: &[u8],
) -> Result<()> {
    connection.execute(
        "INSERT INTO recordings(id, scene, turn, audio) VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT(id) DO NOTHING",
        params![id, scene, turn as i64, audio],
    )?;
    Ok(())
}

pub fn recording(connection: &Connection, id: &str) -> Result<Vec<u8>> {
    connection.query_row("SELECT audio FROM recordings WHERE id=?1", [id], |row| {
        row.get(0)
    })
}

pub fn delete_recording(connection: &Connection, id: &str) -> Result<()> {
    connection.execute("DELETE FROM recordings WHERE id=?1", [id])?;
    Ok(())
}

#[derive(Serialize, Clone)]
pub struct DueItem {
    pub item: String,
    pub due: String,
    pub interval: i64,
    pub reps: i64,
    pub lapses: i64,
}

#[derive(Serialize)]
pub struct ItemStats {
    pub total: i64,
    pub due: i64,
    pub learned: i64,
    pub reviews_today: i64,
    pub reviews_week: i64,
}

#[derive(Serialize, Clone)]
pub struct LessonState {
    pub lesson: String,
    pub completed: bool,
    pub tasks_done: i64,
    pub tasks_total: i64,
    pub correct: i64,
}

pub fn introduce_items(connection: &Connection, lang: &str, items: &[String]) -> Result<()> {
    for item in items {
        connection.execute(
            "INSERT INTO item_reviews(item, lang, due)
             VALUES (?1, ?2, date('now','localtime'))
             ON CONFLICT(item) DO NOTHING",
            params![item, lang],
        )?;
    }
    Ok(())
}

pub fn review_item(
    connection: &mut Connection,
    id: &str,
    item: &str,
    lang: &str,
    grade: u8,
) -> Result<DueItem> {
    let transaction = connection.transaction()?;
    let (interval, ease, reps, lapses): (i64, f64, i64, i64) = transaction.query_row(
        "SELECT interval, ease, reps, lapses FROM item_reviews WHERE item=?1 AND lang=?2",
        params![item, lang],
        |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
    )?;
    let inserted = transaction.execute(
        "INSERT INTO item_review_events(id, item, lang, grade) VALUES (?1, ?2, ?3, ?4)
         ON CONFLICT(id) DO NOTHING",
        params![id, item, lang, grade],
    )?;
    if inserted == 0 {
        let original: (String, String, u8) = transaction.query_row(
            "SELECT item, lang, grade FROM item_review_events WHERE id=?1",
            [id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )?;
        if original != (item.to_string(), lang.to_string(), grade) {
            return Err(rusqlite::Error::InvalidQuery);
        }
        let due = transaction.query_row(
            "SELECT due, interval, reps, lapses FROM item_reviews WHERE item=?1",
            [item],
            |row| {
                Ok(DueItem {
                    item: item.to_string(),
                    due: row.get(0)?,
                    interval: row.get(1)?,
                    reps: row.get(2)?,
                    lapses: row.get(3)?,
                })
            },
        )?;
        return Ok(due);
    }
    let (interval, ease, lapses) = match grade {
        0 => (1, (ease - 0.2).max(1.3), lapses + 1),
        1 => (
            (interval as f64 * 1.2).round().max(1.0) as i64,
            (ease - 0.15).max(1.3),
            lapses,
        ),
        3 => (
            if interval == 0 {
                2
            } else if interval == 1 {
                5
            } else {
                (interval as f64 * ease * 1.3).round() as i64
            },
            (ease + 0.1).min(3.0),
            lapses,
        ),
        _ => (
            if interval == 0 {
                1
            } else if interval == 1 {
                3
            } else {
                (interval as f64 * ease).round() as i64
            },
            ease,
            lapses,
        ),
    };
    let interval = interval.clamp(1, 365);
    let reps = reps + 1;
    transaction.execute(
        "INSERT INTO item_reviews(item, lang, interval, ease, reps, lapses, due, last, first)
         VALUES (?1, ?7, ?2, ?3, ?4, ?5, date('now','localtime',?6), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
         ON CONFLICT(item) DO UPDATE SET
           interval=?2, ease=?3, reps=?4, lapses=?5,
           due=date('now','localtime',?6), last=CURRENT_TIMESTAMP",
        params![item, interval, ease, reps, lapses, format!("+{interval} days"), lang],
    )?;
    let due = transaction.query_row(
        "SELECT due FROM item_reviews WHERE item=?1",
        [item],
        |row| row.get(0),
    )?;
    transaction.commit()?;
    Ok(DueItem {
        item: item.to_string(),
        due,
        interval,
        reps,
        lapses,
    })
}

pub fn due_items(connection: &Connection, lang: &str, limit: usize) -> Result<Vec<DueItem>> {
    let mut query = connection.prepare(
        "SELECT item, due, interval, reps, lapses FROM item_reviews
         WHERE lang=?1 AND due <= date('now','localtime')
         ORDER BY due, item LIMIT ?2",
    )?;
    query
        .query_map(params![lang, limit as i64], |row| {
            Ok(DueItem {
                item: row.get(0)?,
                due: row.get(1)?,
                interval: row.get(2)?,
                reps: row.get(3)?,
                lapses: row.get(4)?,
            })
        })?
        .collect()
}

pub fn item_stats(connection: &Connection, lang: &str) -> Result<ItemStats> {
    connection.query_row(
        "SELECT
           count(*),
           coalesce(sum(due <= date('now','localtime')), 0),
           coalesce(sum(reps > 0), 0),
            (SELECT count(*) FROM item_review_events WHERE lang=?1 AND date(at,'localtime') = date('now','localtime')),
            (SELECT count(*) FROM item_review_events WHERE lang=?1 AND date(at,'localtime') >= date('now','localtime','-6 days'))
         FROM item_reviews WHERE lang=?1",
        [lang],
        |row| {
            Ok(ItemStats {
                total: row.get(0)?,
                due: row.get(1)?,
                learned: row.get(2)?,
                reviews_today: row.get(3)?,
                reviews_week: row.get(4)?,
            })
        },
    )
}

pub fn lesson_states(connection: &Connection, lang: &str) -> Result<Vec<LessonState>> {
    let mut query = connection.prepare(
        "SELECT lesson, completed, tasks_done, tasks_total, correct
         FROM lesson_progress WHERE lang=?1",
    )?;
    query
        .query_map([lang], |row| {
            Ok(LessonState {
                lesson: row.get(0)?,
                completed: row.get::<_, i64>(1)? == 1,
                tasks_done: row.get(2)?,
                tasks_total: row.get(3)?,
                correct: row.get(4)?,
            })
        })?
        .collect()
}

pub fn record_task(
    connection: &Connection,
    id: &str,
    lesson: &str,
    lang: &str,
    task: usize,
    kind: &str,
    correct: bool,
    counted: bool,
    total: usize,
    duration_seconds: u32,
) -> Result<LessonState> {
    connection.execute(
        "INSERT INTO task_attempts(id, lesson, task, kind, correct, counted, duration_seconds)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7) ON CONFLICT(id) DO NOTHING",
        params![
            id,
            lesson,
            task as i64,
            kind,
            correct,
            counted,
            duration_seconds.min(600)
        ],
    )?;
    connection.execute(
        "INSERT INTO lesson_progress(lesson, lang, tasks_total)
         VALUES (?1, ?2, ?3) ON CONFLICT(lesson) DO NOTHING",
        params![lesson, lang, total as i64],
    )?;
    connection.execute(
        "UPDATE lesson_progress SET
           tasks_total = ?2,
           tasks_done = (SELECT count(DISTINCT task) FROM task_attempts WHERE lesson=?1 AND counted=1),
           correct = (SELECT count(DISTINCT task) FROM task_attempts WHERE lesson=?1 AND correct=1),
           completed = CASE WHEN (SELECT count(DISTINCT task) FROM task_attempts WHERE lesson=?1 AND counted=1) >= ?2
                            THEN 1 ELSE completed END,
           finished = CASE WHEN (SELECT count(DISTINCT task) FROM task_attempts WHERE lesson=?1 AND counted=1) >= ?2
                           THEN coalesce(finished, CURRENT_TIMESTAMP) ELSE finished END
         WHERE lesson=?1",
        params![lesson, total as i64],
    )?;
    let state = connection.query_row(
        "SELECT lesson, completed, tasks_done, tasks_total, correct FROM lesson_progress WHERE lesson=?1",
        [lesson],
        |row| {
            Ok(LessonState {
                lesson: row.get(0)?,
                completed: row.get::<_, i64>(1)? == 1,
                tasks_done: row.get(2)?,
                tasks_total: row.get(3)?,
                correct: row.get(4)?,
            })
        },
    )?;
    Ok(state)
}

pub fn streak(connection: &Connection, lang: &str) -> Result<i64> {
    let prefix = format!("{lang}-%");
    let mut query = connection.prepare(
        "SELECT DISTINCT day FROM (
           SELECT date(at,'localtime') AS day FROM task_attempts WHERE lesson LIKE ?1
           UNION ALL SELECT date(at,'localtime') FROM attempts WHERE scene LIKE ?1
           UNION ALL SELECT date(at,'localtime') FROM field_attempts WHERE lang=?2
         ) ORDER BY day DESC LIMIT 400",
    )?;
    let days = query
        .query_map(params![prefix, lang], |row| row.get::<_, String>(0))?
        .collect::<Result<Vec<_>>>()?;
    let mut count = 0;
    let mut expected = connection.query_row("SELECT date('now','localtime')", [], |row| {
        row.get::<_, String>(0)
    })?;
    for day in days {
        if day == expected {
            count += 1;
            expected = connection.query_row("SELECT date(?1, '-1 day')", [&day], |row| {
                row.get::<_, String>(0)
            })?;
        } else if day < expected {
            break;
        }
    }
    Ok(count)
}

pub fn minutes_week(connection: &Connection, lang: &str) -> Result<i64> {
    connection.query_row(
        "SELECT coalesce(sum(t.duration_seconds), 0) / 60 FROM task_attempts t
         JOIN lesson_progress l ON l.lesson=t.lesson
         WHERE l.lang=?1 AND date(t.at,'localtime') >= date('now','localtime','-6 days')",
        [lang],
        |row| row.get(0),
    )
}

pub fn seconds_total(connection: &Connection, lang: &str) -> Result<i64> {
    connection.query_row(
        "SELECT coalesce(sum(t.duration_seconds), 0) FROM task_attempts t
         JOIN lesson_progress l ON l.lesson=t.lesson WHERE l.lang=?1",
        [lang],
        |row| row.get(0),
    )
}

pub fn task_count(connection: &Connection, lang: &str) -> Result<i64> {
    connection.query_row(
        "SELECT count(*) FROM (
            SELECT t.lesson, t.task FROM task_attempts t
            JOIN lesson_progress l ON l.lesson=t.lesson
            WHERE l.lang=?1 AND t.counted=1 GROUP BY t.lesson, t.task
         )",
        [lang],
        |row| row.get(0),
    )
}

pub fn completed_tasks(connection: &Connection, lesson: &str) -> Result<Vec<usize>> {
    let mut query = connection.prepare(
        "SELECT DISTINCT task FROM task_attempts WHERE lesson=?1 AND counted=1 ORDER BY task",
    )?;
    query
        .query_map([lesson], |row| {
            row.get::<_, i64>(0).map(|task| task as usize)
        })?
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn counted_tasks_and_measured_time_are_per_language() {
        let db = open(Path::new(":memory:")).unwrap();
        record_task(&db, "a", "lb-a1-d1", "lb", 0, "choice", true, true, 2, 42).unwrap();
        record_task(&db, "b", "lb-a1-d1", "lb", 1, "choice", false, false, 2, 33).unwrap();
        record_task(&db, "c", "lb-a1-d2", "lb", 0, "choice", true, true, 2, 51).unwrap();
        record_task(&db, "d", "da-a1-d1", "da", 0, "choice", true, true, 2, 60).unwrap();
        record_task(&db, "a", "lb-a1-d1", "lb", 0, "choice", true, true, 2, 600).unwrap();
        assert_eq!(task_count(&db, "lb").unwrap(), 2);
        assert_eq!(seconds_total(&db, "lb").unwrap(), 126);
        assert_eq!(minutes_week(&db, "lb").unwrap(), 2);
        assert_eq!(seconds_total(&db, "da").unwrap(), 60);
    }

    #[test]
    fn review_request_is_idempotent_and_requires_introduction() {
        let mut db = open(Path::new(":memory:")).unwrap();
        assert!(review_item(&mut db, "r0", "lb-word", "lb", 2).is_err());
        introduce_items(&db, "lb", &["lb-word".to_string()]).unwrap();
        let first = review_item(&mut db, "r1", "lb-word", "lb", 2).unwrap();
        let repeat = review_item(&mut db, "r1", "lb-word", "lb", 2).unwrap();
        assert_eq!(first.reps, 1);
        assert_eq!(repeat.reps, 1);
        assert_eq!(item_stats(&db, "lb").unwrap().reviews_today, 1);
        assert!(review_item(&mut db, "r1", "lb-word", "lb", 3).is_err());
    }
}
