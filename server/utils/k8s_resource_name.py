def gen_k8s_resource_prefix(task_id: int, user_id: int) -> str:
    return f"nm-{user_id}-{task_id}"
