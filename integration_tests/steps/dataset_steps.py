import pandas as pd
from behave import given, then, when
from behave.runner import Context

from integration_tests.utils import url_gen
from server.apps.dataset.schemas import DatasetCreateDTO, DatasetDTO
from server.apps.media.schemas import MediaDTO


@given('I upload with file "{file_name}"')
@when('I upload with file "{file_name}"')
def step_impl_1(context: Context, file_name: str) -> None:
    with open(file_name, "rb") as f:
        r = context.sess.post(
            url_gen("medias/upload"), files={"file": (file_name, f, "text/csv")}
        )
        assert r.status_code == 200

        media_dto = MediaDTO(**r.json())
        context.media_dto = media_dto


@then('I should see CSV media object file "{file_name}"')
def step_impl_2(context: Context, file_name: str) -> None:
    assert file_name == context.media_dto.ext_info.file_name

    df = pd.read_csv(file_name)
    header = list(df.columns)
    assert header == context.media_dto.ext_info.header


@given(
    'I create a dataset with the file "{file_name}" and dataset name "{dataset_name}"'
)
@when(
    'I create a dataset with the file "{file_name}" and dataset name "{dataset_name}"'
)
def step_impl_3(context: Context, file_name: str, dataset_name: str) -> None:
    with open(file_name, "rb") as f:
        r = context.sess.post(
            url_gen("medias/upload"), files={"file": (file_name, f, "text/csv")}
        )
        assert r.status_code == 200

        media_dto = MediaDTO(**r.json())

    payload = DatasetCreateDTO(
        name=dataset_name,
        description="dummy description",
        media_id=media_dto.id,
    ).dict()
    r = context.sess.post(url=url_gen("datasets"), json=payload)

    assert r.status_code == 200
    context.dataset_dict[dataset_name] = DatasetDTO(**r.json())


@then("I should have a dataset created")
def step_impl_4(context: Context) -> None:
    # dataset media id should be the same as the media id
    for dataset_name, dataset_dto in context.dataset_dict.items():
        assert dataset_dto.media_id == dataset_dto.media.id
        assert dataset_dto.name == dataset_name
