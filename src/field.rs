use rusqlite::{Connection, Result, params};
use serde::{Deserialize, Serialize};

use crate::course::Quiz;

#[derive(Deserialize)]
pub struct Catalog {
    cases: Vec<Item>,
    checks: Vec<Check>,
    workshop: Vec<Item>,
}

#[derive(Deserialize)]
struct Item {
    id: String,
    lang: String,
}

#[derive(Deserialize)]
struct Check {
    id: String,
    lang: String,
    listening: Questions,
    reading: Questions,
}

#[derive(Deserialize)]
struct Questions {
    questions: Vec<Quiz>,
}

impl Questions {
    fn score(&self, selections: &[usize; 2]) -> Option<u8> {
        if self.questions.len() != selections.len()
            || self
                .questions
                .iter()
                .zip(selections)
                .any(|(quiz, &choice)| choice >= quiz.choices.len())
        {
            return None;
        }
        Some(
            self.questions
                .iter()
                .zip(selections)
                .filter(|(quiz, choice)| quiz.answer == **choice)
                .count() as u8,
        )
    }
}

#[derive(Deserialize)]
pub struct Submission {
    pub id: String,
    pub lang: String,
    key: String,
    #[serde(flatten)]
    pub result: Input,
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "kebab-case")]
pub enum Input {
    Coach {
        score: u8,
        variant: u8,
    },
    Monthly {
        listening: [usize; 2],
        reading: [usize; 2],
        speaking: u8,
        writing: u8,
    },
    Workshop {
        score: u8,
    },
    Daily {
        minutes: u8,
    },
    Dates {
        score: u8,
    },
}

#[derive(Serialize)]
pub struct Outcome {
    kind: &'static str,
    pub scores: [u8; 4],
    variant: u8,
}

impl Catalog {
    pub fn evaluate(&self, submission: &Submission) -> Option<Outcome> {
        let matches = |item: &Item| item.id == submission.key && item.lang == submission.lang;
        let (kind, scores, variant) = match submission.result {
            Input::Coach { score, variant }
                if score <= 3 && variant < 2 && self.cases.iter().any(matches) =>
            {
                ("coach", [score, 0, 0, 0], variant)
            }
            Input::Workshop { score } if score <= 1 && self.workshop.iter().any(matches) => {
                ("workshop", [score, 0, 0, 0], 0)
            }
            Input::Daily { minutes }
                if matches!(minutes, 10 | 20 | 30) && submission.key == "session" =>
            {
                ("daily", [minutes, 0, 0, 0], 0)
            }
            Input::Dates { score } if score <= 3 && submission.key == "dates" => {
                ("dates", [score, 0, 0, 0], 0)
            }
            Input::Monthly {
                listening,
                reading,
                speaking,
                writing,
            } if speaking <= 2 && writing <= 2 => {
                let check = self
                    .checks
                    .iter()
                    .find(|check| check.id == submission.key && check.lang == submission.lang)?;
                (
                    "monthly",
                    [
                        check.listening.score(&listening)?,
                        check.reading.score(&reading)?,
                        speaking,
                        writing,
                    ],
                    0,
                )
            }
            _ => return None,
        };
        Some(Outcome {
            kind,
            scores,
            variant,
        })
    }
}

pub fn store(connection: &Connection, submission: &Submission, score: &Outcome) -> Result<()> {
    let [first, second, third, fourth] = score.scores;
    connection.execute(
        "INSERT INTO field_attempts(id, lang, mode, exercise, score1, score2, score3, score4, variant)
        VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9) ON CONFLICT(id) DO NOTHING",
        params![submission.id, submission.lang, score.kind, submission.key, first, second, third, fourth, score.variant],
    )?;
    Ok(())
}

#[derive(Serialize)]
pub struct History {
    items: Vec<Entry>,
    started_on: Option<String>,
    today: String,
}

#[derive(Serialize)]
struct Entry {
    key: String,
    kind: String,
    scores: [u8; 4],
    variant: u8,
    day: String,
}

pub fn history(connection: &Connection, lang: &str) -> Result<History> {
    let (started_on, today) = connection.query_row(
        "SELECT min(date(at,'localtime')), date('now','localtime') FROM (
          SELECT at FROM attempts WHERE scene LIKE ?1 UNION ALL SELECT at FROM field_attempts WHERE lang=?2
        )", params![format!("{lang}-%"), lang], |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    let mut statement = connection.prepare(
        "WITH ranked AS (
            SELECT exercise, mode, score1, score2, score3, score4, variant, at, rowid,
                   row_number() OVER (PARTITION BY mode, exercise ORDER BY at DESC, rowid DESC) AS recent
            FROM field_attempts WHERE lang=?1
         )
         SELECT exercise, mode, score1, score2, score3, score4, variant, date(at,'localtime')
         FROM ranked WHERE recent <= 28 ORDER BY at DESC, rowid DESC",
    )?;
    let items = statement
        .query_map([lang], |row| {
            Ok(Entry {
                key: row.get(0)?,
                kind: row.get(1)?,
                scores: [row.get(2)?, row.get(3)?, row.get(4)?, row.get(5)?],
                variant: row.get(6)?,
                day: row.get(7)?,
            })
        })?
        .collect::<Result<_>>()?;
    Ok(History {
        items,
        started_on,
        today,
    })
}
