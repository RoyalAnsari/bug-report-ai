from pydantic import BaseModel


class ProjectList(BaseModel):
    projects: list[str]
