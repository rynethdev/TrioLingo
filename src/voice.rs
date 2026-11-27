use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};

const MIN_SAMPLES: usize = 4_000;
const MAX_SAMPLES: usize = 960_000;

#[derive(Default)]
pub struct Speech {
    loaded: Option<(String, WhisperContext)>,
}

pub fn model_path(directory: &Path, lang: &str) -> PathBuf {
    directory.join(format!("{lang}.bin"))
}

impl Speech {
    pub fn transcribe(
        &mut self,
        path: &Path,
        lang: &str,
        samples: &[f32],
    ) -> Result<String, &'static str> {
        if self
            .loaded
            .as_ref()
            .is_none_or(|(loaded, _)| loaded != lang)
        {
            self.loaded = None;
            let context =
                WhisperContext::new_with_params(path, WhisperContextParameters::default())
                    .map_err(|_| "El modelo de voz no pudo abrirse.")?;
            self.loaded = Some((lang.into(), context));
        }
        let mut state = self
            .loaded
            .as_ref()
            .unwrap()
            .1
            .create_state()
            .map_err(|_| "No se pudo iniciar la transcripción.")?;
        let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });
        params.set_language(Some(lang));
        params.set_no_context(true);
        params.set_no_timestamps(true);
        params.set_print_realtime(false);
        params.set_print_progress(false);
        params.set_print_timestamps(false);
        params.set_n_threads(4);
        let deadline = Instant::now() + Duration::from_secs(40);
        params.set_abort_callback_safe(move || Instant::now() >= deadline);
        state
            .full(params, samples)
            .map_err(|_| "No se pudo transcribir. Prueba un clip más corto.")?;
        let transcript = state
            .as_iter()
            .filter(|segment| segment.no_speech_probability() < 0.7)
            .filter_map(|segment| segment.to_str().ok())
            .map(str::trim)
            .collect::<Vec<_>>()
            .join(" ");
        if !transcript.chars().any(char::is_alphabetic) {
            return Err("No se entendió voz en el clip. Vuelve a grabar o escribe la respuesta.");
        }
        Ok(transcript)
    }
}

pub fn decode_audio(raw: &[u8]) -> Result<Vec<f32>, &'static str> {
    if raw.len() % 2 != 0 || !(MIN_SAMPLES * 2..=MAX_SAMPLES * 2).contains(&raw.len()) {
        return Err("Graba entre un cuarto de segundo y un minuto.");
    }
    let samples = raw
        .chunks_exact(2)
        .map(|bytes| f32::from(i16::from_le_bytes([bytes[0], bytes[1]])) / 32768.)
        .collect::<Vec<_>>();
    let voiced = samples.chunks(1_600).any(|window| {
        window.iter().map(|sample| sample * sample).sum::<f32>() / window.len() as f32 > 0.00001
    });
    if !voiced {
        return Err("No se detectó voz. Acércate al micrófono y vuelve a intentarlo.");
    }
    Ok(samples)
}
