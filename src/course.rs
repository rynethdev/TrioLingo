use serde::{Deserialize, Serialize};
use unicode_normalization::UnicodeNormalization;

#[derive(Deserialize, Serialize)]
pub struct Scene {
    pub id: String,
    pub lang: String,
    pub level: String,
    #[serde(default = "first_week")]
    pub week: usize,
    #[serde(default)]
    pub checkpoint: bool,
    pub title: String,
    pub goal: String,
    pub setup: String,
    pub dialogue: Vec<Line>,
    pub listening: Quiz,
    pub turns: Vec<Turn>,
    pub reading: Reading,
    pub writing: Writing,
    #[serde(default)]
    pub exercises: Vec<Exercise>,
}

fn first_week() -> usize {
    1
}

#[derive(Clone, Deserialize, Serialize)]
pub struct Exercise {
    pub kind: String,
    pub prompt: String,
    pub answer: String,
    pub explanation: String,
}

impl Scene {
    pub fn exercise(&self, index: usize) -> Option<Exercise> {
        if index == 0 {
            let line = self.dialogue.get(1)?;
            return Some(Exercise {
                kind: "dictation".into(),
                prompt: "Escucha y escribe la frase.".into(),
                answer: line.text.clone(),
                explanation: format!("Significado: {}", line.es),
            });
        }
        self.exercises.get(index - 1).cloned()
    }
}

#[derive(Deserialize, Serialize)]
pub struct Line {
    pub speaker: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub lang: Option<String>,
    pub text: String,
    pub es: String,
}

#[derive(Deserialize, Serialize)]
pub struct Quiz {
    pub prompt: String,
    pub choices: Vec<String>,
    pub answer: usize,
}

#[derive(Deserialize, Serialize)]
pub struct Reading {
    pub text: String,
    #[serde(flatten)]
    pub quiz: Quiz,
}

#[derive(Deserialize, Serialize)]
pub struct Turn {
    pub prompt: String,
    pub es: String,
    pub model: String,
    pub model_es: String,
    pub accepted: Vec<String>,
    pub tip: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub mistakes: Vec<Mistake>,
}

#[derive(Deserialize, Serialize)]
pub struct Mistake {
    pub text: String,
    pub explanation: String,
}

#[derive(Deserialize, Serialize)]
pub struct Writing {
    pub prompt: String,
    pub model: String,
    pub rubric: String,
}

#[derive(Serialize)]
pub struct Feedback {
    pub status: &'static str,
    pub example: String,
    pub explanation: String,
}

pub fn normalize(text: &str) -> String {
    text.nfc()
        .flat_map(char::to_lowercase)
        .filter_map(|character| match character {
            '’' | 'ʼ' | '\'' => None,
            value if value.is_alphanumeric() => Some(value),
            _ => Some(' '),
        })
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

pub fn evaluate_turn(turn: &Turn, text: &str) -> Feedback {
    let text = normalize(text);
    let matches = std::iter::once(&turn.model)
        .chain(&turn.accepted)
        .any(|variant| normalize(variant) == text);
    let mistake = turn
        .mistakes
        .iter()
        .find(|mistake| normalize(&mistake.text) == text);
    Feedback {
        status: if matches {
            "correct"
        } else if mistake.is_some() {
            "correction"
        } else {
            "reference"
        },
        example: turn.model.clone(),
        explanation: mistake
            .map_or_else(|| turn.tip.clone(), |mistake| mistake.explanation.clone()),
    }
}

pub fn evaluate_quiz(quiz: &Quiz, choice: usize) -> Feedback {
    Feedback {
        status: if choice == quiz.answer {
            "correct"
        } else {
            "retry"
        },
        example: quiz.choices[quiz.answer].clone(),
        explanation: String::new(),
    }
}

pub fn evaluate_exercise(exercise: &Exercise, text: &str) -> Feedback {
    Feedback {
        status: if normalize(&exercise.answer) == normalize(text) {
            "correct"
        } else {
            "correction"
        },
        example: exercise.answer.clone(),
        explanation: exercise.explanation.clone(),
    }
}
