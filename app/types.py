from typing import Annotated

from pydantic import Field

Token = Annotated[str, Field(max_length=1024)]

Id = Annotated[int, Field(ge=0, le=1e15)]
