"""Core logic helpers and system prompt for the Valera bot."""

from __future__ import annotations

from typing import List, Dict, Union


# Define the system prompt that sets the behaviour of the assistant.
# You can adjust this to tweak Valera's personality and style.
SYSTEM_PROMPT = (
    "You are Valera, a friendly and witty virtual assistant. "
    "Answer user queries concisely, in a casual tone, and always be helpful. "
    "When a user sends an image or a link to an image, describe what you see "
    "and incorporate it into your answer."
)


def build_messages(prompt: str, image_links: List[str] | None = None) -> List[Dict[str, Union[str, List]]]:
    """Construct a message payload for the OpenAI Chat API.

    Parameters
    ----------
    prompt: str
        The user's textual prompt.
    image_links: list[str] | None
        Optional list of image URLs that should be included in the conversation.

    Returns
    -------
    list[dict]
        A list of message dicts ready to be passed to openai.ChatCompletion.create.
    """
    messages: List[Dict[str, Union[str, List]]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if image_links:
        # OpenAI API expects a single message with a list of content parts when including images
        parts: List[Dict[str, Union[str, Dict[str, str]]]] = []
        if prompt:
            parts.append({"type": "text", "text": prompt})
        for url in image_links:
            parts.append({"type": "image_url", "image_url": {"url": url}})
        messages.append({"role": "user", "content": parts})
    else:
        messages.append({"role": "user", "content": prompt})

    return messages
