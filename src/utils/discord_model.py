import discord
from discord import Interaction as I

class ReasoningButton(discord.ui.Button):
    def __init__(self, reasoning: str, user_id: int):
        super().__init__(style=discord.ButtonStyle.primary, label='💭')
        self.reasoning = reasoning
        self.user_id = user_id
        
    async def callback(self, i: I):
        if i.user.id == self.user_id:
            await i.response.send_message(content="You are not a developer.")
            return
        await i.response.send_message(content=self.reasoning)
        
class ButtonView(discord.ui.View):
    def __init__(self, reasoning: str, user_id: int):
        super().__init__()
        self.add_item(ReasoningButton(reasoning, user_id))