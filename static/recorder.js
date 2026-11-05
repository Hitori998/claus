class VoiceCapture extends AudioWorkletProcessor {
  constructor() {
    super(); this.parts = []; this.length = 0; this.position = 0; this.newLength = 0;
    this.hasVoice = false; this.lastVoice = 0; this.meterFrames = 0;
    this.port.onmessage = event => { if (event.data === 'flush') { this.flush(); this.port.postMessage({flushed:true}); } };
  }
  flush(keepTail = false) {
    let samples = null;
    if (this.hasVoice && this.length >= sampleRate * 0.25 && this.newLength > 0) {
      samples = new Float32Array(this.length); let offset = 0;
      for (const part of this.parts) { samples.set(part, offset); offset += part.length; }
      const tail = keepTail ? samples.slice(-Math.round(sampleRate * 12)) : null;
      this.port.postMessage({samples, start: (this.position - this.length) / sampleRate, rate: sampleRate, continuation:keepTail}, [samples.buffer]);
      if (tail) { this.parts = [tail]; this.length = tail.length; this.newLength = 0; this.hasVoice = false; return; }
    }
    this.parts = []; this.length = 0; this.newLength = 0; this.hasVoice = false;
  }
  process(inputs) {
    const input = inputs[0]?.[0]; if (!input) return true;
    const copy = new Float32Array(input); this.parts.push(copy);
    this.length += copy.length; this.position += copy.length; this.newLength += copy.length;
    let energy = 0; for (const sample of copy) energy += sample * sample;
    const level = Math.sqrt(energy / copy.length);
    if (level > 0.008) { this.hasVoice = true; this.lastVoice = this.position; }
    this.meterFrames += copy.length;
    if (this.meterFrames > sampleRate / 8) { this.port.postMessage({level:Math.min(1, level * 8)}); this.meterFrames = 0; }
    if (this.hasVoice && this.length >= sampleRate * 2 && this.position - this.lastVoice > sampleRate * 0.6) this.flush();
    else if (this.newLength >= sampleRate * 6) this.flush(this.hasVoice);
    return true;
  }
}
registerProcessor('voice-capture', VoiceCapture);
