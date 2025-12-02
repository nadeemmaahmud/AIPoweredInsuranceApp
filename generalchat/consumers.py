import os
from asgiref.sync import sync_to_async
from django.conf import settings
from groq import Groq
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from . models import ChatRoom, Message

def _get_groq_client():
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)

ALLOWED_KEYWORDS = [

    "hello", "hi", "greetings", "hey", "good morning", "good afternoon", "good evening",
    
    "thank you", "thanks", "appreciate", "grateful", "much obliged", "thankful", "cheers",
    
    "how", "what", "when", "where", "why", "who", "which", "can", "could", "would", "should",

    "exit", "quit", "bye", "goodbye", "see you", "later",

    "sell", "sale", "selling", "buyer", "purchase", "buy", "buying",
    "payment", "transaction", "deal", "sold", "revenue", "profit",
    
    "account", "profile", "register", "login", "logout", "password", "email",
    "verify", "verification", "otp", "reset", "forgot", "user", "authentication",
    
    "chat", "message", "talk", "speak", "communicate", "support", "help",
    "admin", "contact", "question", "ask", "answer", "reply",

    "feature", "function", "capability", "option", "setting", "configuration",
    "upload", "image", "photo", "picture", "media", "file",

    "help", "support", "guide", "tutorial", "how to", "instruction",
    "privacy", "policy", "terms", "conditions", "about",
    
    "create", "add", "new", "update", "edit", "modify", "delete", "remove",
    "view", "see", "show", "display", "list", "search", "find",
    
    "location", "address", "where", "zip", "code", "city", "state",
    
    "date", "time", "today", "tomorrow", "yesterday", "week", "month", "year",
    "appointment", "schedule", "calendar",
]

def is_on_topic(prompt):
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in ALLOWED_KEYWORDS)

async def get_ai_response(prompt, conversation_history=None):
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, test_openai_api, prompt, conversation_history or [])

def test_openai_api(promt, conversation_history=None):

    system_prompt = """You are 'Tushar', an intelligent assistant for SellnService - a comprehensive vehicle fleet management and service platform.

    Your role is to help users with:
    1. **Vehicle Management**: Adding vehicles (units) with VIN, tracking mileage, brand/model info, and managing vehicle status (active, sold, in service, inactive)
    2. **Service Scheduling**: Booking vehicle maintenance appointments, tracking service status, managing service costs and history
    3. **Sales Management**: Recording vehicle sales, managing buyer information, tracking payment methods
    4. **Account Management**: User registration, email verification, password reset, profile updates
    5. **Real-time Chat**: Communicating with admins about specific vehicles, services, or sales
    6. **Platform Features**: Explaining how to use various features like uploading images, viewing history, etc.

    Platform Key Features:
    - JWT-based authentication with email verification (OTP)
    - Vehicle tracking with VIN validation (17 characters)
    - Service workflow: Scheduled → In Progress → Completed
    - Automatic unit status updates when sold
    - WebSocket-based real-time chat system
    - Media management for vehicle and profile images

    When helping users:
    - Be concise and friendly
    - Provide step-by-step guidance when needed
    - Reference specific API endpoints when relevant (e.g., /api/users/register/, /api/main/units/)
    - Explain technical terms in simple language
    - Ask clarifying questions if the user's request is unclear
    - Guide them to the appropriate feature or admin support

    Always stay within the scope of SellnService platform. If asked about unrelated topics, politely redirect to platform-related questions."""

    try:

        messages = [{"role": "system", "content": system_prompt}]
        

        if conversation_history:
            messages.extend(conversation_history[-10:])
        

        messages.append({"role": "user", "content": promt})
        
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=0.9,
            stream=True,
            stop=None
        )
        content = ""
        for chunk in response:
            if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        
        result = content.strip()
        return result if result else "I apologize, but I couldn't generate a response. Please try again."
    except Exception as e:
        raise Exception(f"AI API Error: {str(e)}")

class ChatBotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        room = await sync_to_async(ChatRoom.objects.filter(participants=self.user).first)()

        if not room:
            room = await sync_to_async(ChatRoom.objects.create)(
                participants=self.user,
                name=None
            )

        self.room = room
        self.room_name = str(room.id)

        self.conversation_history = []
        await self.accept()

        await self.send(text_data=json.dumps({
            "message": f"👋 Welcome back! Your chat ID is Room #{self.room.id}."
        }))

    async def disconnect(self, close_code):
        self.conversation_history = []

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            prompt = data.get("message", "").strip()

            if prompt == "":
                return await self.send(json.dumps({"error": "Message cannot be empty"}))

            await sync_to_async(Message.objects.create)(
                user=self.user,
                room=self.room,
                content=prompt
            )

            if any(w in prompt.lower() for w in ["exit", "quit", "bye", "goodbye"]):
                closing_msg = "👋 Tushar: Signing off! Have a great day!"

                await sync_to_async(Message.objects.create)(
                    user=None,
                    room=self.room,
                    content=closing_msg
                )

                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": closing_msg})

                await self.send(json.dumps({"message": closing_msg}))
                return await self.close()

            if not is_on_topic(prompt):
                msg = "I'm here to help you with SellnService features.\nAsk me anything about vehicles, service, sales or account!"
                await self.send(json.dumps({"message": msg}))
                return

            answer = await get_ai_response(prompt, self.conversation_history)

            await sync_to_async(Message.objects.create)(
                user=None,
                room=self.room,
                content=answer
            )

            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": answer})

            await self.send(json.dumps({"message": answer}))

        except Exception as e:
            await self.send(json.dumps({"error": str(e)}))
