from pydantic import BaseModel


class UpscaleResponse(BaseModel):
    task_id: str
    status: str
