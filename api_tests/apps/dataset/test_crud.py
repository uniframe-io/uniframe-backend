from typing import List

import pytest

from server.apps.dataset import schemas
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.group import schemas as group_schemas
from server.apps.media import schemas as media_schemas
from server.apps.user import schemas as user_schemas


def test_get_dataset(
    do_dummy_user: user_schemas.UserDO, do_dummy_dataset: schemas.DatasetDO
) -> None:

    do_dataset = DATASET_CRUD.get_dataset(do_dummy_dataset.id)
    assert do_dataset == do_dummy_dataset

    return


def test_get_dataset_not_exist(
    do_dummy_user: user_schemas.UserDO, do_dummy_dataset: schemas.DatasetDO
) -> None:
    do_dataset = DATASET_CRUD.get_dataset(do_dummy_dataset.id + 1)
    assert do_dataset is None

    return


def test_create_dataset(
    do_dummy_user: user_schemas.UserDO, do_dummy_media: media_schemas.MediaDO
) -> None:
    dataset_create = schemas.DatasetCreateDO(
        name="Dummy Dataset",
        description="This is a dummy dataset for unit test by test_crud",
        media_id=do_dummy_media.id,
        owner_id=do_dummy_user.id,
    )

    do_dataset = DATASET_CRUD.create_dataset(dataset_create)
    assert do_dataset.name == dataset_create.name
    assert do_dataset.description == dataset_create.description
    assert do_dataset.owner_id == dataset_create.owner_id
    assert do_dataset.media_id == dataset_create.media_id

    DATASET_CRUD.delete_dataset(do_dataset.id)
    return


def test_update_dataset(
    do_dummy_user: user_schemas.UserDO, do_dummy_dataset: schemas.DatasetDO
) -> None:

    dataset_update = schemas.DatasetUpdateDO(
        name="Dummy Dataset Update",
        description="This is a dummy dataset for update unit test",
    )
    do_dataset = DATASET_CRUD.update_dataset(
        do_dummy_dataset.id, dataset_update
    )
    assert do_dataset.name == dataset_update.name
    assert do_dataset.description == dataset_update.description

    return


def test_delete_dataset(
    do_dummy_user: user_schemas.UserDO, do_dummy_media: media_schemas.MediaDO
) -> None:
    dataset_create = schemas.DatasetCreateDO(
        name="Dummy Dataset",
        description="This is a dummy dataset for unit test by test_crud",
        media_id=do_dummy_media.id,
        owner_id=do_dummy_user.id,
    )

    do_dataset = DATASET_CRUD.create_dataset(dataset_create)
    assert do_dataset.name == dataset_create.name
    assert do_dataset.description == dataset_create.description

    DATASET_CRUD.delete_dataset(do_dataset.id)
    return


def test_get_datasets_by_owner(
    do_dummy_user: user_schemas.UserDO, do_dummy_dataset: schemas.DatasetDO
) -> None:

    do_datasets = DATASET_CRUD.get_datasets_by_owner(do_dummy_user.id)
    assert len(do_datasets) == 1

    return


@pytest.mark.parametrize(
    "do_dummy_group_list",
    [2],
    indirect=["do_dummy_group_list"],
)
def test_share_dataset_with_groups(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_group_list: List[group_schemas.GroupDO],
) -> None:
    group_ids = [g.id for g in do_dummy_group_list]
    DATASET_CRUD.share_dataset_with_groups(do_dummy_dataset.id, group_ids)

    DATASET_CRUD.remove_shared_groups(do_dummy_dataset.id, group_ids)
    return


