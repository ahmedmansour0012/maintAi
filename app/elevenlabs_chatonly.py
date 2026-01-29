from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import (
    Conversation,
    ConversationInitiationData,
    AgentChatResponsePartType,
)
import time
import re


def wait_for_ws(conversation, timeout=10):
    start = time.time()
    while conversation._ws is None:
        if time.time() - start > timeout:
            raise RuntimeError("WebSocket never connected")
        time.sleep(0.05)


# from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

class NoOpAudioInterface(DefaultAudioInterface):
    def start(self, input_callback):
        # Intentionally do nothing
        pass

    def stop(self):
        pass

    def output(self, audio: bytes):
        pass

    def interrupt(self):
        pass


def anonymize_multiple_docs(text, client):
    # Find all unique Document IDs to avoid redundant API calls
    doc_ids = list(set(re.findall(r'Document:\s*(\S+)', text)))
    
    for doc_id in doc_ids:
        try:
            # Fetch document metadata
            doc = client.conversational_ai.knowledge_base.documents.get(documentation_id=doc_id)
            folder_name = doc.folder_path[0].name if doc.folder_path else "Root"
            doc_name = doc.name
            replacement = f"{folder_name}/{doc_name}"
        except Exception:
            # Fallback if the document isn't found or API fails
            replacement = "Unknown/PrivateDoc"

        # Use re.escape on doc_id to ensure special characters don't break the regex
        # We target ONLY the specific doc_id currently in the loop
        pattern = r'Document:\s*' + re.escape(doc_id)
        text = re.sub(pattern, f"Document: {replacement}", text)
    
    return text, doc_ids

from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import (
    Conversation,
    ConversationInitiationData,
    AgentChatResponsePartType,
)
import time

def start_text_only_conversation(api_key: str, agent_id: str, initial_message: str):
    transcr = []


    elevenlabs = ElevenLabs(api_key=api_key)
    agent_done = False
    agent_parts = []

    # Streaming callback
    def handle_agent_chat_response_part(text, part_type):
        nonlocal agent_done
        if part_type == AgentChatResponsePartType.START:
            agent_done = False
            print("Agent: ", end="", flush=True)

        elif part_type == AgentChatResponsePartType.DELTA:
            print(text, end="", flush=True)
            agent_parts.append(text)

        elif part_type == AgentChatResponsePartType.STOP:
            agent_done = True
            print()


    config = ConversationInitiationData(
        conversation_config_override={
            "conversation": {"text_only": True}
        }
    )

    conversation = Conversation(
        elevenlabs,
        agent_id,
        requires_auth=True,
        config=config,
        audio_interface=NoOpAudioInterface(),
        callback_agent_chat_response_part=handle_agent_chat_response_part,
    )

    conversation.start_session()
    # time.sleep(1)
    wait_for_ws(conversation)
    conversation.send_user_message(initial_message)

    # ⏳ KEEP SESSION ALIVE
# conversation.send_user_message(initial_message)

    while not agent_done:
        time.sleep(0.05)

    print("✅ Agent finished responding")

    conversation.end_session()

    return agent_parts
