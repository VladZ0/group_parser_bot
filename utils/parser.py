from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.tl.types import InputPeerChat, PeerUser, PeerChannel
from telethon.tl import types 
from telethon.tl.functions.help import GetUserInfoRequest
import pandas as pd

class GroupUserParser:

    def __init__(self, phone_number: str, api_key: str, api_hash: str, participants_limit=1000,
                    messages_limit=None, messages_per_participant_limit=10):
        self.participants_limit = participants_limit
        self.messages_limit = messages_limit
        self.messages_per_participant_limit = messages_per_participant_limit
        self.client = TelegramClient(phone_number, int(api_key), api_hash)
        self.client.start()

    async def __call__(self, url: str, keywords: list) -> pd.DataFrame:
        group = await self.client.get_entity(url)
        df = pd.DataFrame()
        participants = []

        async for participant in self.client.iter_participants(group):
            participants.append(participant)

        df['id'] = [participant.id for participant in participants]
        df['username'] = [participant.username for participant in participants]
        df['phone'] = [f"+{participant.phone}" if participant.phone != None else None for participant in participants]
        df['status'] = [self.__getStatusAsString(participant.status) for participant in participants]
        df['counter'] = [0 for participant in participants]
        df['message'] = ["" for participant in participants]

        df.set_index(df['id'], inplace=True)
        
        async for message in self.client.iter_messages(group, self.messages_limit):
            for key in keywords:
                if message.text is not None:
                    if key in message.text:
                        sender = await message.get_sender()
                        if sender is not None:               
                            if (sender.id in (df.index.values)) \
                                    and df.loc[sender.id]['counter'] < self.messages_per_participant_limit:

                                if df.loc[sender.id]['counter'] == 0:
                                    df.loc[sender.id, 'message'] = message.text
                                    df.loc[sender.id, 'counter'] = df.loc[sender.id, 'counter'] + 1

                                else:
                                    df.loc[sender.id, 'message'] = df.loc[sender.id, 'message'] \
                                        + ";\n" + message.text
                                    df.loc[sender.id, 'counter'] = df.loc[sender.id, 'counter'] + 1
                    
        df = df.sort_values('counter', ascending=False)
        df.drop(['counter', 'id'], axis="columns", inplace=True)
        df['phone'].fillna('Hidden', inplace=True)
        df = df[df['message'] != ""]

        if df.shape[0] > self.participants_limit:
            return df.head(self.participants_limit)
        
        return df

    def __getStatusAsString(self, status) -> str:
        if isinstance(status, types.UserStatusRecently):
            return "last seen recently"

        if isinstance(status, types.UserStatusLastWeek):
            return "last seen last week"     

        if isinstance(status, types.UserStatusLastMonth):
            return "last seen last month"

        if isinstance(status, types.UserStatusOnline):
            return "online"   

        if isinstance(status, types.UserStatusOffline):
            return "offline"   

        if isinstance(status, types.UserStatusEmpty):
            return "empty"   