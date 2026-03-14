# (c) @harshil8981 — Enhanced V2

import datetime
import motor.motor_asyncio
from configs import Config


class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.clone_col = self.db.clones  # Feature 11: Clone bots
        self.admin_col = self.db.admins  # Feature 9: Admin panel

    def new_user(self, id):
        return dict(
            id=id,
            join_date=datetime.date.today().isoformat(),
            language="en",  # Feature 12: Multi-language
            token_data=dict(  # Feature 7: Token system
                token="",
                token_time=0,
                is_verified=False
            ),
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.date.max.isoformat(),
                ban_reason=''
            )
        )

    async def add_user(self, id):
        user = self.new_user(id)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return True if user else False

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_duration, ban_reason):
        ban_status = dict(
            is_banned=True,
            ban_duration=ban_duration,
            banned_on=datetime.date.today().isoformat(),
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason=''
        )
        user = await self.col.find_one({'id': int(id)})
        if user:
            return user.get('ban_status', default)
        return default

    async def get_all_banned_users(self):
        banned_users = self.col.find({'ban_status.is_banned': True})
        return banned_users

    # ==================== FEATURE 7: TOKEN/VERIFY SYSTEM ====================
    async def update_token(self, user_id: int, token: str, token_time: int):
        await self.col.update_one(
            {'id': user_id},
            {'$set': {
                'token_data.token': token,
                'token_data.token_time': token_time,
                'token_data.is_verified': True
            }}
        )

    async def get_token_data(self, user_id: int) -> dict:
        default = dict(token="", token_time=0, is_verified=False)
        user = await self.col.find_one({'id': int(user_id)})
        if user:
            return user.get('token_data', default)
        return default

    async def reset_token(self, user_id: int):
        await self.col.update_one(
            {'id': user_id},
            {'$set': {
                'token_data.token': '',
                'token_data.token_time': 0,
                'token_data.is_verified': False
            }}
        )

    # ==================== FEATURE 9: ADMIN PANEL ====================
    async def add_admin(self, user_id: int, added_by: int):
        if not await self.admin_col.find_one({'id': int(user_id)}):
            await self.admin_col.insert_one({
                'id': int(user_id),
                'added_by': added_by,
                'added_on': datetime.date.today().isoformat()
            })

    async def remove_admin(self, user_id: int):
        await self.admin_col.delete_one({'id': int(user_id)})

    async def is_admin(self, user_id: int) -> bool:
        if user_id == Config.BOT_OWNER or user_id in Config.ADMINS:
            return True
        admin = await self.admin_col.find_one({'id': int(user_id)})
        return True if admin else False

    async def get_all_admins(self) -> list:
        admins = []
        async for admin in self.admin_col.find({}):
            admins.append(admin['id'])
        # Include Config.ADMINS and BOT_OWNER
        all_admins = list(set([Config.BOT_OWNER] + Config.ADMINS + admins))
        return all_admins

    # ==================== FEATURE 11: CLONE BOT ====================
    async def add_clone(self, user_id: int, bot_token: str, bot_username: str, db_channel: int):
        await self.clone_col.insert_one({
            'user_id': int(user_id),
            'bot_token': bot_token,
            'bot_username': bot_username,
            'db_channel': db_channel,
            'created_on': datetime.date.today().isoformat(),
            'is_active': True
        })

    async def get_clone(self, user_id: int):
        return await self.clone_col.find_one({'user_id': int(user_id), 'is_active': True})

    async def remove_clone(self, user_id: int):
        await self.clone_col.update_one(
            {'user_id': int(user_id)},
            {'$set': {'is_active': False}}
        )

    async def get_all_clones(self):
        return self.clone_col.find({'is_active': True})

    # ==================== FEATURE 12: MULTI-LANGUAGE ====================
    async def set_language(self, user_id: int, lang_code: str):
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {'language': lang_code}}
        )

    async def get_language(self, user_id: int) -> str:
        user = await self.col.find_one({'id': int(user_id)})
        if user:
            return user.get('language', Config.DEFAULT_LANGUAGE)
        return Config.DEFAULT_LANGUAGE


db = Database(Config.DATABASE_URL, Config.BOT_USERNAME)
