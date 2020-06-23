# Rhasspy Silence

[![Continous Integration](https://github.com/rhasspy/rhasspy-silence/workflows/Tests/badge.svg)](https://github.com/rhasspy/rhasspy-silence/actions)
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
