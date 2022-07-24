from server.apps.nm_task.schemas import RESOURCE_TSHIRT_SIZE

# base memory is 208 MiB = 208*1024*1024 Byte
# when realtime task load FastAPI, the memory usage is around 208 MB
BASE_MEM = 208


def gen_pod_mem_size(req_mem_size: int) -> str:
    """
    return the nm task pod memory size = base_mem + request_mem
    unit: MiB
    """
    return f"{req_mem_size + BASE_MEM}Mi"


def gen_pod_cpu_size(
    req_cpu_size: float, tshirt_size: RESOURCE_TSHIRT_SIZE
) -> float:
    """
    tune and return cpu size

    if Large, actual CPU size is X - 0.15. 0.15 is reserved for some system and application background pod usage
    Otherwise, it is difficult to scale up
    """

    # TODO: check if 0.15 is a good number?
    if tshirt_size == RESOURCE_TSHIRT_SIZE.LARGE:
        return req_cpu_size - 0.15

    return req_cpu_size
