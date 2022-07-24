from server.apps.media import schemas as media_schemas
from server.apps.media.crud import MEDIA_CRUD
from server.apps.user import schemas as user_schemas


def test_get_media_not_exist(
    do_dummy_user: user_schemas.UserDO, do_dummy_media: media_schemas.MediaDO
) -> None:

    do_media = MEDIA_CRUD.get_media(do_dummy_media.id + 1)
    assert do_media is None

    return


def test_get_media(
    do_dummy_user: user_schemas.UserDO, do_dummy_media: media_schemas.MediaDO
) -> None:

    do_media = MEDIA_CRUD.get_media(do_dummy_media.id)
    assert do_media == do_dummy_media

    return


def test_create_media(do_dummy_user: user_schemas.UserDO) -> None:
    do_media_create = media_schemas.MediaCreateDO(
        owner_id=do_dummy_user.id,
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
    )
    do_dummy_media = MEDIA_CRUD.create_media(do_media_create)
    assert do_dummy_media.e_tag == do_media_create.e_tag

    MEDIA_CRUD.delete_media(do_dummy_media.id)
    return


def test_delete_media(do_dummy_user: user_schemas.UserDO) -> None:
    do_media_create = media_schemas.MediaCreateDO(
        owner_id=do_dummy_user.id,
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
    )
    do_dummy_media = MEDIA_CRUD.create_media(do_media_create)
    assert do_dummy_media.e_tag == do_media_create.e_tag

    MEDIA_CRUD.delete_media(do_dummy_media.id)
    return


def test_get_media_by_etag(
    do_dummy_user: user_schemas.UserDO, do_dummy_media: media_schemas.MediaDO
) -> None:
    do_media = MEDIA_CRUD.get_media_by_etag(
        do_dummy_user.id, do_dummy_media.e_tag
    )
    assert do_media == do_dummy_media
    return


def test_get_all_medias_by_owner(do_dummy_user: user_schemas.UserDO) -> None:
    do_media_create1 = media_schemas.MediaCreateDO(
        owner_id=do_dummy_user.id,
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
    )
    do_dummy_media1 = MEDIA_CRUD.create_media(do_media_create1)

    do_media_create2 = media_schemas.MediaCreateDO(
        owner_id=do_dummy_user.id,
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.xls",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.XLS,
        ),
    )
    do_dummy_media2 = MEDIA_CRUD.create_media(do_media_create2)

    user_all_medias = MEDIA_CRUD.get_all_medias_by_owner(do_dummy_user.id)
    assert len(user_all_medias) == 2

    MEDIA_CRUD.delete_media(do_dummy_media1.id)
    MEDIA_CRUD.delete_media(do_dummy_media2.id)
    return


def test_delete_media_by_owner(do_dummy_user: user_schemas.UserDO) -> None:
    do_media_create1 = media_schemas.MediaCreateDO(
        owner_id=do_dummy_user.id,
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
    )
    do_dummy_media1 = MEDIA_CRUD.create_media(do_media_create1)

    do_media_create2 = media_schemas.MediaCreateDO(
        owner_id=do_dummy_user.id,
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.xls",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.XLS,
        ),
    )
    do_dummy_media2 = MEDIA_CRUD.create_media(do_media_create2)

    MEDIA_CRUD.delete_media_by_owner(do_dummy_user.id)

    user_all_medias = MEDIA_CRUD.get_all_medias_by_owner(do_dummy_user.id)
    assert len(user_all_medias) == 2
    for m in user_all_medias:
        assert m.is_active is False

    MEDIA_CRUD.delete_media(do_dummy_media1.id)
    MEDIA_CRUD.delete_media(do_dummy_media2.id)
    return
