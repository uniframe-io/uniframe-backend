import json
import time

from behave import given, then, when
from behave.runner import Context

from integration_tests.utils import url_gen
from server.apps.nm_task.schemas import (
    NM_STATUS,
    AbcXyz_TYPE,
    NmTaskCreateDTO,
    NmTaskDTO,
)


@given(
    'I create a nm batch task "{task_name}" with gt dataset "{gt_dataset_name}" and nm dataset "{nm_dataset_name}" and config file "{config_file}"'
)
@when(
    'I create a nm batch task "{task_name}" with gt dataset "{gt_dataset_name}" and nm dataset "{nm_dataset_name}" and config file "{config_file}"'
)
def setp_impl_1(
    context: Context,
    task_name: str,
    gt_dataset_name: str,
    nm_dataset_name: str,
    config_file: str,
) -> None:
    assert gt_dataset_name in context.dataset_dict
    assert nm_dataset_name in context.dataset_dict

    with open(config_file, "r") as f:
        task_config_dict = json.load(f)
        nm_task_dto = NmTaskCreateDTO(**task_config_dict)

        # assign the dataset
        nm_task_dto.name = task_name
        nm_task_dto.ext_info.gt_dataset_config.dataset_id = (
            context.dataset_dict[gt_dataset_name].id
        )
        nm_task_dto.ext_info.nm_dataset_config.dataset_id = (  # type: ignore
            context.dataset_dict[nm_dataset_name].id
        )

        r = context.sess.post(url_gen("tasks/nm"), json=nm_task_dto.dict())
        assert r.status_code == 200

        context.nm_task_dict[task_name] = NmTaskDTO(**r.json())
        print("after create batch", context.nm_task_dict)


@given(
    'I create a nm realtime task "{task_name}" with gt dataset "{gt_dataset_name}" and config file "{config_file}"'
)
@when(
    'I create a nm realtime task "{task_name}" with gt dataset "{gt_dataset_name}" and config file "{config_file}"'
)
def setp_impl_2(
    context: Context,
    task_name: str,
    gt_dataset_name: str,
    config_file: str,
) -> None:
    assert gt_dataset_name in context.dataset_dict

    with open(config_file, "r") as f:
        task_config_dict = json.load(f)
        nm_task_dto = NmTaskCreateDTO(**task_config_dict)

        # assign the dataset
        nm_task_dto.name = task_name
        nm_task_dto.ext_info.gt_dataset_config.dataset_id = (
            context.dataset_dict[gt_dataset_name].id
        )

        r = context.sess.post(url_gen("tasks/nm"), json=nm_task_dto.dict())
        assert r.status_code == 200

        context.nm_task_dict[task_name] = NmTaskDTO(**r.json())


@then("I should have a nm task")
def setp_impl_3(context: Context) -> None:
    pass


@given('I run the nm task "{task_name}" and wait "{wait_time}" second')
@when('I run the nm task "{task_name}" and wait "{wait_time}" second')
def setp_impl_4(context: Context, task_name: str, wait_time: str) -> None:
    assert task_name in context.nm_task_dict

    task_id = context.nm_task_dict[task_name].id

    r = context.sess.post(url_gen(f"tasks/nm/{task_id}/start"))
    assert r.status_code == 200
    assert r.json() == f"start task {task_id} successfully"

    time.sleep(int(wait_time))


@then('I should have a realtime task "{task_name}" which is ready for matching')
def step_impl_5(context: Context, task_name: str) -> None:
    assert task_name in context.nm_task_dict
    assert (
        context.nm_task_dict[task_name].type
        == AbcXyz_TYPE.NAME_MATCHING_REALTIME
    )

    task_id = context.nm_task_dict[task_name].id
    r = context.sess.get(url_gen(f"tasks/nm/{task_id}"))
    assert r.status_code == 200
    nm_task_dto = NmTaskDTO(**r.json())

    print(nm_task_dto)
    assert nm_task_dto.ext_info.nm_status == NM_STATUS.READY


@then(
    'I should be able to stop the task "{task_name}" and wait "{wait_time}" second'
)
def step_impl_6(context: Context, task_name: str, wait_time: str) -> None:
    assert task_name in context.nm_task_dict

    task_id = context.nm_task_dict[task_name].id

    r = context.sess.post(url_gen(f"tasks/nm/{task_id}/stop"))
    assert r.status_code == 200
    assert r.json() == f"Stop task {task_id} successfully"

    time.sleep(int(wait_time))


@then(
    'I should have a realtime task "{task_name}" which is successfully terminated'
)
def step_impl_7(context: Context, task_name: str) -> None:
    assert task_name in context.nm_task_dict
    assert (
        context.nm_task_dict[task_name].type
        == AbcXyz_TYPE.NAME_MATCHING_REALTIME
    )

    task_id = context.nm_task_dict[task_name].id
    r = context.sess.get(url_gen(f"tasks/nm/{task_id}"))
    assert r.status_code == 200
    nm_task_dto = NmTaskDTO(**r.json())

    print(nm_task_dto)
    assert nm_task_dto.ext_info.nm_status == NM_STATUS.STOPPED


@then('I should have a batch task "{task_name}" complete')
def setp_impl_8(context: Context, task_name: str) -> None:
    print(context.nm_task_dict)
    print(task_name)
    assert task_name in context.nm_task_dict
    assert (
        context.nm_task_dict[task_name].type == AbcXyz_TYPE.NAME_MATCHING_BATCH
    )

    task_id = context.nm_task_dict[task_name].id
    r = context.sess.get(url_gen(f"tasks/nm/{task_id}"))
    assert r.status_code == 200
    nm_task_dto = NmTaskDTO(**r.json())

    print(nm_task_dto)
    assert nm_task_dto.ext_info.nm_status == NM_STATUS.COMPLETE


@then(
    'I can download the batch matching result of the batch task "{task_name}"'
)
def setp_impl_9(context: Context, task_name: str) -> None:
    assert task_name in context.nm_task_dict
    assert (
        context.nm_task_dict[task_name].type == AbcXyz_TYPE.NAME_MATCHING_BATCH
    )

    # N.B. This download testing is dummy since we use localfs

    # task_id = context.nm_task_dict[task_name].id
    # r = context.sess.get(url_gen(f"tasks/nm/{task_id}/download-batch-result"))
    # assert r.status_code == 200

    # presigned_url = r.json()
    # print(presigned_url)

    # r = requests.get(presigned_url)
    # assert r.status_code == 200


@then(
    'I do realtime match on task "{task_name}" with search key and expect value in file "{rt_name_test_file}"'
)
def step_impl_10(
    context: Context, task_name: str, rt_name_test_file: str
) -> None:
    assert task_name in context.nm_task_dict
    assert (
        context.nm_task_dict[task_name].type
        == AbcXyz_TYPE.NAME_MATCHING_REALTIME
    )

    task_id = context.nm_task_dict[task_name].id

    with open(rt_name_test_file, "r") as f:
        rt_name_test_cases = json.load(f)

        for test_case in rt_name_test_cases:
            r = context.sess.post(
                url_gen(f"tasks/nm/{task_id}/match"),
                json=test_case["query_request"],
            )
            assert r.status_code == 200
            print(r.json())
            match_result = r.json()
            assert match_result == test_case["expected_value"]
