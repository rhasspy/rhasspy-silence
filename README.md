# Rhasspy Silence

[![Continuous Integration](https://github.com/rhasspy/rhasspy-silence/workflows/Tests/badge.svg)](https://github.com/rhasspy/rhasspy-silence/actions)
[![GitHub license](https://img.shields.io/github/license/rhasspy/rhasspy-silence.svg)](https://github.com/rhasspy/rhasspy-silence/blob/master/LICENSE)

Detect speech/silence in voice commands with [webrtcvad](https://github.com/wiseman/py-webrtcvad).

## Requirements

* Python 3.7
* [webrtcvad](https://github.com/wiseman/py-webrtcvad)

## Installation

```bash
$ git clone https://github.com/rhasspy/rhasspy-silence
$ cd rhasspy-silence
$ ./configure
$ make
$ make install
```

## How it Works

`rhasspy-silence` uses a state machine to decide when a voice command has started and stopped. The variables that control this machine are:

* `skip_seconds` - seconds of audio to skip before voice command detection starts
* `speech_seconds` - seconds of speech before voice command has begun
* `before_seconds` - seconds of audio to keep before voice command has begun
* `minimum_seconds` - minimum length of voice command (seconds)
* `maximum_seconds` - maximum length of voice command before timeout (seconds, None for no timeout)
* `silence_seconds` - seconds of silence before a voice command has finished

The sensitivity of `webrtcvad` is set with `vad_mode`, which is a value between 0 and 3 with 0 being the most sensitive.

[![State machine diagram for silence detection](docs/img/state_machine.png)](docs/img/state_machine.svg)

If there is no timeout, the final voice command audio will consist of:

* `before_seconds` worth of audio before the voice command had started
* At least `min_seconds` of audio during the voice command
