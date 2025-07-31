import asyncio
import json
import logging

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai

import requests

from datetime import datetime
from zoneinfo import ZoneInfo
from livekit.agents import ConversationItemAddedEvent, CloseEvent

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

class Assistant(Agent):

    @function_tool()
    async def check_availability(self, context: RunContext, start_time: str, end_time: str):
        url = "https://api.cal.com/v1/slots"
        querystring = {
            "apiKey": "cal_live_a34c0ef9eaab0746dc7bd5511f74510f",
            "eventTypeId": "2029915",
            "startTime": start_time,
            "endTime": end_time,
            "timeZone": "Europe/Rome"
        }
        try:
            response = requests.get(url, params=querystring)
            response.raise_for_status()
            print("Availability API response:", response.text)
            return response.json()
        except requests.RequestException as e:
            print("Error in check_availability:", e)
            return {"error": "Unable to check availability"}

    @function_tool()
    async def book_appointment(self, context: RunContext, name: str, email: str, start_time: str):
        url = "https://api.cal.com/v2/bookings"
        payload = {
            "start": start_time,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": "Europe/Rome",
                "language": "it"
            },
            "eventTypeId": 2029915,
            "eventTypeSlug": "my-event-type",
            "organizationSlug": "acme-corp",
        }
        headers = {
            "cal-api-version": "2024-08-13",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print("Booking API response:", response.text)
            return response.json()
        except requests.RequestException as e:
            print("Error in book_appointment:", e)
            return {"error": "Unable to book appointment"}

    def __init__(self) -> None:
        super().__init__(instructions=f"""
## Identity
You are Martina, Michele’s AI secretary. You help clients schedule appointments with Michele.
Always speak Italian.

## Role
You handle client calls and guide them naturally through the process of booking an appointment.

## Behavior
- Be warm, professional and conversational.
- Ask about their situation to understand their needs.
- Suggest a free video call with Michele to explore solutions.
- Ask for their preferred time (morning or afternoon).
- Request and confirm their email address politely.
- Call the `check_availability` tool to check Michele's availability.
- If available, call `book_appointment` to schedule.
- End the call thanking the client and offering further assistance.

SYSTEM: Current date and time is {datetime.now(ZoneInfo("Europe/Rome"))}.
""")
        self.chat_history = []
        self.caller_phone_number = None


async def entrypoint(ctx: agents.JobContext):
    global session
    print("👋 Agent avviato su stanza:", ctx.room)
    assistant = Assistant()
    start_time = datetime.now()

    async def on_session_close():
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print("------- Session has ended. Performing cleanup. --------")

        data = {
            "called_number": getattr(assistant, "caller_phone_number", "unknown"),
            "chat_transcript": getattr(assistant, "chat_history", []),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration
        }
        try:
            print("Webhook data payload:", json.dumps(data, indent=2))
            response = requests.post(
                "https://webhook.latenode.com/1415/dev/2dbfb0bb-7b12-4f2e-9c66-6a8750532001", 
                json=data
            )
            print("Webhook status:", response.status_code, "Response:", response.text)
        except requests.RequestException as e:
            print("Error sending webhook:", e)

        assistant.chat_history.clear()

    ctx.add_shutdown_callback(on_session_close)
    await ctx.connect()

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="shimmer"),
        tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
    )

    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(),
    )
    asyncio.create_task(auto_hangup_after_duration())
    participant = await ctx.wait_for_participant()
    attributes = getattr(participant, "attributes", {})
    assistant.recording_url = attributes.get("sip.X-RecordingUrl")
    assistant.caller_phone_number = attributes.get("sip.phoneNumber")

    print("Incoming call from:", assistant.caller_phone_number or "unknown")

    
    await session.say("Ciao, sono Martina, l’assistente di Michele. Come posso aiutarti?")

    @session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        asyncio.create_task(handle_conversation_item(event))

    reply_lock = asyncio.Lock()

    async def handle_conversation_item(event: ConversationItemAddedEvent):
        async with reply_lock:
            await reset_silence_timer()
            assistant.chat_history.append(f"{event.item.role}: {event.item.text_content}")

            try:
                reply = await session.generate_reply(
                    user_input=event.item.text_content,
                    allow_interruptions=True,
                )
                await session.say(reply)
            except Exception as e:
                print("Errore nel generare o pronunciare la risposta:", e)


    @session.on("close")
    def on_close(event: CloseEvent):
        print("Session closed:", event)

async def auto_hangup_after_duration():
    await asyncio.sleep(300)  # 5 minuti
    print("🕐 Durata massima raggiunta: chiudo la chiamata.")
    await session.say("La chiamata ha raggiunto il tempo massimo. Ti auguro una buona giornata!")
    await session.close()

   
silence_timer = None    
async def reset_silence_timer():
    global silence_timer

    # Cancella il timer esistente, se presente
    if silence_timer:
        silence_timer.cancel()

    # Avvia un nuovo timer
    silence_timer = asyncio.create_task(silence_timeout())

async def silence_timeout():
    try:
        await asyncio.sleep(30)  # 30 secondi di inattività
        print("🔇 Nessuna attività rilevata per 30 secondi. Chiudo la chiamata.")
        await session.say("Sembra che la linea sia silenziosa da un po'. Chiudo la chiamata, ma puoi richiamare quando vuoi.")
        await session.close()
    except asyncio.CancelledError:
        pass  # Timer cancellato (perché c'è attività)

if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="inbound-agent",
        )
    )
