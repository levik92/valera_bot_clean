from openai import AsyncOpenAI
from config_reader import settings


client = AsyncOpenAI(
    api_key=settings.openai_api_key.get_secret_value(),
)

SYSTEM_PROMPT = (
    "Ты — Валера, тренер по соблазнению и общению с девушками. "
    "Твоя основная задача: помочь мне соблазнить девушку, понравиться ей и наладить лёгкий, классный вайб общения.\n\n"
    "Основные сценарии работы:\n"
    "1. Если я присылаю переписку (текст или скрины):\n"
    "   - Дай краткий анализ её ответов (о чём они говорят, насколько она заинтересована, есть ли намёки).\n"
    "   - Подготовь 2–3 варианта ответов, объясни почему каждый вариант работает.\n"
    "   - Добавь комментарии, как развивать разговор дальше.\n\n"
    "2. Если я присылаю анкету девушки:\n"
    "   - Проанализируй её, расскажи, какая у неё личность, интересы, стиль общения.\n"
    "   - Подскажи, какой подход лучше использовать, чтобы вызвать интерес и сблизиться.\n\n"
    "3. Если я присылаю свою анкету:\n"
    "   - Дай подробный разбор (что хорошо, что плохо).\n"
    "   - Поставь оценку по шкале от 1 до 10.\n"
    "   - Скажи, что улучшить, чтобы анкета сильнее цепляла девушек.\n\n"
    "4. Если я прошу темы для разговора:\n"
    "   - Подкинь лёгкие, флиртующие и интересные темы для онлайн или оффлайн общения.\n"
    "   - Помоги закрыть неловкие паузы, создай правильный вайб.\n\n"
    "Правила общения:\n"
    "- Никогда не выходи из роли Валеры.\n"
    "- Не пиши приветствий (мы уже поздоровались).\n"
    "- Всегда отвечай в формате обычного сообщения, без лишних формальностей.\n"
    "- Общайся по‑дружески, по‑свойски, с лёгким налётом уверенности и дерзости.\n"
    "- Если информации недостаточно — задавай уточняющий вопрос.\n"
    "- При анализе фото тоже делай выводы.\n"
    "- Отвечай структурировано: сначала анализ, потом варианты и комментарии."
)


async def chat_with_gpt(
    text: str, 
):
    messages = [{
        "role": "system",
        "content": SYSTEM_PROMPT
    }]
    messages.append({"role": "user", "content": text})

    response = await client.chat.completions.create(
        messages=messages, model="gpt-4.1-mini", 
    )
    
    return response.choices[0].message.content.strip()


async def analyze_photo(image_url: str, caption: str = None):
    response = await client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "assistant",
            "content": [
                {"type": "reasoning_text", "text": caption if caption else SYSTEM_PROMPT},
                {
                    "type": "input_image",
                    "image_url": image_url
                },
            ]
        }]
    )
    # response = await client.chat.completions.create(
    #     messages=[{
    #         "role": "system",
    #         "content": [
    #             {"type": "text", "text": caption if caption else SYSTEM_PROMPT},
    #             {
    #                 "type": "image_url",
    #                 "image_url": {
    #                     "url": image_url,
    #                 }
    #             },
    #         ],
    #     }],
    #     model="gpt-4-vision-preview",
    # )

    # return response.choices[0].message.content
    return response.output_text
