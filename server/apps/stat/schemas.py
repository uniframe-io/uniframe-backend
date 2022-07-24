from pydantic import BaseModel


class TaskStat(BaseModel):
    created_count: int
    running_count: int
    failed_count: int
    complete_count: int


class DatasetStat(BaseModel):
    uploaded_count: int


class StatDTO(BaseModel):
    batch_task: TaskStat
    realtime_task: TaskStat
    created_dataset: DatasetStat
