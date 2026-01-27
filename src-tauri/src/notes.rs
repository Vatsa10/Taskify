use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct MeetingNote {
    pub timestamp: DateTime<Utc>,
    pub key_points: Vec<String>,
    pub decisions: Vec<String>,
    pub action_items: Vec<String>,
    pub transcript: String,
}

impl MeetingNote {
    pub fn new() -> Self {
        Self {
            timestamp: Utc::now(),
            key_points: vec![],
            decisions: vec![],
            action_items: vec![],
            transcript: String::new(),
        }
    }
}
