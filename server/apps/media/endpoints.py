import hashlib
import io
import traceback
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, Request, UploadFile

from server.apps.media.crud import MEDIA_CRUD
from server.apps.media.schemas import (
    MEDIA_CONTENT_TYPE,
    MediaCreateDO,
    MediaDTO,
    MediaExtInfo,
)
from server.apps.user.schemas import UserDO
from server.apps.user.utils import get_user_premium_type
from server.core import dependency
from server.core.exception import EXCEPTION_LIB
from server.libs.fs import FILE_STORE_FACTORY
from server.settings import USER_BASE_LIMIT_CONFIG
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_media_logger as logger

router = APIRouter()


@router.post(
    "/medias/upload",
    summary="Upload a data file. Only accept CSV/EXCEL files",
    response_model=MediaDTO,
    response_description="uploaded media object",
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> MediaDTO:
    """
    Upload media and currently supports csv, xls and xlsx.

    - file: file to upload
    - current_user: a logged-in user
    """

    # TODO: There are sveral issues still to consider
    # 1. How to calculate the total rows number, maybe do it async.
    # 2. What if the file has more than one worksheet.

    # TODO: How and when does `content-length` header added to fastapi request header?
    if "content-length" not in request.headers:
        logger.error(
            f"[upload_file] MEDIA__FILE_CONTENT_LENGTH_ERROR: Upload media request with invalid header, current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.MEDIA__FILE_CONTENT_LENGTH_ERROR.value(
            "Upload media request with invalid header"
        )

    content_length = int(request.headers["content-length"])

    # get user upload limitation according to user type
    user_premium_type = get_user_premium_type(current_user)
    limit_size_mb: int = USER_BASE_LIMIT_CONFIG[
        user_premium_type
    ].ui_permission.max_upload_dataset_size
    limit_size: int = limit_size_mb * 1024 * 1024

    if content_length > limit_size:
        logger.error(
            f"[upload_file] MEDIA__FILE_CONTENT_LENGTH_ERROR: The uploaded file exceeds the maximum limit, current_user [{current_user.id}] limitation [{limit_size_mb} MB]"
        )
        raise EXCEPTION_LIB.MEDIA__FILE_CONTENT_LENGTH_ERROR.value(
            f"The uploaded file exceeds the maximum limit [{limit_size_mb} MB]"
        )

    file_name = file.filename
    media_type = file.content_type

    if media_type not in MEDIA_CONTENT_TYPE.list():
        logger.error(
            f"[upload_file] MEDIA__MIME_TYPE_ERROR: error mime type [{media_type}], current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.MEDIA__MIME_TYPE_ERROR.value(
            f"File mime type {media_type} error, please use csv, xls or xlsx."
        )

    contents = await file.read(limit_size + 1)
    if len(contents) > limit_size:
        logger.error(
            f"[upload_file] MEDIA__FILE_CONTENT_LENGTH_ERROR: The uploaded file exceeds the maximum limit, current_user [{current_user.id}] limitation [{limit_size_mb} MB]"
        )
        raise EXCEPTION_LIB.MEDIA__FILE_CONTENT_LENGTH_ERROR.value(
            f"The uploaded file exceeds the maximum limit [{limit_size_mb} MB]"
        )

    # calculate md5 checksum
    hash_md5 = hashlib.md5(contents)  # type: ignore
    md5_checksum = hash_md5.hexdigest()

    # hotfix: skip md checksum
    # # check md5 checksum in db
    # do_media = MEDIA_CRUD.get_media_by_etag(current_user.id, md5_checksum)
    # if do_media is not None:
    #     dto_media = MEDIA_CRUD.media_do_to_dto(do_media)
    #     return dto_media

    # fetch fisrt 5 rows for data preview
    try:
        if media_type == MEDIA_CONTENT_TYPE.CSV:
            df = pd.read_csv(io.BytesIO(contents), encoding="utf8", nrows=5)  # type: ignore
        else:
            df = pd.read_excel(io.BytesIO(contents), nrows=5)  # type: ignore
    except Exception as e:
        traceback.print_exc()
        err_msg = str(e)
        logger.error(
            f"[upload_file] MEDIA__PARSE_FILE_ERROR: error [{err_msg}], current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.MEDIA__PARSE_FILE_ERROR.value(
            f"Dataset file parse error. Pandas exception message:\n{err_msg}"
        )

    header_list = list(df.columns)
    contents_str = df.to_json(orient="records")
    bucket_name = GLOBAL_CONFIG.bucket_name

    uuid_str = str(uuid.uuid4())
    key_name = f"user={current_user.id}/medias/{uuid_str}"
    presigned_url = FILE_STORE_FACTORY.get_upload_object_presigned_url(
        bucket_name=bucket_name,
        key_name=key_name,
        expiry_in_sec=GLOBAL_CONFIG.filestore_put_object_url_ttl,
    )

    logger.info(f"Test: presigned_url [{presigned_url}]")
    FILE_STORE_FACTORY.upload_to_file_store(url=presigned_url, data=contents)

    # validate local md5 checksum and etag of s3
    etag = FILE_STORE_FACTORY.get_etag_from_file_store(
        bucket_name=bucket_name, key_name=key_name
    )
    if etag != md5_checksum:
        logger.error(
            f"[upload_file] MEDIA__FILE_ETAG_CHECK_ERROR: error etag {etag} md5 checksum {md5_checksum}, current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.MEDIA__FILE_ETAG_CHECK_ERROR.value(
            f"upload file etag error: presigned url {presigned_url}"
        )

    loc_prefix = FILE_STORE_FACTORY.generate_fs_prefix()
    location = f"{loc_prefix}/{bucket_name}/{key_name}"

    ext_info = MediaExtInfo(
        header=header_list,
        first_n_rows=contents_str,
        file_name=file_name,
        media_type=media_type,
    )
    do_media = MEDIA_CRUD.create_media(
        MediaCreateDO(
            owner_id=current_user.id,
            location=location,
            ext_info=ext_info,
            e_tag=etag,
        )
    )
    dto_media = MEDIA_CRUD.media_do_to_dto(do_media)

    return dto_media
