class Recorder extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const samples = inputs[0]?.[0];
    if (samples) this.port.postMessage(samples);
    for (const channel of outputs[0]) channel.fill(0);
    return true;
  }
}
registerProcessor('idiomas-recorder', Recorder);
