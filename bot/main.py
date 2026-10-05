import asyncio
import logging
import os
from uuid import uuid4

import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

logger = logging.getLogger(__name__)

class Application(StatesGroup):
    name = State()
    contact = State()
    request = State()
    confirm = State()

class CRMClient:
    def __init__(self, http: httpx.AsyncClient, url: str, secret: str):
        self.http, self.url, self.secret = http, url.rstrip('/'), secret
    async def submit(self, payload: dict) -> int:
        response = await self.http.post(self.url + '/api/integrations/telegram/leads/', json=payload, headers={'X-Bot-Secret': self.secret})
        response.raise_for_status()
        return int(response.json()['id'])


def build_dispatcher(client) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage(), events_isolation=SimpleEventIsolation())
    router = Router()
    router.message.filter(F.chat.type == 'private')
    confirm_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить заявку')], [KeyboardButton(text='/cancel')]], resize_keyboard=True)

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await state.clear()
        await state.set_state(Application.name)
        await message.answer('Здравствуйте! Оставим заявку агентству. Как вас зовут?\n\nДля отмены: /cancel', reply_markup=ReplyKeyboardRemove())

    @router.message(Command('cancel'))
    async def cancel(message: Message, state: FSMContext):
        await state.clear()
        await message.answer('Анкета отменена. Чтобы начать заново, отправьте /start.', reply_markup=ReplyKeyboardRemove())

    @router.message(Application.name)
    async def collect_name(message: Message, state: FSMContext):
        value = (message.text or '').strip()
        if not value or len(value) > 150:
            await message.answer('Введите имя текстом: от 1 до 150 символов.')
            return
        await state.update_data(name=value)
        await state.set_state(Application.contact)
        await message.answer('Оставьте контакт: телефон, email или Telegram @username.', reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Поделиться своим телефоном', request_contact=True)]], resize_keyboard=True, one_time_keyboard=True))

    @router.message(Application.contact)
    async def collect_contact(message: Message, state: FSMContext):
        if message.contact:
            if message.contact.user_id != message.from_user.id:
                await message.answer('Поделитесь своим телефоном или введите контакт текстом.')
                return
            value = message.contact.phone_number
        else:
            value = (message.text or '').strip()
        if not value or len(value) > 255:
            await message.answer('Введите контакт текстом: от 1 до 255 символов.')
            return
        await state.update_data(contact=value)
        await state.set_state(Application.request)
        await message.answer('Расскажите, с чем нужна помощь. До 5000 символов.', reply_markup=ReplyKeyboardRemove())

    @router.message(Application.request)
    async def collect_request(message: Message, state: FSMContext):
        value = (message.text or '').strip()
        if not value or len(value) > 5000:
            await message.answer('Опишите запрос текстом: от 1 до 5000 символов.')
            return
        await state.update_data(request=value, submission_id=str(uuid4()), telegram_user_id=message.from_user.id, telegram_chat_id=message.chat.id)
        await state.set_state(Application.confirm)
        data = await state.get_data()
        preview = value if len(value) <= 1200 else value[:1200] + '\n… (полный запрос будет сохранён)'
        await message.answer(f"Проверьте заявку:\n\nИмя: {data['name']}\nКонтакт: {data['contact']}\nЗапрос: {preview}\n\nНажмите «Отправить заявку». Для отмены: /cancel.", reply_markup=confirm_keyboard)

    @router.message(Application.confirm, F.text.in_({'Отправить заявку', '/retry'}))
    async def submit(message: Message, state: FSMContext):
        payload = await state.get_data()
        try:
            lead_id = await client.submit(payload)
        except (httpx.HTTPError, ConnectionError, ValueError, KeyError):
            # Avoid logging request bodies, secrets, or Telegram contacts.
            logger.warning('CRM submission failed; user can retry')
            await message.answer('Не удалось подтвердить сохранение. Заявка осталась в анкете. Нажмите «Отправить заявку» повторно.', reply_markup=confirm_keyboard)
            return
        await state.clear()
        await message.answer(f'Спасибо! Заявка №{lead_id} сохранена. Агентство свяжется с вами по указанному контакту.\n\nНовая заявка: /start', reply_markup=ReplyKeyboardRemove())

    @router.message(Application.confirm)
    async def waiting(message: Message):
        await message.answer('Нажмите «Отправить заявку» или отмените анкету командой /cancel.', reply_markup=confirm_keyboard)

    @router.message()
    async def fallback(message: Message):
        await message.answer('Чтобы оставить заявку агентству, отправьте /start.')

    dispatcher.include_router(router)
    return dispatcher


async def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    secret = os.getenv('TELEGRAM_API_SECRET', '')
    url = os.getenv('CRM_API_URL', 'http://backend:8000')
    if not token or not secret:
        raise SystemExit('Set TELEGRAM_BOT_TOKEN and TELEGRAM_API_SECRET')
    # httpx avoids following redirects: an unexpected host must not receive the secret.
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as http:
        client = CRMClient(http, url, secret)
        dispatcher = build_dispatcher(client)
        async with Bot(token) as bot:
            await bot.delete_webhook(drop_pending_updates=False)
            await dispatcher.start_polling(bot, allowed_updates=['message'])

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
