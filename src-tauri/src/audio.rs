
use anyhow::{anyhow, Context, Result};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Stream, StreamConfig, SampleFormat};
use ringbuf::{HeapRb, Producer, SharedRb, Consumer};
use std::sync::Arc;
use tracing::{error, info};

pub struct AudioSystem {
    producer: Option<Producer<f32, Arc<SharedRb<f32, Vec<std::mem::MaybeUninit<f32>>>>>>,
}

impl AudioSystem {
    pub fn new() -> (Self, Consumer<f32, Arc<SharedRb<f32, Vec<std::mem::MaybeUninit<f32>>>>>) {
         // Buffer size for ~5 seconds of 48kHz stereo
        let rb = HeapRb::<f32>::new(48000 * 2 * 5);
        let (producer, consumer) = rb.split();
        (Self { producer: Some(producer) }, consumer)
    }

    pub fn start_capture(&mut self) -> Result<(Stream, u32, u16)> {
        let producer = self.producer.take().ok_or_else(|| anyhow!("Producer already consumed"))?;
        
        let host = cpal::default_host();
        // WASAPI Loopback: Use default output device as input source
        let device = host.default_output_device()
            .ok_or_else(|| anyhow!("No default output device found for loopback capture"))?;
            
        info!("Audio Device: {}", device.name().unwrap_or_default());

        let config = device.default_output_config()
            .context("Failed to get default output config")?;
            
        let stream_config: StreamConfig = config.clone().into();
        let sample_rate = stream_config.sample_rate.0;
        let channels = stream_config.channels;
        
        info!("Stream Config: {:?}Hz, {} channels", sample_rate, channels);

        if config.sample_format() != SampleFormat::F32 {
            return Err(anyhow!("Unsupported sample format (expected F32)"));
        }

        let mut producer = producer;

        let stream = device.build_input_stream(
            &stream_config,
            move |data: &[f32], _: &_| {
                // Non-blocking push. If full, we drop samples (overrun).
                // In production, we should log overruns or use a larger buffer.
                let _ = producer.push_slice(data);
            },
            |err| error!("Stream error: {}", err),
            None
        )?;
        
        stream.play()?;
        
        Ok((stream, sample_rate, channels))
    }
}

