from typing import List

from intelmqtools.classes.botissue import BotIssue
from intelmqtools.classes.intelmqbot import IntelMQBot


class StrangeBot:

    def __init__(self, bot: IntelMQBot = None, issues: List[BotIssue] = None):
        self.bot: IntelMQBot = bot
        self.issues = issues
