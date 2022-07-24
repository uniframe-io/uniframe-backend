from pydantic import BaseModel


class HelpGuide(BaseModel):
    text: str
    link: str