@pytest.mark.parametrize(
    "do_dummy_user_list",
    [2],
    indirect=["do_dummy_user_list"],
)
def test_share_dataset_with_users(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    user_ids = [u.id for u in do_dummy_user_list]
    DATASET_CRUD.share_dataset_with_users(do_dummy_dataset.id, user_ids)

    DATASET_CRUD.remove_shared_users(do_dummy_dataset.id, user_ids)
    return


@pytest.mark.parametrize(
    "do_dummy_group_list",
    [2],
    indirect=["do_dummy_group_list"],
)
def test_get_shared_groups(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_group_list: List[group_schemas.GroupDO],
) -> None:
    group_ids = [g.id for g in do_dummy_group_list]
    DATASET_CRUD.share_dataset_with_groups(do_dummy_dataset.id, group_ids)

    do_group_ids = DATASET_CRUD.get_shared_groups(do_dummy_dataset.id)

    assert group_ids == do_group_ids

    DATASET_CRUD.remove_shared_groups(do_dummy_dataset.id, group_ids)
    return


@pytest.mark.parametrize(
    "do_dummy_user_list",
    [2],
    indirect=["do_dummy_user_list"],
)
def test_get_shared_users(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    user_ids = [u.id for u in do_dummy_user_list]
    DATASET_CRUD.share_dataset_with_users(do_dummy_dataset.id, user_ids)

    do_user_ids = DATASET_CRUD.get_shared_users(do_dummy_dataset.id)

    assert user_ids == do_user_ids

    DATASET_CRUD.remove_shared_users(do_dummy_dataset.id, user_ids)
    return


@pytest.mark.parametrize(
    "do_dummy_group_list",
    [2],
    indirect=["do_dummy_group_list"],
)
def test_remove_shared_groups(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_group_list: List[group_schemas.GroupDO],
) -> None:
    group_ids = [g.id for g in do_dummy_group_list]
    DATASET_CRUD.share_dataset_with_groups(do_dummy_dataset.id, group_ids)

    DATASET_CRUD.remove_shared_groups(do_dummy_dataset.id, group_ids)
    return


@pytest.mark.parametrize(
    "do_dummy_user_list",
    [2],
    indirect=["do_dummy_user_list"],
)
def test_remove_shared_users(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    user_ids = [u.id for u in do_dummy_user_list]
    DATASET_CRUD.share_dataset_with_users(do_dummy_dataset.id, user_ids)

    DATASET_CRUD.remove_shared_users(do_dummy_dataset.id, user_ids)

    do_user_ids = DATASET_CRUD.get_shared_users(do_dummy_dataset.id)
    assert len(do_user_ids) == 0

    return


@pytest.mark.parametrize(
    "do_dummy_group_list",
    [2],
    indirect=["do_dummy_group_list"],
)
def test_get_dataset_shared_with_groups(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_group_list: List[group_schemas.GroupDO],
) -> None:

    do_dataset_ids = DATASET_CRUD.get_dataset_shared_with_groups(
        [do_dummy_group_list[0].id]
    )

    assert len(do_dataset_ids) == 0

    DATASET_CRUD.share_dataset_with_groups(
        do_dummy_dataset.id, [do_dummy_group_list[0].id]
    )

    do_dataset_ids = DATASET_CRUD.get_dataset_shared_with_groups(
        [do_dummy_group_list[0].id]
    )

    assert do_dataset_ids == [do_dummy_dataset.id]

    DATASET_CRUD.remove_shared_groups(
        do_dummy_dataset.id, [do_dummy_group_list[0].id]
    )

    do_group_ids = DATASET_CRUD.get_shared_groups(do_dummy_dataset.id)
    assert len(do_group_ids) == 0

    return


@pytest.mark.parametrize(
    "do_dummy_user_list",
    [2],
    indirect=["do_dummy_user_list"],
)
def test_get_dataset_shared_with_user(
    do_dummy_dataset: schemas.DatasetDO,
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    do_dataset_ids = DATASET_CRUD.get_dataset_shared_with_user(
        do_dummy_user_list[0].id
    )

    assert len(do_dataset_ids) == 0

    DATASET_CRUD.share_dataset_with_users(
        do_dummy_dataset.id, [do_dummy_user_list[0].id]
    )

    do_dataset_ids = DATASET_CRUD.get_dataset_shared_with_user(
        do_dummy_user_list[0].id
    )
    assert do_dataset_ids == [do_dummy_dataset.id]

    DATASET_CRUD.remove_shared_users(
        do_dummy_dataset.id, [do_dummy_user_list[0].id]
    )

    do_user_ids = DATASET_CRUD.get_shared_users(do_dummy_dataset.id)
    assert len(do_user_ids) == 0

    return


@pytest.mark.parametrize(
    "do_dummy_dataset_list",
    [2],
    indirect=["do_dummy_dataset_list"],
)
def test_get_dataset_by_ids(
    do_dummy_dataset_list: List[schemas.DatasetDO],
) -> None:
    datasets = DATASET_CRUD.get_dataset_by_ids(
        [d.id for d in do_dummy_dataset_list]
    )

    dataset_ids = [d.id for d in datasets]

    for did in dataset_ids:
        assert did in [d.id for d in do_dummy_dataset_list]

    return


@pytest.mark.parametrize(
    "do_dummy_dataset_list",
    [2],
    indirect=["do_dummy_dataset_list"],
)
def test_delete_dataset_by_owner(
    do_dummy_user: user_schemas.UserDO,
    do_dummy_dataset_list: List[schemas.DatasetDO],
) -> None:

    DATASET_CRUD.delete_dataset_by_owner(do_dummy_user.id)

    datasets = DATASET_CRUD.get_dataset_by_ids(
        [d.id for d in do_dummy_dataset_list]
    )
    for d in datasets:
        assert d.is_active is False

    return


def test_create_public_dataset(
    do_dummy_dataset: schemas.DatasetDO,
) -> None:
    DATASET_CRUD.create_public_dataset(
        schemas.PublicDatasetCreateDO(dataset_id=do_dummy_dataset.id)
    )

    do_public_datasets = DATASET_CRUD.get_public_datasets()
    assert len(do_public_datasets) == 1

    DATASET_CRUD.delete_public_dataset(do_dummy_dataset.id)


def test_delete_public_dataset(
    do_dummy_dataset: schemas.DatasetDO,
) -> None:
    DATASET_CRUD.create_public_dataset(
        schemas.PublicDatasetCreateDO(dataset_id=do_dummy_dataset.id)
    )

    do_public_datasets = DATASET_CRUD.get_public_datasets()
    assert len(do_public_datasets) == 1

    DATASET_CRUD.delete_public_dataset(do_dummy_dataset.id)

    do_public_datasets = DATASET_CRUD.get_public_datasets()
    assert len(do_public_datasets) == 0


@pytest.mark.parametrize(
    "do_dummy_dataset_list",
    [2],
    indirect=["do_dummy_dataset_list"],
)
def test_get_public_datasets(
    do_dummy_dataset_list: List[schemas.DatasetDO],
) -> None:
    for d in do_dummy_dataset_list:
        DATASET_CRUD.create_public_dataset(
            schemas.PublicDatasetCreateDO(dataset_id=d.id)
        )

    do_public_datasets = DATASET_CRUD.get_public_datasets()
    assert len(do_public_datasets) == 2

    DATASET_CRUD.delete_public_dataset_by_ids(do_public_datasets)


@pytest.mark.parametrize(
    "do_dummy_dataset_list",
    [2],
    indirect=["do_dummy_dataset_list"],
)
def test_delete_public_dataset_by_ids(
    do_dummy_dataset_list: List[schemas.DatasetDO],
) -> None:
    for d in do_dummy_dataset_list:
        DATASET_CRUD.create_public_dataset(
            schemas.PublicDatasetCreateDO(dataset_id=d.id)
        )

    do_public_datasets = DATASET_CRUD.get_public_datasets()
    assert len(do_public_datasets) == 2

    DATASET_CRUD.delete_public_dataset_by_ids(do_public_datasets)

    do_public_datasets = DATASET_CRUD.get_public_datasets()
    assert len(do_public_datasets) == 0
