use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::course::{Feedback, normalize};

#[derive(Deserialize, Serialize)]
pub struct Course {
    pub version: u32,
    pub units: Vec<Unit>,
    pub items: Vec<Item>,
    #[serde(default)]
    pub roadmap: Vec<Stage>,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Stage {
    pub level: String,
    pub start: usize,
    pub end: usize,
    pub hours: usize,
    pub title: String,
    pub focus: String,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Unit {
    pub id: String,
    pub lang: String,
    pub level: String,
    pub week: usize,
    pub title: String,
    pub can_do: String,
    pub scene: String,
    #[serde(default)]
    pub editorial_status: Option<String>,
    pub lessons: Vec<Lesson>,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Lesson {
    pub id: String,
    pub lang: String,
    pub level: String,
    pub week: usize,
    pub day: usize,
    pub unit: String,
    pub title: String,
    pub goal: String,
    pub tasks: Vec<Task>,
    #[serde(default)]
    pub items: Vec<String>,
    #[serde(default)]
    pub checkpoint: bool,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Task {
    pub kind: String,
    pub prompt: String,
    #[serde(default)]
    pub answer: Option<String>,
    #[serde(default)]
    pub accepted: Vec<String>,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub explain: Option<String>,
    #[serde(default)]
    pub choices: Vec<String>,
    #[serde(default)]
    pub audio: Option<String>,
    #[serde(default)]
    pub items: Vec<String>,
    #[serde(flatten)]
    pub extra: serde_json::Map<String, Value>,
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Item {
    pub id: String,
    pub lang: String,
    pub level: String,
    pub text: String,
    pub translation: String,
    #[serde(default)]
    pub example: String,
    #[serde(default)]
    pub example_es: String,
    #[serde(default)]
    pub kind: String,
    #[serde(default)]
    pub audio: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
}

/// Graded outcome for one task inside a lesson.
pub struct Grade {
    pub feedback: Feedback,
    pub correct: bool,
    pub graded: bool,
}

impl Course {
    pub fn lesson(&self, id: &str) -> Option<&Lesson> {
        self.units
            .iter()
            .flat_map(|unit| &unit.lessons)
            .find(|lesson| lesson.id == id)
    }

    pub fn item(&self, id: &str) -> Option<&Item> {
        self.items.iter().find(|item| item.id == id)
    }

    /// Lessons for one language in study order.
    pub fn lessons(&self, lang: &str) -> Vec<&Lesson> {
        let mut lessons = self
            .units
            .iter()
            .filter(|unit| unit.lang == lang)
            .flat_map(|unit| &unit.lessons)
            .collect::<Vec<_>>();
        lessons.sort_by_key(|lesson| (lesson.week, lesson.day));
        lessons
    }

    pub fn units(&self, lang: &str) -> Vec<&Unit> {
        let mut units = self
            .units
            .iter()
            .filter(|unit| unit.lang == lang)
            .collect::<Vec<_>>();
        units.sort_by_key(|unit| unit.week);
        units
    }

    pub fn first_unfinished<'a>(
        &'a self,
        lang: &str,
        done: &std::collections::HashSet<String>,
    ) -> Option<&'a Lesson> {
        self.lessons(lang)
            .into_iter()
            .find(|lesson| !done.contains(&lesson.id))
    }
}

pub fn evaluate(task: &Task, text: &str, choice: Option<usize>) -> Grade {
    match task.kind.as_str() {
        "choice" | "reading" => {
            let answer = task
                .answer
                .as_deref()
                .and_then(|value| value.parse::<usize>().ok());
            let picked = choice.filter(|value| *value < task.choices.len());
            let correct =
                matches!((answer, picked), (Some(answer), Some(picked)) if answer == picked);
            let model = answer
                .and_then(|index| task.choices.get(index))
                .cloned()
                .unwrap_or_default();
            Grade {
                feedback: Feedback {
                    status: if correct { "correct" } else { "retry" },
                    example: model,
                    explanation: task.explain.clone().unwrap_or_default(),
                },
                correct,
                graded: true,
            }
        }
        "cloze" | "dictation" | "translation" => {
            let typed = normalize(text);
            let answer = task.answer.as_deref().unwrap_or_default();
            let correct = answer
                .split('|')
                .map(normalize)
                .any(|variant| !variant.is_empty() && variant == typed);
            Grade {
                feedback: Feedback {
                    status: if correct { "correct" } else { "correction" },
                    example: answer.replace('|', " / "),
                    explanation: task.explain.clone().unwrap_or_default(),
                },
                correct,
                graded: true,
            }
        }
        "speaking" => {
            let typed = normalize(text);
            let model = task.model.as_deref().unwrap_or_default();
            let correct = std::iter::once(model)
                .chain(task.accepted.iter().map(String::as_str))
                .any(|variant| normalize(variant) == typed);
            Grade {
                feedback: Feedback {
                    status: if correct { "correct" } else { "reference" },
                    example: model.to_string(),
                    explanation: task.explain.clone().unwrap_or_default(),
                },
                correct,
                graded: true,
            }
        }
        "writing" => Grade {
            feedback: Feedback {
                status: "reference",
                example: task.model.clone().unwrap_or_default(),
                explanation: task.explain.clone().unwrap_or_default(),
            },
            correct: false,
            graded: false,
        },
        _ => Grade {
            feedback: Feedback {
                status: "reference",
                example: String::new(),
                explanation: task.explain.clone().unwrap_or_default(),
            },
            correct: false,
            graded: false,
        },
    }
}

pub fn level_hours(level: &str) -> (usize, usize) {
    match level {
        "A1" => (90, 100),
        "A2" => (180, 220),
        "B1" => (350, 400),
        "B2" => (500, 580),
        "C1" => (700, 790),
        "C2" => (1000, 1200),
        _ => (0, 0),
    }
}

pub fn total_weeks() -> usize {
    200
}
