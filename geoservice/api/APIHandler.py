from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from geoservice.api.parcels_api import router as parcel_router
from geoservice.api.units_api import router as unit_router

from geoservice.exception.service_exception import ServiceException
from geoservice.exception.common import ErrorCodes
from geoservice.api.common import ResponseCodes
from geoservice.model.dto.BaseDTO import Header, BaseResponse
from geoservice.api.middleware.MockMiddleware import MockMiddleware
from geoservice.api.middleware.DBLogMiddleware import DBLogMiddleware
from geoservice.api.middleware.AuthenticationMiddleware import AuthenticationMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from i18n.locale import get_locale
from log.logger import logger
import os
import traceback


async def set_request_body_in_scope(request: Request):
    log = logger()
    method = request.method.upper()    

    lang = os.environ['default_locale']
    request_lang = None
    
    if method == "GET":
        request_lang = request.query_params.get("lang", None)
    else:
        request_body = await request.json()
        request.scope["request_body"] = request_body
        try:
            request_lang = request_body["header"]["lang"]
        except KeyError as e:
            log.debug("cannot get request_body.header.lang: {e}")

    if request_lang:
        lang = request_lang
    request.scope["lang"] = lang


class APIHandler:

    def __init__(self, app) -> None:
        self.app = app
        self.app_mode = os.environ['app_mode']
        self.log = logger()

        self.handle_routes()
        self.handle_exceptions()
        self.handle_middleware()

    def handle_routes(self):
        self.app.include_router(
            parcel_router,
            prefix="/parcels",
            tags=["parcels"],
            dependencies=[Depends(set_request_body_in_scope)]
        )

        self.app.include_router(
            unit_router,
            prefix="/unit",
            tags=["unit"],
            dependencies=[Depends(set_request_body_in_scope)]
        )

    def handle_exceptions(self):

        @self.app.exception_handler(ServiceException)
        def service_exception_handler(request: Request, ex: ServiceException):

            # TODO: messsage_key must be translated
            error_message = ""
            if ex.error_message:
                error_message = ex.error_message
            else:
                error_message = ex.error_code.messsage_key
            error_message = get_locale(
                message=error_message,
                locale=request.query_params.get("lang", None))
            header = Header(result_code=ex.error_code.code,
                            result_message=error_message)
            response = BaseResponse(header=header)

            return JSONResponse(
                # TODO: maybe we should return proper http response
                status_code=ResponseCodes.SUCCESS.code,
                content=jsonable_encoder(response),
            )

        @self.app.exception_handler(Exception)
        def exception_handler(request: Request, ex: Exception):

            error_message = ErrorCodes.SERVER_ERROR.messsage_key
            error_message = get_locale(
                message=error_message,
                locale=request.query_params.get("lang", None))

            exception_txt = repr(ex) + " ---> " + ''.join(
                traceback.TracebackException.from_exception(ex).format())
            self.log.error(
                f"error_message: {error_message},  exception_txt: {exception_txt}")

            header = Header(result_code=ErrorCodes.SERVER_ERROR.code,
                            result_message=error_message)
            response = BaseResponse(header=header)

            return JSONResponse(
                status_code=ErrorCodes.SERVER_ERROR.code,
                content=jsonable_encoder(response),
            )

    def handle_middleware(self):

        enable_api_mock = os.environ['enable_api_mock']
        # TODO: mock middleware is better be handled at dispatcher
        if self.app_mode == "app" and enable_api_mock == "true":
            mock_middleware = MockMiddleware()
            self.app.add_middleware(
                BaseHTTPMiddleware, dispatch=mock_middleware)

        # TODO: auth middleware is better be handled at dispatcher
        if self.app_mode == "app":
            auth_middleware = AuthenticationMiddleware()
            self.app.add_middleware(
                BaseHTTPMiddleware, dispatch=auth_middleware)

        """
            db log middleware must be the last one on the stack so that whatever
            happens in other middlewares, the log is available
        """
        enable_db_log = os.environ['enable_db_log']
        if self.app_mode == "app" and enable_db_log == "true":
            db_log_middleware = DBLogMiddleware()
            self.app.add_middleware(
                BaseHTTPMiddleware, dispatch=db_log_middleware)
