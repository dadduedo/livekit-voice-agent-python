# Python Voice Agent

A basic example of a voice agent using LiveKit and Python. Has a few extras to get started:
- Turn detection
- Function calling
  - Get weather
  - Get current time
- Summary usage logging

## Dev Setup

Clone the repository and install dependencies to a virtual environment:

```console
# Linux/macOS
cd livekit-voice-agent-python
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
python3 agent.py download-files
```

<details>
  <summary>Windows instructions (click to expand)</summary>
  
```cmd
:: Windows (CMD/PowerShell)
cd livekit-voice-agent-python
python3 -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
```
</details>


Set up the environment by copying `.env.example` to `.env.local` and filling in the required values:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `ELEVEN_API_KEY`
- `DEEPGRAM_API_KEY`

You can also do this automatically using the LiveKit CLI:

```console
lk app env
```

Run the agent:

```console
python3 agent.py dev
```

This agent requires a frontend application to communicate with. You can use one this example frontend in [livekit-nextjs-voice-agent-interface](https://github.com/kylecampbell/livekit-nextjs-voice-agent-interface)
