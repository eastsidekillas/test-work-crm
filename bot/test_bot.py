import unittest
from datetime import datetime, timezone
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMessage
from aiogram.types import Message, Update, Chat, User
from main import build_dispatcher

class TelegramSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.messages = []
    async def close(self):
        pass
    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, SendMessage):
            self.messages.append(method.text)
            return Message(message_id=len(self.messages), date=datetime.now(timezone.utc), chat=Chat(id=int(method.chat_id), type='private'), text=method.text)
        raise AssertionError(type(method))
    async def stream_content(self, url, **kwargs):
        if False:
            yield b''

class CRMClient:
    def __init__(self):
        self.calls = []
        self.fail = False
    async def submit(self, payload):
        self.calls.append(payload.copy())
        if self.fail:
            raise ConnectionError('offline')
        return 123

class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session = TelegramSession()
        self.bot = Bot('123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi', session=self.session)
        self.client = CRMClient()
        self.dispatcher = build_dispatcher(self.client)
        self.update_id = 0
    async def asyncTearDown(self):
        await self.dispatcher.storage.close()
        await self.bot.session.close()
    async def text(self, value, chat_type='private'):
        self.update_id += 1
        message = Message(message_id=self.update_id, date=datetime.now(timezone.utc), chat=Chat(id=42, type=chat_type), from_user=User(id=42, is_bot=False, first_name='Анна'), text=value)
        await self.dispatcher.feed_update(self.bot, Update(update_id=self.update_id, message=message))
    async def fill(self, request='Нужен сайт'):
        for text in ['/start', 'Анна', '@anna', request]:
            await self.text(text)
    async def test_complete_application(self):
        await self.fill()
        await self.text('Отправить заявку')
        self.assertEqual(len(self.client.calls), 1)
        self.assertEqual(self.client.calls[0]['name'], 'Анна')
        self.assertEqual(self.client.calls[0]['contact'], '@anna')
        self.assertEqual(self.client.calls[0]['request'], 'Нужен сайт')
        self.assertEqual(self.client.calls[0]['telegram_user_id'], 42)
        self.assertIn('123', self.session.messages[-1])
    async def test_retry_preserves_submission_id(self):
        await self.fill()
        self.client.fail = True
        await self.text('Отправить заявку')
        self.assertIn('повтор', self.session.messages[-1].lower())
        self.client.fail = False
        await self.text('Отправить заявку')
        self.assertEqual(len(self.client.calls), 2)
        self.assertEqual(self.client.calls[0]['submission_id'], self.client.calls[1]['submission_id'])
    async def test_blank_name_and_long_name_do_not_advance(self):
        await self.text('/start')
        await self.text(' ')
        self.assertIn('150', self.session.messages[-1])
        await self.text('x' * 151)
        self.assertIn('150', self.session.messages[-1])
        await self.text('Анна')
        self.assertIn('контакт', self.session.messages[-1].lower())
    async def test_cancel_does_not_submit(self):
        await self.fill()
        await self.text('/cancel')
        await self.text('Отправить заявку')
        self.assertEqual(self.client.calls, [])
        self.assertIn('/start', self.session.messages[-1])
    async def test_long_request_summary_fits_telegram_limit(self):
        await self.fill('x' * 5000)
        self.assertLessEqual(len(self.session.messages[-1]), 4096)
        await self.text('Отправить заявку')
        self.assertEqual(len(self.client.calls[0]['request']), 5000)
    async def test_group_messages_not_collected(self):
        await self.text('/start', 'group')
        self.assertEqual(self.session.messages, [])


# Optional live integration: Telegram delivery is replaced with a local transport,
# but the aiogram dispatcher, HTTP client, Django and database are real.
import os
import httpx
from main import CRMClient as LiveCRMClient

@unittest.skipUnless(os.getenv('CRM_TEST_URL'), 'Set CRM_TEST_URL to run live backend integration')
class LiveIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_bot_to_database_to_tag_filter(self):
        url = os.environ['CRM_TEST_URL']
        secret = os.environ['CRM_TEST_SECRET']
        async with httpx.AsyncClient(base_url=url, timeout=15) as http:
            session = TelegramSession()
            bot = Bot('123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi', session=session)
            dispatcher = build_dispatcher(LiveCRMClient(http, url, secret))
            name = 'Telegram integration ' + datetime.now(timezone.utc).strftime('%H%M%S%f')
            try:
                for index, text in enumerate(['/start', name, '@integration', 'Проверка связки бот → CRM', 'Отправить заявку'], 1):
                    message = Message(message_id=index, date=datetime.now(timezone.utc), chat=Chat(id=42, type='private'), from_user=User(id=42, is_bot=False, first_name='Тест'), text=text)
                    await dispatcher.feed_update(bot, Update(update_id=index, message=message))
                self.assertIn('сохранена', session.messages[-1])
                csrf = await http.get('/api/auth/csrf/')
                csrf.raise_for_status()
                response = await http.post('/api/auth/login/', json={'username': os.environ['CRM_TEST_USERNAME'], 'password': os.environ['CRM_TEST_PASSWORD']}, headers={'X-CSRFToken': http.cookies['csrftoken']})
                self.assertEqual(response.status_code, 200)
                listing = await http.get('/api/leads/')
                lead = next(item for item in listing.json()['results'] if item['name'] == name)
                self.assertEqual(lead['source'], 'telegram_bot')
                headers = {'X-CSRFToken': http.cookies['csrftoken']}
                response = await http.post('/api/tags/', json={'name': 'Интеграция ' + name[-12:]}, headers=headers)
                self.assertEqual(response.status_code, 201)
                tag = response.json()
                response = await http.patch(f"/api/leads/{lead['id']}/", json={'tag_ids': [tag['id']]}, headers=headers)
                self.assertEqual(response.status_code, 200)
                filtered = await http.get('/api/leads/', params={'tag_id': tag['id']})
                self.assertEqual(filtered.json()['count'], 1)
                self.assertEqual(filtered.json()['results'][0]['id'], lead['id'])
            finally:
                await dispatcher.storage.close()
                await bot.session.close()

if __name__ == '__main__':
    unittest.main()
