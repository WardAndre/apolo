from pydantic import BaseModel, ConfigDict


class LiquidsoapTrackEvent(BaseModel):
    apolo_track_id: str | None = None
    filename: str | None = None
    initial_uri: str | None = None
    title: str | None = None
    rid: str | None = None

    model_config = ConfigDict(extra="allow")
