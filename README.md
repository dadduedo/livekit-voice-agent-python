# Python Voice Agent + Optional Inbound Calls with Twilio

A basic example of a voice agent using LiveKit and Python. Has a few extras to get started:
- Turn detection
- Function calling
  - Get weather
  - Get current time
- Summary usage logging
- Optional inbound calls with Twilio
- Krisp noise cancellation
- Inbound calls switch to a model optimized for telephony

## Dev Setup

Clone the repository then run the following commands to:
- change directory to `livekit-voice-agent-python`
- create a virtual environment and activate it
- install dependencies
- download files

### Linux/macOS
```console
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


## Optional: Enable inbound calls with Twilio

The following steps expect you have LiveKit CLI installed. To install on macOS:
```console
brew update && brew install livekit-cli
```
Then authenticate with LiveKit Cloud:
```console
lk cloud auth
```
Then, follow instructions and log in from a browser.

1. Create a Twilio account
2. Get a Twilio phone number
3. Create a SIP trunk
- In Twilio console go to Explore products > Elastic SIP Trunking > SIP Trunks > Get started > Create a SIP Trunk, name it, then Save.
4. Associate your LiveKit SIP URI with your SIP trunk
- Go to Origination, select Add new Origination URI, go to your LiveKit Cloud project settings, copy your SIP URI, go back to Twilio console, paste the SIP URI, and add the `;transport=tcp`. So it looks like this: `<YOUR_SIP_URI>;transport=tcp`, then save.
5. Associate your phone number with your SIP trunk
- Finally, go to Number, select Add a number, select Add an Existing Number, select the phone number you got earlier, make Priority 1, Weight 1, and Add Selected. 
6. Create LiveKit Cloud inbound trunk
- View the file called `inbound-trunk.json` and notice the IP addresses in the allowed_addresses list are Twilio's US SIP signaling IP addresses. Update the list to include the regional IP addresses that are needed for your application.
- Krisp noise cancellation is enabled in the file.
- Create the inbound trunk using lk CLI:
```console
lk sip inbound create inbound-trunk.json
```
7. Create LiveKit Cloud dispatch rule
- Create the dispatch rule using lk CLI:
```console
lk sip dispatch create dispatch-rule.json
```
Now, you should be able to make inbound calls to your phone number.





