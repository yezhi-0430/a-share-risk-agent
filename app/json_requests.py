"""Parse market prices directly as decimals before request validation."""

import json
from decimal import Decimal
from typing import NoReturn

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute


def reject_nonfinite_number(value: str) -> NoReturn:
    raise json.JSONDecodeError("Non-finite JSON number", value, 0)


class DecimalJSONRequest(Request):
    async def json(self):
        if not hasattr(self, "_json"):
            self._json = json.loads(
                await self.body(),
                parse_float=Decimal,
                parse_constant=reject_nonfinite_number,
            )
        return self._json


class DecimalJSONRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def handler(request: Request) -> Response:
            try:
                return await original_handler(DecimalJSONRequest(request.scope, request.receive))
            except RequestValidationError as exc:
                # Invalid decimals can exceed JSON's integer/float range. Keep their
                # original decimal representation in validation errors as well.
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": jsonable_encoder(exc.errors(), custom_encoder={Decimal: str})
                    },
                )

        return handler
