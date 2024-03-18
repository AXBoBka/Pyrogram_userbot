import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Interval
from sqlalchemy.orm.exc import NoResultFound


engine = create_engine('sqlite:///userbot.db')
Base = declarative_base()

messages = [
    {"time": timedelta(seconds=5), "text": "Текст1", "trigger": "msg_1"},
    {"time": timedelta(seconds=15), "text": "Текст2", "trigger": "msg_2"},
    {"time": timedelta(seconds=30), "text": "Текст3", "trigger": "msg_3"}
]

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='alive')
    status_updated_at = Column(DateTime, default=datetime.utcnow)
    last_message_sent_at = Column(DateTime, default=None)
    message_num = Column(Integer, default=0)

    def trigger_condition_met(self):
        if 'прекрасно' in messages[self.message_num]['text'].lower() or 'ожидать' in messages[self.message_num]['text'].lower():
            return True
        return False


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def add_user(user_id):
    user = User(id=user_id)
    session.add(user)
    session.commit()


def update_user_status(user_id, new_status):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.status = new_status
        user.status_updated_at = datetime.utcnow()
        user.last_message_sent_at = datetime.utcnow()
        session.commit()


def is_user_registered(user_id):
    try:
        session.query(User).filter_by(id=user_id).one()
        return True
    except NoResultFound:
        return False


API_ID="<your_api_id>"
API_HASH="<your_api_hash>"
BOT_TOKEN="<your_bot_token>"
app = Client('FirstBot', api_id=21852550, api_hash='2f16a0c76f44e6abd7118a067443dcb5', bot_token='6532776030:AAEuwut9kX2jeSSh9ex-IMgk0stQ3XJ7htw')


@app.on_message()
async def handle_message(client, message):
    try:
        if message.text == '/start':
            if is_user_registered(message.from_user.id) is False:
                user_id = message.from_user.id
                add_user(user_id)
                await message.reply('Привет! Вы успешно зарегистрированы в нашем боте.')
            update_user_status(message.from_user.id, 'alive')
    except Exception as e:
        update_user_status(message.from_user.id, 'dead')


async def check_and_send_messages(client, users):
    for user in users:
        if user.message_num >= len(messages):
            user.message_num = 0
            update_user_status(user.id, 'finished')
            continue
        current_time = datetime.utcnow()
        if user.last_message_sent_at is None or \
                (current_time - user.last_message_sent_at) >= messages[user.message_num]['time']:
            if user.trigger_condition_met():
                update_user_status(user.id, 'finished')
            else:
                await app.send_message(user.id, messages[user.message_num]['text'])
                user.last_message_sent_at = current_time
                user.message_num += 1



async def main():
    while True:
        users = session.query(User).filter_by(status='alive').all()

        for user in users:
            try:
                await check_and_send_messages(app, users)
            except Exception as e:
                print(f'Ошибка при отправке сообщения пользователю {user.id}: {e}')
                update_user_status(user.id, 'dead')

        await asyncio.sleep(10)


if __name__ == '__main__':
    app.start()
    app.run(main())
