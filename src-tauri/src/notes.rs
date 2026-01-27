use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use anyhow::{Result, Context};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MeetingNote {
    pub timestamp: DateTime<Utc>,
    pub key_points: Vec<String>,
    pub decisions: Vec<String>,
    pub action_items: Vec<String>,
    pub transcript: Vec<(String, String)>, // (Timestamp, Text)
}

impl MeetingNote {
    pub fn new() -> Self {
        Self {
            timestamp: Utc::now(),
            key_points: vec![],
            decisions: vec![],
            action_items: vec![],
            transcript: vec![],
        }
    }

    pub fn add_transcript_segment(&mut self, text: String, timestamp: String) {
        self.transcript.push((timestamp, text));
    }

    pub fn format_markdown(&self) -> String {
        let date_str = self.timestamp.format("%Y-%m-%d %H:%M").to_string();
        let mut md = format!("# Meeting – {}\n\n", date_str);

        md.push_str("## Key Points\n");
        if self.key_points.is_empty() {
             md.push_str("_No key points recorded._\n");
        } else {
            for point in &self.key_points {
                md.push_str(&format!("- {}\n", point));
            }
        }
        md.push_str("\n");

        md.push_str("## Decisions\n");
        if self.decisions.is_empty() {
             md.push_str("_No decisions recorded._\n");
        } else {
            for decision in &self.decisions {
                md.push_str(&format!("- {}\n", decision));
            }
        }
        md.push_str("\n");
        
        md.push_str("## Action Items\n");
        if self.action_items.is_empty() {
             md.push_str("_No action items recorded._\n");
        } else {
            for item in &self.action_items {
                md.push_str(&format!("- [ ] {}\n", item));
            }
        }
        md.push_str("\n");

        md.push_str("## Transcript\n");
        for (time, text) in &self.transcript {
            md.push_str(&format!("**[{}]** {}\n\n", time, text));
        }

        md
    }

    pub fn save_to_file(&self, base_dir: Option<PathBuf>) -> Result<PathBuf> {
        let dir = base_dir.unwrap_or_else(|| PathBuf::from("meetings"));
        if !dir.exists() {
            fs::create_dir_all(&dir).context("Failed to create meetings directory")?;
        }

        let filename = format!("meeting_{}.md", self.timestamp.format("%Y%m%d_%H%M%S"));
        let path = dir.join(filename);
        
        let content = self.format_markdown();
        fs::write(&path, content).context("Failed to write meeting note file")?;
        
        Ok(path)
    }
}
